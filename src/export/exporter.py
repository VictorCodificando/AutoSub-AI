from src.models import Job, TranscriptionSegment
from ..utils.utils import format_time


def export_to_srt(job: Job):
    transcriptions = job.transcription
    subtitles = ""

    for transcript in transcriptions:
        start:str = format_time(transcript.start)
        end:str = format_time(transcript.end)
        subtitles += f"{transcript.id}\n{start} --> {end}\n{transcript.translated_text}\n\n"
        
        
    srt_path = job.video_path.with_suffix(".srt")

    srt_path.write_text(subtitles, encoding="utf-8")
    
