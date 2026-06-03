import shutil
from pathlib import Path
from .config import settings
from .models import Job
from .ingestion.extract import extract_audio


def delete_temp_path(delete: bool = True):
    if not delete:
        return
    try:
        shutil.rmtree(settings.temp_path)
    except OSError as e:
        print(f"Error: {settings.temp_path} : {e}")


def create_path(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)


def process_videos(videos: list[str]):
    jobs: list[Job] = [
        Job(id=index, video_path=Path(video)) for index, video in enumerate(videos)
    ]
    for job in jobs:
        # Ingestion
        audio_path = Path(
            f"{settings.temp_path}/{job.video_path.name}/{job.id}_{job.video_path.name}_audio.wav"
        )
        create_path(str(audio_path.parent))
        extract_audio(job.video_path, audio_path)
        # Segmentación
        # Aislamiento
        # Transcripcion
        # Diarizacion
        # Traducción


if __name__ == "__main__":
    videos = ["./test_data/01_test.mp4"]
    create_path(settings.temp_path)
    process_videos(videos)
    pass
