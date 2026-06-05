from typing import Any
from dataclasses import dataclass
from pathlib import Path
from abc import ABC, abstractmethod
from pydantic import BaseModel, Field, field_validator
import gc
import torch


class TranscriptionSegment(BaseModel):
    id: int = Field(..., description="ID único del segmento, comenzando en 1", ge=1)
    time_start: str = Field(..., description="Tiempo de inicio (ej. '00:01:23,456')")
    time_end: str = Field(..., description="Tiempo de finalización (ej. '00:01:23,456')")
    transcription: str = Field(..., description="Texto limpio de la transcripción")

    @field_validator("transcription")
    @classmethod
    def strip_spaces(cls, v: str) -> str:
        return v.strip()


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
        gc.collect()
        self.free()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        return False
