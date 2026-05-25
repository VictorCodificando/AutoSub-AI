# AutoSub-AI - Requisitos del Proyecto

Este será un proyecto que te permitirá darle como input uno (o varios) videos y generará subtítulos traducidos a tu idioma.

## Flujo de Procesamiento (Por Fases - Especificación del MVP)
Para evitar la saturación de memoria (VRAM) por cambiar modelos constantemente, el proceso opera en "Fases Horizontales" (todo el audio pasa por una fase completa antes de iniciar la siguiente):

1. **Extracción (FFmpeg):** Extrae la pista de audio del video original (conversión a 16kHz, mono).
2. **Segmentación (Silero VAD v4):** Identifica zonas con presencia de voz y delimita silencios. *Nota:* En la configuración recomendada de VRAM alta, el modelo de aislamiento vocal BS Roformer ya tiene integrado Silero VAD de forma interna. Sin embargo, el pipeline mantendrá esta fase de segmentación desacoplada e independiente usando Silero VAD v4 para permitir las futuras alternativas de bajo (low) y medio (medium) consumo de VRAM.
3. **Aislamiento Vocal (BS Roformer):** Procesa el audio para separar la voz limpia de la música de fondo, efectos e instrumental.
4. **Transcripción (Whisper large-v3):** Transcribe las secciones de voz limpia. De forma predeterminada para el MVP se usa el modelo `large-v3`. (Se añadirán alternativas optimizadas para baja VRAM en versiones posteriores).
5. **Diarización (Pyannote.audio 3.1):** Analiza el audio para identificar quién habla en cada momento (Locutor 1, Locutor 2, etc.), enriqueciendo la metadata para guiar la traducción.
6. **Reagrupación Semántica:** Organiza las palabras y fragmentos transcritos en oraciones con lógica gramatical basándose en pausas y signos de puntuación, evitando cortes abruptos.
7. **Generación de Glosario Automático (Opcional):** Extracción automatizada de entidades (nombres propios, términos recurrentes) para un pre-glosario en formato JSON.
8. **Traducción (Cerebras API):** 
   - Se agrupan los subtítulos por bloques con una técnica de ventana deslizante ("Sliding Window Context"), arrastrando contexto previo para mantener la coherencia del diálogo.
   - La traducción se delega a la API de Cerebras (para una inferencia de LLM ultrarrápida).
   - Se inyecta el glosario generado y se fuerza una salida estructurada en JSON que mantenga el mapeo exacto de marcas de tiempo (timestamps).
9. **Revisión Humana (Opcional):** Interfaz para verificar y afinar los subtítulos antes de renderizar.
10. **Ensamblado y Muxing (FFmpeg):** Generación del archivo `.srt`/`.vtt` y multiplexado en el contenedor original como subtítulos opcionales (Soft Subs).

## Características Principales
1. **Multimodelo LLM:** Elegir entre Ollama (local), OpenAI, Gemini, etc. mediante API keys.
2. **Exportación:** Generar solo `.srt` o archivo de video con subtítulos seleccionables (Soft Subs).
3. **Idiomas:** Especificar entrada (o auto) y especificar salida (con opción a "igual que la entrada" para solo transcribir).
4. **Context Presets:** JSON creados a mano o auto-generados para dar contexto y reglas de traducción.
5. **Interfaz UI:** Inicialmente en Gradio, con un paso opcional de revisión (Human-in-the-loop).
6. **Compatibilidad:** Soporte universal para múltiples formatos de video usando FFmpeg.

## Características Aplazadas (Versiones Futuras)
- Soporte para *Hard Subs* (subtítulos quemados en la imagen del video).
- Límite automático de caracteres por segundo/línea (CPS/CPL) en el LLM.
- Filtro avanzado de limpieza de alucinaciones típicas de Whisper.
- Batch processing completo (procesar múltiples videos de golpe en la UI).
