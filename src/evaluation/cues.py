from collections import Counter
from pathlib import Path
from typing import NamedTuple

import pysubs2

from ..models import TranscriptionSegment

# utf-8-sig also decodes plain utf-8, so it covers files with and without BOM
DEFAULT_ENCODING = "utf-8-sig"


class Cue(NamedTuple):
    start: float
    end: float
    text: str


def from_segments(
    segments: list[TranscriptionSegment], *, translated: bool
) -> list[Cue]:
    return [
        Cue(
            start=segment.start,
            end=segment.end,
            text=segment.translated_text if translated else segment.text,
        )
        for segment in segments
    ]


def from_file(
    path: Path,
    *,
    styles: set[str] | None = None,
    encoding: str = DEFAULT_ENCODING,
) -> list[Cue]:
    subs = pysubs2.load(str(path), encoding=encoding)
    # SRT and VTT have no real styles, every event is "Default"
    allowed = styles if subs.format in ("ass", "ssa") else None

    cues: list[Cue] = []
    for event in subs:
        if not event.is_text:
            continue
        if allowed is not None and event.style not in allowed:
            continue

        # Empty cues are kept so the validator can flag them and numbering stays aligned
        text = event.plaintext.strip()
        cues.append(Cue(start=event.start / 1000, end=event.end / 1000, text=text))

    return cues


def styles_in(path: Path, *, encoding: str = DEFAULT_ENCODING) -> dict[str, int]:
    subs = pysubs2.load(str(path), encoding=encoding)
    return dict(Counter(event.style for event in subs if event.is_text).most_common())
