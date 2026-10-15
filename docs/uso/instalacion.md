# Instalación

## Requisitos

- GPU NVIDIA con CUDA. Se ha probado con 12 GB de VRAM; `large-v3` en `float16` y BS Roformer necesitan varios GB cada uno, aunque nunca están cargados a la vez.
- FFmpeg instalado en el sistema (`ffmpeg` y `ffprobe` en el `PATH`).
- Python con conda.
- Una API key de Gemini para la traducción.

## Pasos

```bash
git clone https://github.com/VictorCodificando/AutoSub-AI.git
cd AutoSub-AI
conda create -n autosub python=3.11
conda activate autosub
pip install -r requirements.txt
```

Crear un `.env` en la raíz:

```ini
TEMP_PATH=test_data/output
LLM_PROVIDER=google
LLM_MODEL=gemini-2.5-flash
API_KEYS='["clave_1", "clave_2"]'
```

- `TEMP_PATH`: carpeta para los archivos intermedios (audio extraído y voz aislada).
- `LLM_PROVIDER`: proveedor de traducción. Ahora solo existe `google`.
- `LLM_MODEL`: modelo del proveedor (el de arriba es un ejemplo).
- `API_KEYS`: lista JSON con una o más claves del proveedor. Se usan por turnos: cada petición va con la siguiente clave y, si falla, se reintenta con la otra.
- `MAX_CONSECUTIVE_ERRORS` (opcional, 5 por defecto): fallos seguidos tras los que se da la traducción del vídeo por fallida y se sigue con el siguiente.
- `RETRY_DELAY` (opcional, 5 por defecto): segundos de espera entre un fallo y el siguiente intento.

La primera ejecución descarga BS Roformer en `models/` y Whisper `large-v3` en la caché de Hugging Face.

## Uso

Se documentará cuando exista el CLI (ver [hoja de ruta](../hoja_de_ruta.md)).
