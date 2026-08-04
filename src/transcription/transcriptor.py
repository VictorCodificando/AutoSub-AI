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
            str(audio_path),
            beam_size=10,
            language=self.language,
            vad_filter=True,
            vad_parameters=dict(
                threshold=0.45,
                min_silence_duration_ms=500,
                speech_pad_ms=300,
                max_speech_duration_s=25,
                min_speech_duration_ms=250,
            ),
        )

        return [
            TranscriptionSegment(
                id=index + 1, start=segment.start, end=segment.end, text=segment.text
            )
            for index, segment in enumerate(segments)
        ]

    def free(self):
        del self.model
