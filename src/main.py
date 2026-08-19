from pathlib import Path
from .config import settings
from .models import Job
from .ingestion.extract import extract_audio
from .utils.utils import create_path
from .isolation.isolate import Isolator
from .export.exporter import export_to_srt
from .transcription.transcriptor import Transcriptor, adjust_timestamps
from .translation.translator import TranslatorFactory
import time


def process_videos(
    videos: list[str],
):

    phase_times = {}
    start_time = time.perf_counter()

    jobs: list[Job] = [
        Job(id=index + 1, video_path=Path(video)) for index, video in enumerate(videos)
    ]
    print("Phase 1: Data Ingestion")
    t_init_phase = time.perf_counter()
    # Ingestion
    for job in jobs:
        job.audio_path = Path(
            f"{settings.temp_path}/{job.video_path.name}/{job.id}_{job.video_path.name}_audio.wav"
        )
        create_path(str(job.audio_path.parent))
        extract_audio(job.video_path, job.audio_path)
    print("Ingestion finished")
    print("----------------")
    phase_times["Phase 1: Data Ingestion"] = time.perf_counter() - t_init_phase

    # Segmentation
    for job in jobs:
        pass
    print("Phase 2: Isolation")
    t_init_phase = time.perf_counter()
    # Isolation
    with Isolator() as isolator:
        for job in jobs:
            job.clean_audio_path = isolator.isolate_voice(job.audio_path)
    print("Isolation finished")
    print("----------------")
    phase_times["Phase 2: Isolation"] = time.perf_counter() - t_init_phase

    print("Phase 3: Transcription")
    t_init_phase = time.perf_counter()
    # Transcripcion
    with Transcriptor() as transcriptor:
        for job in jobs:
            job.transcription = transcriptor.transcribe(job.clean_audio_path)
            print(job.transcription)

    print("Transcription finished")
    print("---------------")
    phase_times["Phase 3: Transcription"] = time.perf_counter() - t_init_phase

    # Diarization
    for job in jobs:
        pass

    t_init_phase = time.perf_counter()
    print("Phase 4: Translation")
    # Translation
    for job in jobs:
        translator = TranslatorFactory.crear()
        idioma = "Spanish"
        translator.translate(
            segments=job.transcription, target_language=idioma, context=""
        )
    print("Translation finished")
    print("---------------")
    phase_times["Phase 4: Translation"] = time.perf_counter() - t_init_phase
    # Export
    print("Phase 5: Export")
    for job in jobs:
        export_to_srt(job)

    print("Export finished")
    print("---------------")

    finish_time = time.perf_counter()
    total_time = finish_time - start_time
    
    print("\n" + "=" * 60)
    print(f"{'TIME REPORT':^60}")
    print("=" * 60)
    print(f"{'Phase':<35} | {'Time (s)':<10} | {'Percent':<10}")
    print("-" * 60)
    for phase_name, duration in phase_times.items():
        percent = (duration / total_time) * 100
        print(f"{phase_name:<35} | {duration:>8.3f} s | {percent:>8.2f} %")


if __name__ == "__main__":
    videos = ["./test_data/02_test.mkv"]
    create_path(settings.temp_path)
    process_videos(videos)
    # delete_path(settings.temp_path)
    pass
