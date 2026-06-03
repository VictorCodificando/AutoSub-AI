# Roadmap y Plan de Versiones

Este documento define el alcance y las tecnologías confirmadas para el MVP (Mínimo Producto Viable) de **AutoSub-AI**.

---

## Alcance del MVP (Mínimo Producto Viable)

El objetivo actual del proyecto es establecer un flujo de procesamiento estable y de alta calidad (máxima precisión de segmentación, aislamiento de audio y traducción contextual fluida).

### Pila Tecnológica del MVP:
* **Ingesta:** Extracción de audio mediante FFmpeg (remuestreo a 16kHz, mono).
* **Segmentación:** Silero VAD v4 (integrado internamente en BS Roformer en el flujo recomendado, pero mantenido como módulo independiente para flexibilizar la arquitectura).
* **Aislamiento Vocal:** Modelo **BS Roformer** para supresión de ruido e instrumentales de fondo.
* **Transcripción:** Modelo **Whisper large-v3** para procesar los segmentos de voz limpios.
* **Diarización:** **Pyannote.audio 3.1** para la identificación y etiquetado de los distintos locutores.
* **Traducción:** Ventana deslizable contextual ("Sliding Window Context") procesada mediante la API de **Cerebras** (LLM con salida estructurada en JSON).
* **Interfaz de Usuario:** Interfaz básica en Gradio que incluye una pantalla de revisión opcional para corrección de subtítulos (Human-in-the-loop) y posterior exportación.


## Configuración previa

- API key del LLM (Cerebras en el MVP).
- Idioma de entrada (opcional; si no se indica, se autodetecta).
- Idioma de salida (opcional; si no se elige, no se traduce, solo se transcribe).

## Decisiones de diseño del MVP

### Segmentación / VAD

En el MVP no hay un paso de Silero VAD aparte. Se usa el VAD nativo de faster-whisper (`vad_filter`).

El único que necesita las regiones de voz es Whisper, y Whisper ya lleva Silero dentro. Un paso separado sería código que no aporta nada hoy.

Se recuperará el paso de VAD desacoplado cuando exista un perfil de aislamiento de VRAM baja que sustituya a BS Roformer (modelo aún por decidir) y que no traiga VAD integrado. En ese caso las regiones de voz ya no vendrían dadas y habría que calcularlas. Hasta entonces, no se implementa.

### Contratos entre fases y memoria

"Fases horizontales" no es procesar en paralelo. Hay una sola GPU. Lo que se hace es cargar un modelo y pasar todos los archivos por él de forma secuencial; solo después se cambia de modelo. Lo que se ahorra es recargar el modelo una y otra vez, no tiempo por paralelizar.

Cada fase recibe una lista y devuelve una lista, no un archivo de cada vez. \
La relación entre el vídeo original y sus salidas intermedias se mantiene con un objeto que va acumulando campos fase a fase (`video_original`, `audio`, `audio_limpio`, `transcripcion`...), en vez de listas de rutas sueltas.

En VRAM hay un solo modelo a la vez. Al terminar cada fase se libera (`del modelo; torch.cuda.empty_cache()`) antes de cargar el siguiente.

Entradas y salidas por fase:

- Ingesta: ruta del vídeo → ruta del audio (mono, 16 kHz).
- Aislamiento: ruta del audio → ruta del audio limpio (BS Roformer).
- Transcripción: ruta del audio limpio → JSON `[{id, inicio, fin, texto}]`.
- Traducción: ese mismo JSON → el mismo JSON con `texto` traducido.
- Ensamblado: JSON traducido → `.srt`/`.vtt` (y muxing opcional).

### Traducción sin deriva de timestamps

No se le pide al LLM que devuelva un SRT. El proceso es:

1. La salida de Whisper se pasa a JSON `[{id, inicio, fin, texto}, ...]`.
2. El LLM devuelve el mismo array con solo el `texto` traducido, conservando `id`, `inicio` y `fin`.
3. El SRT/VTT final se arma con nuestros timestamps, no con lo que escriba el LLM.

Para empezar se le pasa el bloque entero y se valida que el mapeo cuadra. La ventana deslizante contextual se añade en una segunda pasada.

### Diarización (segunda pasada)

Pyannote devuelve un objeto `Annotation` en memoria. RTTM es solo un formato de intercambio. Basta con `{inicio, fin, locutor}` en memoria.

El locutor se asigna a cada subtítulo por solapamiento temporal: gana el turno que más se solapa con el intervalo del subtítulo.

Ayuda al traductor con el género, el número y la coherencia entre personajes. Es lo más prescindible para un primer flujo completo, así que se deja para después. Luego podemos asignarle un color por personaje si lo vemos mejor.

### Cómo se construye: esqueleto andante

Primero un único vídeo recorriendo todas las fases con la calidad mínima, hasta sacar un SRT traducido. Eso prueba los contratos entre fases de verdad, no sobre el papel. La diarización y la ventana deslizante se añaden cuando el flujo completo ya funciona.