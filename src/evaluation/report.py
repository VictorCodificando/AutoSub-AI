from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import Any

from . import metrics
from .cues import Cue
from .rules import ERROR, WARNING, Thresholds, Violation, check


@dataclass
class FileReport:
    file: str
    run: str | None
    thresholds: dict[str, Any]
    aggregates: dict[str, Any]
    violations: list[Violation]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def evaluate(
    cues: list[Cue],
    *,
    name: str,
    thresholds: Thresholds = Thresholds(),
    regions: list[tuple[float, float]] | None = None,
    run: str | None = None,
    failed_translations: int | None = None,
) -> FileReport:
    violations = check(cues, thresholds)
    valid = [cue for cue in cues if metrics.duration(cue) > 0]
    speeds = [speed for cue in valid if (speed := metrics.cps(cue)) is not None]
    total = len(cues)

    rules: defaultdict[str, dict[str, float]] = defaultdict(lambda: {ERROR: 0, WARNING: 0})
    for violation in violations:
        rules[violation.rule][violation.severity] += 1
    for counts in rules.values():
        counts["pct"] = _pct(counts[ERROR] + counts[WARNING], total)

    aggregates: dict[str, Any] = {
        "n_cues": total,
        "n_errors": sum(v.severity == ERROR for v in violations),
        "n_warnings": sum(v.severity == WARNING for v in violations),
        "duration": metrics.aggregate([metrics.duration(c) for c in valid])._asdict(),
        "cps": metrics.aggregate(speeds)._asdict(),
        "rules": dict(sorted(rules.items())),
        "occupancy": metrics.occupancy(cues),
        "coverage": metrics.coverage(cues, regions),
        "translation_failed_rate": (
            failed_translations / total if failed_translations is not None and total else None
        ),
    }

    return FileReport(
        file=name,
        run=run,
        thresholds=asdict(thresholds),
        aggregates=aggregates,
        violations=violations,
    )


def _pct(part: float, total: int) -> float:
    return part / total * 100 if total else 0.0

