from dataclasses import dataclass

from . import metrics
from .cues import Cue

ERROR = "error"
WARNING = "warning"


@dataclass(frozen=True)
class Thresholds:
    duration_min_warn: float = 1.0
    duration_min_error: float = 0.833
    duration_max_warn: float = 6.0
    duration_max_error: float = 7.0
    cps_warn: float = 17.0
    cps_error: float = 21.0
    cpl_warn: int = 37
    cpl_error: int = 42
    max_lines: int = 2
    min_gap: float = 0.083


PRESETS: dict[str, Thresholds] = {
    "default": Thresholds(),
    "ja": Thresholds(cps_warn=4.0, cps_error=5.0, cpl_warn=13, cpl_error=16),
    "zh": Thresholds(cps_warn=9.0, cps_error=11.0, cpl_warn=16, cpl_error=20),
    "ko": Thresholds(cps_warn=12.0, cps_error=15.0, cpl_warn=16, cpl_error=20),
}

_LANGUAGE_CODES = {"japanese": "ja", "chinese": "zh", "korean": "ko"}


def thresholds_for(language: str) -> Thresholds:
    key = language.lower()
    return PRESETS.get(_LANGUAGE_CODES.get(key, key), PRESETS["default"])


@dataclass(frozen=True)
class Violation:
    cue: int  # 1-based position in the list, matches SRT numbering of our output
    start: float
    rule: str
    value: float | None
    severity: str


Hit = tuple[str, float | None, str]


def check(cues: list[Cue], thresholds: Thresholds = Thresholds()) -> list[Violation]:
    violations: list[Violation] = []

    for number, cue in enumerate(cues, start=1):
        for rule, value, severity in _check_cue(cue, thresholds):
            violations.append(Violation(number, cue.start, rule, value, severity))

    for number, (current, following) in enumerate(zip(cues, cues[1:]), start=2):
        for rule, value, severity in _check_pair(current, following, thresholds):
            violations.append(Violation(number, following.start, rule, value, severity))

    return violations


def _check_cue(cue: Cue, t: Thresholds) -> list[Hit]:
    seconds = metrics.duration(cue)
    if seconds <= 0:
        return [("inverted", seconds, ERROR)]

    hits: list[Hit] = []
    if not metrics.has_content(cue):
        hits.append(("empty", None, ERROR))

    severity = _below(seconds, t.duration_min_warn, t.duration_min_error)
    if severity:
        hits.append(("duration_too_short", seconds, severity))

    severity = _above(seconds, t.duration_max_warn, t.duration_max_error)
    if severity:
        hits.append(("duration_too_long", seconds, severity))

    speed = metrics.cps(cue)
    severity = _above(speed, t.cps_warn, t.cps_error)
    if severity:
        hits.append(("cps_too_high", speed, severity))

    length = metrics.cpl(cue)
    severity = _above(length, t.cpl_warn, t.cpl_error)
    if severity:
        hits.append(("line_too_long", length, severity))

    lines = metrics.line_count(cue)
    if lines > t.max_lines:
        hits.append(("too_many_lines", lines, ERROR))

    return hits


def _check_pair(current: Cue, following: Cue, t: Thresholds) -> list[Hit]:
    if metrics.duration(current) <= 0 or metrics.duration(following) <= 0:
        return []
    if following.start < current.start:
        return [("out_of_order", following.start - current.start, ERROR)]

    hits: list[Hit] = []
    space = metrics.gap(current, following)
    if space < 0:
        hits.append(("overlap", space, ERROR))
    elif space < t.min_gap:
        hits.append(("gap_too_small", space, WARNING))

    if metrics.has_content(current) and _same_text(current, following):
        hits.append(("duplicate", None, WARNING))

    return hits


def _same_text(a: Cue, b: Cue) -> bool:
    return metrics.normalize(a.text, strip_accents=True) == metrics.normalize(
        b.text, strip_accents=True
    )


def _above(value: float, warn: float, error: float) -> str | None:
    if value > error:
        return ERROR
    if value > warn:
        return WARNING
    return None


def _below(value: float, warn: float, error: float) -> str | None:
    if value < error:
        return ERROR
    if value < warn:
        return WARNING
    return None
