from typing import Any
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Job:
    id: int
    video_path: Path
    phase: int = 1
    audio_path: Path | None = None
    clean_audio_path: Path | None = None
    transcription: dict[str, Any] | None = None
    vad_timestamps: list[tuple[int, int]] | None = None
