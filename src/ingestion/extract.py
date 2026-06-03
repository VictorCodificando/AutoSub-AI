import subprocess
import json
from pathlib import Path


def has_audio(video_path: Path):
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "a",
        "-show_entries",
        "stream=codec_type",
        "-of",
        "json",
        str(video_path),
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)

        info = json.loads(result.stdout)

        if "streams" in info and len(info["streams"]) > 0:
            return True
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error analizando el video {video_path.name}: {e.stderr}")


def extract_audio(video_path: Path, audio_path: Path):
    if not has_audio(video_path):
        raise Exception(f"El video {video_path.name} no tiene pista de audio")

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",
        "-c:a",
        "pcm_s16le",
        "-ac",
        "1",
        "-ar",
        "16000",
        "-y",
        str(audio_path),  # Para que sea un .wav ha de terminar en .wav no tiene mas
    ]
    try:
        _ = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"Video {video_path.name} ha sido extraido su audio en {str(audio_path)}")
    except FileNotFoundError as e:
        print(
            "Error grave: 'ffmpeg' no está instalado en el sistema o no se encuentra en el PATH"
        )
        raise e
    except subprocess.CalledProcessError as e:
        print(f"Error convirtiendo el video: {e.stderr}")
        raise e
