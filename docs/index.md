# AutoSub-AI

AutoSub-AI genera subtítulos traducidos a partir de archivos de vídeo. Recibe uno o varios vídeos, extrae el audio, separa la voz de la música y los efectos, transcribe con Whisper, traduce con un LLM y escribe un `.srt` por vídeo. Al final imprime un informe de calidad de cada subtítulo generado.

Funciona en local sobre una GPU NVIDIA. La traducción es la única parte que usa una API externa.

## Para qué sirve

Está pensado para contenido con diálogo y ruido de fondo: anime, series, películas, vídeos de YouTube y charlas. Los idiomas de origen probados son inglés, japonés y español.

El proyecto es también un ejercicio de diseño: montar un pipeline con varios modelos pesados que conviven en una sola GPU de consumo, y justificar cada elección con medidas en vez de intuición.

## Estado actual

Funciona de principio a fin para una lista de vídeos:

1. Extracción de audio con FFmpeg.
2. Aislamiento de voz con BS Roformer.
3. Detección de voz y transcripción con faster-whisper (`large-v3`).
4. Traducción con Gemini, con salida JSON validada.
5. Exportación a `.srt` e informe de calidad.

Todavía no hay CLI ni interfaz: los vídeos se indican en `src/main.py`. La diarización, el glosario y la ventana de contexto están en estudio. El detalle está en la [hoja de ruta](hoja_de_ruta.md).

## Cómo leer esta documentación

- [Cómo funciona](funcionamiento/pipeline.md): el pipeline con esquemas, fase por fase.
- [Decisiones técnicas](decisiones.md): qué se eligió, por qué y qué alternativas había.
- [Recorrido](recorrido.md): cómo ha evolucionado el proyecto y qué problemas aparecieron.
- [Calidad](calidad.md): cómo se mide el resultado.
- [Hoja de ruta](hoja_de_ruta.md): qué falta para la versión 1.0 y qué queda fuera.
- [Instalación](uso/instalacion.md).

Desarrollado y probado en una GPU de 12 GB.
