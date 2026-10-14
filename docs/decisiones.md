# Decisiones técnicas

Cada entrada explica una decisión: el problema, lo que se eligió, por qué y qué otras opciones había. Algunas elecciones se hicieron sin comparar alternativas; se indica así y quedan como estudio pendiente en la [hoja de ruta](hoja_de_ruta.md).

## Fases horizontales

**Problema.** El pipeline usa al menos dos modelos pesados en GPU (BS Roformer y Whisper `large-v3`). Si cada vídeo hiciera el recorrido completo, habría que cargar y descargar ambos modelos una vez por vídeo.

**Decisión.** Todos los vídeos pasan por una fase antes de empezar la siguiente. Solo hay un modelo cargado en VRAM en cada momento.

**Por qué.** Cargar `large-v3` o Roformer tarda segundos y ocupa varios GB. Con N vídeos, el orden vertical hace 2N cargas y el horizontal 2. Además, tener un único modelo en memoria evita errores de falta de VRAM en una GPU de 12 GB.

**Coste.** No hay resultados parciales: el primer `.srt` aparece cuando todos los vídeos han terminado la última fase. Los archivos intermedios de todos los vídeos tienen que caber en disco a la vez.

## Liberar memoria con un gestor de contexto

**Decisión.** Las fases con modelo heredan de `Model`, que define `load()` y `free()` y se usa con `with`. Al salir se llama a `gc.collect()` y `torch.cuda.empty_cache()`.

**Por qué.** Con `del modelo` no basta para que PyTorch devuelva la VRAM. Ponerlo en la clase base garantiza que ninguna fase se lo salte, incluso si hay una excepción.

## Extraer el audio a 44,1 kHz estéreo

**Problema.** La primera especificación pedía extraer a mono 16 kHz, que es lo que usa Whisper.

**Decisión.** Se extrae a 44,1 kHz estéreo y se baja a mono 16 kHz justo antes de transcribir.

**Por qué.** BS Roformer trabaja con audio estéreo a 44,1 kHz. Si recibe audio ya reducido, separa peor la voz de la música. Whisper hace su propia conversión al cargar el audio, así que reducir antes no aporta nada.

## VAD dentro de la fase de transcripción

**Problema.** La especificación original tenía Silero VAD como fase independiente, antes del aislamiento.

**Decisión.** El VAD se ejecuta dentro del `Transcriptor`, sobre la voz ya aislada, con el Silero que incluye faster-whisper.

**Por qué.** Whisper es el único que usa las regiones de voz. Sobre la pista de voz limpia el VAD acierta más que sobre la mezcla original. Y no hace falta otra dependencia.

**Estado.** En `main.py` queda un bucle vacío donde iría una segmentación separada. Volvería a tener sentido con un perfil de poca VRAM sin Roformer, que está fuera de la 1.0. Decisión abierta.

## Transcribir por región de voz

**Problema.** Transcribiendo el audio completo, los subtítulos se desfasaban en vídeos largos, aparecían antes de que se hablara y se perdían frases cortas.

**Decisión.** Cada región del VAD se transcribe por separado. Los tiempos salen de las marcas por palabra y se recortan a los límites de la región. Las regiones de menos de 2 s se transcriben con 1 s de margen a cada lado.

**Por qué.** Anclar cada fragmento a su región impide que el error se acumule. Las marcas por palabra son más precisas que las del segmento. El margen da a Whisper contexto suficiente para reconocer un "sí" o un "vamos" suelto.

**Coste.** Más llamadas a Whisper, y una frase partida entre dos regiones se transcribe en dos trozos.

## Compromiso entre frases inventadas y frases perdidas

**Problema.** Si el VAD es muy sensible, entra ruido y Whisper se inventa frases. Si es estricto, se pierden frases dichas rápido o en voz baja.

**Decisión actual.** Umbral del VAD en 0,65, descartar segmentos con `no_speech_prob > 0,8` y `condition_on_previous_text=False`.

**Estado.** No está resuelto. Siguen apareciendo algunas frases inventadas. El ajuste se hará midiendo con el informe de calidad en lugar de a ojo.

## BS Roformer para aislar la voz

**Decisión.** BS Roformer (`ep_368`, SDR 12,96) con la librería `audio-separator`.

**Por qué.** Se eligió por recomendaciones y por ser un modelo más complejo que las alternativas habituales, con la idea de que separaría mejor. No se ha comparado con Demucs, MDX-Net ni otros modelos de UVR.

**Estado.** Pendiente de comparar.

## faster-whisper con `large-v3`

**Decisión.** faster-whisper (CTranslate2) con `large-v3` en `float16` y `beam_size=10`.

**Por qué.** `large-v3` es el modelo más preciso de Whisper y cabe en 12 GB en `float16`. faster-whisper incluye el VAD de Silero y marcas de tiempo por palabra.

**Estado.** No se ha comparado con `large-v3-turbo`, WhisperX ni la implementación original de OpenAI. Pendiente de comparar.

## El LLM devuelve JSON por id, no un SRT

**Problema.** Si se pide al LLM que traduzca un SRT, puede fusionar líneas, saltarse alguna o cambiar los tiempos.

**Decisión.** Se envía una lista `[{id, text}]` y se exige una respuesta con el esquema `TranslatedBatch` (salida estructurada). Los tiempos no se envían. Si falta un `id`, el subtítulo conserva el texto original y se marca como `translation_failed`.

**Por qué.** Los tiempos no pueden cambiar porque el LLM nunca los ve. Un fallo parcial no rompe el archivo: deja una línea sin traducir y queda contado en el informe.

## Proveedor de LLM configurable, Gemini primero

**Problema.** La especificación inicial elegía Cerebras por su velocidad.

**Decisión.** El traductor se crea con una fábrica según `LLM_PROVIDER`. El primer proveedor implementado es Gemini.

**Por qué Gemini.** Tiene capa gratuita y una ventana de contexto grande: cabe un episodio entero en una petición, así que de momento no hace falta partir en lotes.

**Por qué configurable.** Cada proveedor tiene ventajas distintas (coste, velocidad, ejecución local). Añadir uno nuevo es una clase más en `TranslatorFactory`. Para la 1.0 se quieren añadir más.

## Medir la calidad sin subtítulos de referencia

**Problema.** Muchos ajustes (umbral del VAD, margen de las regiones, modelo) se probaban a ojo y no había forma de saber si un cambio mejoraba o empeoraba el resultado.

**Decisión.** Un informe que comprueba reglas de subtitulado profesional sobre el resultado: duración, caracteres por segundo, longitud de línea, solapes, duplicados y traducciones fallidas. No necesita un subtítulo de referencia.

**Por qué.** Conseguir subtítulos de referencia buenos para cada vídeo de prueba requiere mucho trabajo manual. Las reglas de legibilidad detectan los fallos más visibles (subtítulos de 0,2 s, líneas de 80 caracteres, solapes) y se pueden calcular sobre cualquier archivo.

**Límite.** No mide si la transcripción o la traducción son correctas. Ver [Calidad](calidad.md).

## Diarización, glosario y ventana de contexto aplazados

**Problema.** La especificación incluía diarización con Pyannote (para resolver género y número al traducir), un glosario automático de nombres propios y una ventana deslizante de contexto entre lotes.

**Decisión.** Ninguna se implementa todavía. Las tres se tratan como estudios: primero se mide si mejoran el resultado y si compensan el coste.

**Por qué.** La diarización añade otro modelo pesado y un token de Hugging Face, y no está claro cuánto mejora la traducción. Con un episodio entero en una sola petición, la ventana de contexto pierde sentido mientras no haya lotes. El glosario tiene el mismo problema: el LLM ya ve todo el texto.
