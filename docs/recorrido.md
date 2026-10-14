# Recorrido

Cómo ha llegado el proyecto a su estado actual, qué se planteó al principio y qué cambió al implementarlo.

## El punto de partida

El proyecto empezó con una especificación de diez pasos: extracción a mono 16 kHz, Silero VAD como fase propia, BS Roformer, Whisper `large-v3`, diarización con Pyannote, reagrupación semántica, glosario automático, traducción con Cerebras usando ventana deslizante, revisión en Gradio y muxing con FFmpeg.

La idea central, que se ha mantenido, era procesar por fases horizontales para no cargar y descargar modelos en la GPU.

## Primera versión completa

En lugar de construir cada fase completa, se buscó que un solo vídeo llegara de principio a fin con la calidad mínima. Así los contratos entre fases (qué recibe y qué devuelve cada una) se prueban con datos reales.

En junio salieron la ingesta, el aislamiento y una primera transcripción. En agosto se completó el recorrido con la traducción y la exportación a SRT.

Al implementarlo, varias piezas de la especificación cambiaron:

- La extracción pasó de mono 16 kHz a 44,1 kHz estéreo, porque es lo que necesita Roformer.
- El VAD dejó de ser una fase propia y pasó a la transcripción.
- Cerebras se sustituyó por un traductor configurable, empezando por Gemini por su capa gratuita y su ventana de contexto.
- La diarización, la reagrupación, el glosario y la ventana deslizante se dejaron para después.

El porqué de cada cambio está en [Decisiones técnicas](decisiones.md).

## Problema 1: los tiempos

Con el primer SRT completo apareció el problema más visible. Transcribiendo el audio entero de una vez:

- En vídeos largos los subtítulos se iban desfasando.
- Muchos aparecían antes de que el personaje hablara.
- Frases cortas, como una respuesta de una palabra, no salían.

La solución fue transcribir cada región de voz por separado, tomar los tiempos de la primera y la última palabra, y dar 1 s de margen a las regiones de menos de 2 s.

## Problema 2: frases inventadas

Whisper inventa texto cuando recibe audio sin voz. El aislamiento con Roformer ayuda, pero no basta. Al ajustar el VAD apareció un compromiso: si capta mucho, Whisper se inventa frases; si capta poco, se pierden las que se dicen rápido.

Los valores actuales (umbral 0,65, descartar `no_speech_prob > 0,8`) son un punto intermedio elegido probando. El problema sigue abierto.

## Problema 3: no saber si un cambio mejora

Los dos problemas anteriores se ajustaban escuchando el vídeo y mirando el SRT. Era lento y no permitía comparar dos versiones con objetividad. Por eso, en octubre se añadió un informe de calidad que se genera al final de cada ejecución y que también se puede lanzar sobre cualquier archivo de subtítulos.

Con el informe se puede pasar a la siguiente etapa. Muchas elecciones del proyecto (Roformer, `large-v3`, los parámetros del VAD) se hicieron por recomendación y no por medición. Compararlas es parte de la versión 1.0.
