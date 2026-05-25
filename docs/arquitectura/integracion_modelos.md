# Integración de Modelos (MVP)

Este documento detalla las especificaciones de integración de los modelos de IA seleccionados para el MVP de **AutoSub-AI**, sus roles en el pipeline y las pautas técnicas para su configuración.

---

## 1. Segmentación y Aislamiento Vocal

### Silero VAD v4
* **Rol:** Detección de Actividad de Voz (Voice Activity Detection).
* **Propósito:** Analizar la señal de audio para discriminar entre el habla humana y el silencio, evitando que la fase de transcripción procese audio innecesario y previniendo alucinaciones en Whisper.
* **Integración en el Pipeline:**
  * **Modo VRAM Alta (Recomendado):** Silero VAD se ejecuta integrado internamente dentro del flujo de pre-procesamiento de BS Roformer.
  * **Modos VRAM Media/Baja:** Se mantiene desacoplado en una etapa independiente al principio del pipeline, lo que permite omitir BS Roformer o usar modelos de aislamiento más ligeros sin alterar el flujo general.

### BS Roformer
* **Rol:** Aislamiento de voz y separación de fuentes de audio.
* **Propósito:** Separar la voz del instrumental, la música de fondo y los efectos de sonido.
* **Configuración técnica:** Recibe como entrada el audio extraído del video y entrega pistas limpias conteniendo únicamente la señal de voz. Esto asegura una tasa de error de palabras (WER) significativamente menor durante la transcripción.

---

## 2. Transcripción

### Whisper (large-v3)
* **Rol:** Transcripción de audio a texto con marcas de tiempo.
* **Propósito:** Generar la transcripción base precisa de cada bloque de voz.
* **Configuración del MVP:**
  * Modelo base: `large-v3`.
  * Optimización: Carga en formato de precisión media (`float16`) o mediante implementaciones optimizadas como `faster-whisper` (utilizando cuantizaciones `int8` o `float16` en GPU si se requiere limitar el consumo de VRAM).
  * **Roadmap de VRAM:** En futuras versiones se habilitarán selectores para modelos más ligeros (`medium`, `small`, `base`) como alternativas de bajo consumo de recursos.

---

## 3. Diarización

### Pyannote.audio 3.1
* **Rol:** Segmentación y etiquetado de locutores (Speaker Diarization).
* **Propósito:** Identificar quién habla en cada momento dentro de la pista de audio limpia.
* **Detalles de Integración:**
  * Requiere un token de Hugging Face (`HF_TOKEN`) tras aceptar los términos de uso de los modelos en Hugging Face Hub (específicamente `pyannote/speaker-diarization-3.1` y `pyannote/segmentation-3.0`).
  * Genera un listado de intervalos de tiempo asociados a identificadores únicos de locutor (ej. `SPEAKER_00`, `SPEAKER_01`). Esta información se acopla en el proceso de reagrupación semántica para adaptar la traducción.

---

## 4. Traducción

### API de Cerebras (LLMs de Inferencia Ultrarrápida)
* **Rol:** Traducción semántica y contextual de los subtítulos.
* **Propósito:** Traducir los enunciados respetando el tono, modismos y contexto de la conversación a gran velocidad.
* **Flujo de Trabajo:**
  * **Ventana Deslizable (Sliding Window):** Se agrupan los subtítulos en lotes y se adjunta un fragmento de las traducciones previas para dar contexto continuo al LLM.
  * **Glosario Dinámico:** Se inyecta un glosario JSON con términos fijos o nombres propios detectados en la fase preliminar.
  * **Output Estructurado (Structured Outputs):** Se envía un esquema JSON estricto en la solicitud para obligar al modelo de Cerebras a devolver las traducciones indexadas por ID de subtítulo, asegurando que las marcas de tiempo no se alteren o pierdan durante el procesamiento.
