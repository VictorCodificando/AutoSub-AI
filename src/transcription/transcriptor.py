from pathlib import Path
from ..models import Model, TranscriptionSegment
from faster_whisper import WhisperModel
from ..utils.utils import format_time


class Transcriptor(Model):
    def __init__(
        self, model_size: str = "large-v3", language: str | None = None
    ) -> None:
        self.model_size: str | None = model_size
        self.language: str | None = language

    def load(self):
        self.model: WhisperModel = WhisperModel(
            self.model_size, device="cuda", compute_type="float16"
        )

    def transcribe(self, audio_path: Path | None) -> list[TranscriptionSegment]:
        segments, _ = self.model.transcribe(
            str(audio_path), beam_size=10, language=self.language
        )

        result: list[TranscriptionSegment] = []

        for index, segment in enumerate(segments):
            time_start: str = format_time(segment.start)
            time_end: str = format_time(segment.end)

            item: TranscriptionSegment = TranscriptionSegment(
                id=index + 1,
                time_start=time_start,
                time_end=time_end,
                transcription=segment.text,
            )

            result.append(item)

        return result

    def free(self):
        del self.model
