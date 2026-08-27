from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
import gc
import torch


class TranscriptionSegment(BaseModel):
    id: int = Field(..., description="Unique numeric ID, starting in 1", ge=1)
    start: float = Field(..., description="Start time in seconds", ge=0)
    end: float = Field(..., description="End time in seconds", ge=0)
    text: str = Field(..., description="Clean transcripted text")
    translated_text: str = Field(default="", description="Clean translated text")
    translation_failed: bool = Field(
        default=False, description="Translation failed and the original text is saved"
    )

    @field_validator("text", "translated_text")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        return v.strip()

    @property
    def duration(self) -> float:
        return self.end - self.start


@dataclass
class Job:
    id: int
    video_path: Path
    phase: int = 1
    audio_path: Path | None = None
    clean_audio_path: Path | None = None
    transcription: list[TranscriptionSegment] | None = None
    vad_timestamps: list[tuple[int, int]] | None = None


class Model(ABC):
    @abstractmethod
    def load(self) -> None: ...

    @abstractmethod
    def free(self) -> None: ...

    def __enter__(self):
        self.load()
        return self

    def __exit__(self, *_):
        self.free()
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return False
