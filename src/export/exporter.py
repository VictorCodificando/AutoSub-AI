from pathlib import Path

from ..models import Job
from ..utils.utils import create_path, format_time


def export_to_srt(job: Job, output_dir: Path) -> Path:
    transcriptions = job.transcription
    subtitles = ""

    for transcript in transcriptions:
        start: str = format_time(transcript.start)
        end: str = format_time(transcript.end)
        subtitles += (
            f"{transcript.id}\n{start} --> {end}\n{transcript.translated_text}\n\n"
        )

    create_path(str(output_dir))
    srt_path = output_dir / f"{job.video_path.stem}.srt"

    srt_path.write_text(subtitles, encoding="utf-8")

    return srt_path