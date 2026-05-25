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
