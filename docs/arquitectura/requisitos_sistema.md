# Requisitos del Sistema y Arquitectura

Este documento resume la arquitectura del pipeline de procesamiento por fases y los requisitos técnicos de **AutoSub-AI** para su despliegue.

---

## Resumen Ejecutivo
Pipeline automatizado para la transcripción, traducción y embebido de subtítulos en videos. El sistema procesa archivos de video extrayendo el audio, aislando voces por fases para optimizar la VRAM, transcribiendo con Whisper, e inteligentemente traduciendo usando LLMs mediante técnicas de ventana deslizante y generación de glosarios.

---

## Arquitectura del Pipeline (Procesamiento por Fases)

Para maximizar el rendimiento y evitar tiempos de carga/descarga de modelos en la VRAM, el sistema opera por **Fases Horizontales** (todo el contenido pasa por una fase antes de cargar en memoria el modelo de la siguiente fase):

### Fase 1: Ingesta y Segmentación
1. **Extracción (FFmpeg):** Extracción del canal de audio original y conversión (downmix a mono, 16kHz).
2. **Segmentación por VAD (Voice Activity Detection):**
   - **Silero VAD v4** como motor de segmentación.
   - *Nota de Arquitectura:* En la configuración recomendada de alta VRAM del MVP, el aislamiento vocal se realiza con el modelo BS Roformer, el cual ya contiene una ejecución interna de Silero VAD. Sin embargo, para perfiles futuros de VRAM media/baja que prescindan de BS Roformer, se implementará y mantendrá el procesamiento por Silero VAD v4 como un paso independiente en el pipeline.
   - Generación de un mapa estructurado de marcas de tiempo (timestamps) y chunks.

### Fase 2: Aislamiento Vocal
3. **Aislamiento de voz con BS Roformer:**
   - Carga del modelo **BS Roformer** para suprimir ruido de fondo, música e instrumentos de forma avanzada.
   - Procesamiento de los segmentos de audio generados en la fase previa para entregar pistas de voz totalmente aisladas a la fase de transcripción.

### Fase 3: Transcripción y Diarización
4. **Transcripción (Whisper):**
   - Uso del modelo **Whisper large-v3** por defecto en el MVP.
   - Transcripción completa de los fragmentos de audio limpios y aislados.
   - Prevención de alucinaciones en zonas sin voz gracias a la limpieza previa de audio.
5. **Diarización:**
   - Uso de **Pyannote.audio 3.1** para la separación de hablantes.
   - Clasificación de marcas de tiempo por locutor (Locutor 1, Locutor 2, etc.), proporcionando información vital para resolver ambigüedades de plural o género.
6. **Reagrupación Semántica:**
   - Agrupación del texto transcrito en enunciados gramaticalmente coherentes y lógicos (basado en la puntuación y el flujo natural del diálogo), ignorando los cortes físicos del segmentador VAD.

### Fase 4: Contexto y Traducción (LLM)
7. **Generación de Glosario Automático (Fase Cero):**
   - Análisis preliminar del texto completo para identificar nombres propios y entidades clave, generando un archivo `preset.json` que sirve como glosario y reglas de contexto.
8. **Traducción Estructurada (Sliding Window Context):**
   - **Contexto Deslizable:** Envío de bloques de subtítulos (entre 30 y 50 líneas) incluyendo las últimas líneas del bloque anterior como contexto histórico inmediato.
   - **Motor de Inferencia:** Inferencia ultrarrápida a través de la API de **Cerebras** (usando modelos tipo Llama-3).
   - **Output Estructurado:** Uso de JSON estructurado para emparejar directamente los textos traducidos con los IDs de marcas de tiempo.

### Fase 5: Revisión y Ensamblado
9. **Human-in-the-Loop (Revisión UI):**
    - Interfaz en Gradio que presenta un componente editable para que el usuario pueda revisar y corregir traducciones o errores antes del render final. Este paso es opcional.
10. **Muxing y Exportación:**
     - Reensamblaje usando los timestamps originales.
     - Exportación cruda (`.srt` / `.vtt`).
     - Exportación embebida (Soft Subs en contenedor `.mkv`/`.mp4` vía FFmpeg).

---

## Features Aplazadas (Roadmap a futuro)
- **Hard Subs:** Incrustado de subtítulos directos en los píxeles del video.
- **Límites de Lectura (CPS/CPL):** Control estricto de la longitud de la traducción para garantizar tiempos de lectura cómodos directamente desde el LLM.
- **Limpieza de Alucinaciones:** Post-procesado o filtros para eliminar alucinaciones comunes de Whisper en zonas de silencio residual.
- **Batch Processing:** Soporte para encolar múltiples videos simultáneamente desde la interfaz.

---
*Diseño Modular: La arquitectura basada en fases permite cambiar el modelo o proveedor de una etapa específica sin alterar el ecosistema global.*
