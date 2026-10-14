import re
import statistics
import unicodedata
from typing import NamedTuple

from .cues import Cue

Interval = tuple[float, float]


class Stats(NamedTuple):
    median: float | None
    p90: float | None
    maximum: float | None
    minimum: float | None


def duration(cue: Cue) -> float:
    return cue.end - cue.start


def cps(cue: Cue) -> float | None:
    seconds = duration(cue)
    if seconds <= 0:
        return None
    return len(cue.text.replace("\n", "")) / seconds


def cpl(cue: Cue) -> int:
    return max(len(line) for line in cue.text.split("\n"))


def line_count(cue: Cue) -> int:
    return cue.text.count("\n") + 1


def has_content(cue: Cue) -> bool:
    return any(char.isalnum() for char in cue.text)


def normalize(text: str, *, strip_accents: bool = False) -> str:
    text = unicodedata.normalize("NFC", text.lower().strip())
    if strip_accents:
        text = _strip_latin_accents(text)
    text = re.sub(r"[^\w\s]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_latin_accents(text: str) -> str:
    # Only drop marks that sit on Latin letters, so Japanese dakuten survive
    kept: list[str] = []
    base = ""
    for char in unicodedata.normalize("NFD", text):
        if unicodedata.category(char) == "Mn":
            if unicodedata.name(base, "").startswith("LATIN"):
                continue
        else:
            base = char
        kept.append(char)
    return unicodedata.normalize("NFC", "".join(kept))


def gap(current: Cue, following: Cue) -> float:
    return following.start - current.end


def aggregate(values: list[float]) -> Stats:
    if not values:
        return Stats(median=None, p90=None, maximum=None, minimum=None)
    if len(values) == 1:
        p90 = values[0]
    else:
        p90 = statistics.quantiles(values, n=10, method="inclusive")[-1]
    return Stats(
        median=statistics.median(values),
        p90=p90,
        maximum=max(values),
        minimum=min(values),
    )


def occupancy(cues: list[Cue]) -> float | None:
    intervals = _merge([(cue.start, cue.end) for cue in cues if duration(cue) > 0])
    if not intervals:
        return None
    span = intervals[-1][1] - intervals[0][0]
    if span <= 0:
        return None
    return _total(intervals) / span


def coverage(cues: list[Cue], regions: list[Interval] | None) -> float | None:
    if not regions:
        return None
    speech = _merge(regions)
    speech_total = _total(speech)
    if speech_total <= 0:
        return None
    subtitled = _merge([(cue.start, cue.end) for cue in cues if duration(cue) > 0])
    return _intersection(subtitled, speech) / speech_total


def _merge(intervals: list[Interval]) -> list[Interval]:
    merged: list[Interval] = []
    for start, end in sorted(intervals):
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def _total(intervals: list[Interval]) -> float:
    return sum(end - start for start, end in intervals)


def _intersection(a: list[Interval], b: list[Interval]) -> float:
    total, i, j = 0.0, 0, 0
    while i < len(a) and j < len(b):
        low = max(a[i][0], b[j][0])
        high = min(a[i][1], b[j][1])
        if high > low:
            total += high - low
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return total
