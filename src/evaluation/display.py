import os
import sys
from collections import defaultdict
from typing import Any, Callable, NamedTuple

from ..utils.utils import format_time
from .report import FileReport
from .rules import ERROR, Thresholds, Violation

GREEN, YELLOW, ORANGE, RED = range(4)

Grade = Callable[[float], int]

_COLORS = {
    GREEN: "\033[32m",
    YELLOW: "\033[33m",
    ORANGE: "\033[38;5;208m",
    RED: "\033[1;31m",
}
_RESET = "\033[0m"

# Percent of cues with errors: (green max, yellow max, orange max)
_PCT_BANDS = (2.0, 5.0, 15.0)
# Rules that are bugs rather than style, so any hit is suspicious
_STRICT_PCT_BANDS = (0.0, 1.0, 3.0)

# Rules shown as columns, with their header and bands
TABLE_RULES = {
    "duration_too_long": ("Largos", _PCT_BANDS),
    "duration_too_short": ("Cortos", _PCT_BANDS),
    "cps_too_high": ("Rápidos", _PCT_BANDS),
    "line_too_long": ("Anchos", _PCT_BANDS),
    "overlap": ("Solapes", _STRICT_PCT_BANDS),
    "empty": ("Vacíos", _STRICT_PCT_BANDS),
}

# A typical median cue lasts between these values (seconds)
_MEDIAN_DURATION_LOW = (1.5, 1.2)
_MEDIAN_DURATION_HIGH = (4.0, 5.0)


class Cell(NamedTuple):
    text: str
    level: int | None = None


def format_table(reports: list[FileReport], *, color: bool | None = None) -> str:
    if color is None:
        color = _use_color()

    show_failed = any(r.aggregates["translation_failed_rate"] is not None for r in reports)

    headers = ["Fichero", "Cues", "Dur.med", "Dur.máx", "CPS med", "CPS p90"]
    headers += [header for header, _ in TABLE_RULES.values()]
    headers.append("Ocup.")
    if show_failed:
        headers.append("Trad.fallida")

    rows = [_row(report, show_failed) for report in reports]

    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell.text))

    lines = [
        _join([Cell(h) for h in headers], widths, color=False),
        "  ".join("-" * w for w in widths),
    ]
    lines += [_join(row, widths, color=color) for row in rows]
    lines.append("")
    lines.append(_legend(color))
    lines.append("Columnas de reglas: % de cues con error (no cuenta avisos).")
    return "\n".join(lines)


def format_details(report: FileReport, *, color: bool | None = None) -> str:
    if color is None:
        color = _use_color()

    worst: dict[str, Violation] = {}
    counts: dict[str, int] = defaultdict(int)
    for violation in report.violations:
        if violation.severity != ERROR:
            continue
        counts[violation.rule] += 1
        current = worst.get(violation.rule)
        if current is None or abs(violation.value or 0) > abs(current.value or 0):
            worst[violation.rule] = violation

    agg = report.aggregates
    errors = _paint(f"{agg['n_errors']} errores", RED if agg["n_errors"] else GREEN, color)
    lines = [f"{report.file}: {errors}, {agg['n_warnings']} avisos"]
    if not worst:
        lines.append("  sin errores")

    total = agg["n_cues"]
    for rule, violation in sorted(worst.items(), key=lambda item: -counts[item[0]]):
        bands = TABLE_RULES.get(rule, ("", _STRICT_PCT_BANDS))[1]
        level = _rising(_pct(counts[rule], total), bands)
        name = _paint(f"{rule:<20}", level, color)
        value = "" if violation.value is None else f"valor {violation.value:.2f}"
        lines.append(
            f"  {name} {counts[rule]:>5}   peor: cue {violation.cue} @ {format_time(violation.start)}  {value}"
        )
    return "\n".join(lines)


def _row(report: FileReport, show_failed: bool) -> list[Cell]:
    agg: dict[str, Any] = report.aggregates
    t = Thresholds(**report.thresholds)
    total: int = agg["n_cues"]
    duration = agg["duration"]
    speed = agg["cps"]

    row = [
        Cell(report.file),
        Cell(str(total)),
        _cell(duration["median"], "{:.2f}s", _median_duration_level(t)),
        _cell(
            duration["maximum"],
            "{:.2f}s",
            lambda v: _rising(v, (t.duration_max_warn, t.duration_max_error, 10.0)),
        ),
        _cell(
            speed["median"],
            "{:.1f}",
            lambda v: _rising(v, (t.cps_warn, t.cps_error, t.cps_error * 1.25)),
        ),
        _cell(
            speed["p90"],
            "{:.1f}",
            lambda v: _rising(v, (t.cps_error, t.cps_error * 1.15, t.cps_error * 1.4)),
        ),
    ]

    for rule, (_, bands) in TABLE_RULES.items():
        errors = agg["rules"].get(rule, {}).get(ERROR, 0)
        pct = _pct(errors, total)
        row.append(Cell(f"{pct:.1f}%", _rising(pct, bands)))

    # Occupancy depends on the content, so it is not graded
    occupancy = agg["occupancy"]
    row.append(Cell("—" if occupancy is None else f"{occupancy * 100:.0f}%"))

    if show_failed:
        rate = agg["translation_failed_rate"]
        row.append(
            Cell("—")
            if rate is None
            else Cell(f"{rate * 100:.1f}%", _rising(rate * 100, _STRICT_PCT_BANDS))
        )

    return row


def _median_duration_level(t: Thresholds) -> Grade:
    def level(value: float) -> int:
        low = _falling(value, (*_MEDIAN_DURATION_LOW, t.duration_min_warn))
        high = _rising(value, (*_MEDIAN_DURATION_HIGH, t.duration_max_warn))
        return max(low, high)

    return level


def _cell(value: float | None, fmt: str, grade: Grade) -> Cell:
    if value is None:
        return Cell("—")
    return Cell(fmt.format(value), grade(value))


def _rising(value: float, limits: tuple[float, float, float]) -> int:
    for level, limit in enumerate(limits):
        if value <= limit:
            return level
    return RED


def _falling(value: float, limits: tuple[float, float, float]) -> int:
    for level, limit in enumerate(limits):
        if value >= limit:
            return level
    return RED


def _join(row: list[Cell], widths: list[int], *, color: bool) -> str:
    parts: list[str] = []
    for i, (cell, width) in enumerate(zip(row, widths)):
        text = cell.text.ljust(width) if i == 0 else cell.text.rjust(width)
        parts.append(_paint(text, cell.level, color))
    return "  ".join(parts)


def _paint(text: str, level: int | None, color: bool) -> str:
    if not color or level is None:
        return text
    return f"{_COLORS[level]}{text}{_RESET}"


def _legend(color: bool) -> str:
    items = [
        (GREEN, "normal"),
        (YELLOW, "algo fuera"),
        (ORANGE, "bastante fuera"),
        (RED, "nada normal"),
    ]
    return "Leyenda: " + "  ".join(_paint(f"■ {label}", level, color) for level, label in items)


def _use_color() -> bool:
    if "NO_COLOR" in os.environ:
        return False
    if "FORCE_COLOR" in os.environ:
        return True
    return sys.stdout.isatty()


def _pct(part: float, total: int) -> float:
    return part / total * 100 if total else 0.0
