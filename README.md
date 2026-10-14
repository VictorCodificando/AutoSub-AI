# AutoSub-AI

Genera subtítulos traducidos a partir de vídeos. Extrae el audio, aísla la voz con BS Roformer, transcribe con Whisper `large-v3`, traduce con un LLM y exporta a SRT con un informe de calidad.

Funciona en local con una GPU NVIDIA; solo la traducción usa una API externa.

Documentación: https://victorcodificando.github.io/AutoSub-AI/

## Estado

El pipeline funciona de principio a fin. Falta el CLI, la exportación a VTT y soft-subs, la interfaz de revisión y comparar los modelos elegidos con alternativas. Ver la [hoja de ruta](https://victorcodificando.github.io/AutoSub-AI/hoja_de_ruta/).

## Instalación

Requiere FFmpeg en el sistema y CUDA.

```bash
pip install -r requirements.txt
```

Configuración en `.env`: ver la [guía de instalación](https://victorcodificando.github.io/AutoSub-AI/uso/instalacion/).
