from pathlib import Path
from ..models import Model, TranscriptionSegment


class Transcriptor(Model):
    def __init__(self, provider: "", language: str | None = None) -> None:
        pass

    def load(self):
        pass

    def translate(transcription: list[TranscriptionSegment]):
        pass

    def free(self):
        pass
