import shutil
from pathlib import Path
from .config import settings
from .models import Job
from .ingestion.extract import extract_audio
from .utils.utils import create_path, delete_path
from .isolation.isolate import isolate_voice


def process_videos(videos: list[str]): # TODO No cumple con el bucle horizontal(Hay que cargar modelos e ir haciendo todo, luego pasar al siguiente)
    jobs: list[Job] = [
        Job(id=index + 1, video_path=Path(video)) for index, video in enumerate(videos)
    ]

    # Ingestion
    for job in jobs:
        job.audio_path = Path(
            f"{settings.temp_path}/{job.video_path.name}/{job.id}_{job.video_path.name}_audio.wav"
        )
        create_path(str(job.audio_path.parent))
        extract_audio(job.video_path, job.audio_path)

    # Segmentación
    for job in jobs:
        pass
    # Aislamiento
    for job in jobs:
        job.clean_audio_path = isolate_voice(job.audio_path)
        pass
    # Transcripcion
    
    # Diarizacion
    # Traducción


if __name__ == "__main__":
    videos = ["./test_data/01_test.mp4"]
    create_path(settings.temp_path)
    process_videos(videos)
    # delete_path(settings.temp_path)
    pass
