# AutoSub-AI

Bienvenido a la documentación oficial de **AutoSub-AI**, un pipeline automatizado avanzado para la transcripción, traducción y embebido de subtítulos en videos.

## ¿Qué es AutoSub-AI?

AutoSub-AI es un proyecto diseñado para procesar uno o varios videos y generar subtítulos traducidos a tu idioma preferido. Para lograr esto con la máxima eficiencia y precisión, el sistema utiliza un flujo de procesamiento horizontal por fases, apoyándose en herramientas de IA punteras como Silero VAD v4 (detección de voz), BS Roformer (aislamiento vocal), Whisper large-v3 (transcripción), Pyannote.audio 3.1 (diarización) e inferencia ultra rápida con la API de Cerebras para la traducción mediante LLMs.

## Enlaces Rápidos

- 🏗️ **[Arquitectura y Diseño](arquitectura/pipeline_procesamiento.md):** Sumérgete en el procesamiento horizontal por fases y la gestión de VRAM.
- 🔌 **[Integración de Modelos](arquitectura/integracion_modelos.md):** Detalles sobre la configuración de Silero, Whisper, Pyannote y Cerebras.
- 📋 **[Requisitos del Sistema](arquitectura/requisitos_sistema.md):** Especificaciones técnicas del pipeline y dependencias de hardware.
- 🚀 **[Roadmap y Versiones](desarrollo/roadmap.md):** Evolución desde el MVP hasta perfiles de bajo consumo (Low/Medium VRAM).

---
