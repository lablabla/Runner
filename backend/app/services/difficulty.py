"""Per-run difficulty scoring.

Produces a 0-100 ``difficulty_score`` plus a component breakdown so the UI can
explain *why* a run was hard. The score is a weighted blend of:

  intensity   – how hard the effort was (HR relative to max, or pace)
  duration    – longer efforts accumulate more strain
  elevation   – climbing adds load
  heat         – apparent temperature above a comfort band penalises the run
  readiness   – poor prior-night sleep / low body battery makes a run feel harder

Everything is deterministic and unit-testable. Missing inputs degrade gracefully:
components that can't be computed are dropped and the remaining weights renormalised.
"""
from __future__ import annotations

from dataclasses import dataclass

# Component weights (before renormalisation for missing data).
WEIGHTS = {
    "intensity": 0.35,
    "duration": 0.20,
    "elevation": 0.15,
    "heat": 0.15,
    "readiness": 0.15,
}

COMFORT_TEMP_C = 12.0  # ideal running temperature
HEAT_SPAN_C = 20.0  # degrees above comfort that map to a full heat penalty


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


@dataclass
class DifficultyInputs:
    duration_s: float | None = None
    distance_m: float | None = None
    avg_hr: float | None = None
    max_hr_user: float | None = None  # user's max HR (e.g. 220-age); falls back to 190
    elevation_gain_m: float | None = None
    apparent_temp_c: float | None = None
    # Readiness proxies (day of run)
    body_battery_high: float | None = None
    sleep_score: float | None = None


def _intensity(inp: DifficultyInputs) -> float | None:
    if inp.avg_hr is None:
        return None
    max_hr = inp.max_hr_user or 190.0
    # Map 55% (easy) -> 0 ... 95% (near max) -> 1
    frac = inp.avg_hr / max_hr
    return _clamp((frac - 0.55) / (0.95 - 0.55))


def _duration(inp: DifficultyInputs) -> float | None:
    if not inp.duration_s:
        return None
    # 0 at 0 min, ~1 around 150 min (a long run / race)
    return _clamp(inp.duration_s / (150 * 60))


def _elevation(inp: DifficultyInputs) -> float | None:
    if inp.elevation_gain_m is None or not inp.distance_m:
        return None
    # metres climbed per km; ~20 m/km is rolling, 40+ is hilly.
    grade = inp.elevation_gain_m / (inp.distance_m / 1000.0)
    return _clamp(grade / 40.0)


def _heat(inp: DifficultyInputs) -> float | None:
    if inp.apparent_temp_c is None:
        return None
    return _clamp((inp.apparent_temp_c - COMFORT_TEMP_C) / HEAT_SPAN_C)


def _readiness(inp: DifficultyInputs) -> float | None:
    """Higher output == harder because the athlete was under-recovered."""
    signals: list[float] = []
    if inp.body_battery_high is not None:
        signals.append(_clamp((100.0 - inp.body_battery_high) / 100.0))
    if inp.sleep_score is not None:
        signals.append(_clamp((100.0 - inp.sleep_score) / 100.0))
    if not signals:
        return None
    return sum(signals) / len(signals)


def compute_difficulty(inp: DifficultyInputs) -> tuple[float, dict]:
    """Return (score 0-100, breakdown dict of component contributions 0-100)."""
    components = {
        "intensity": _intensity(inp),
        "duration": _duration(inp),
        "elevation": _elevation(inp),
        "heat": _heat(inp),
        "readiness": _readiness(inp),
    }
    present = {k: v for k, v in components.items() if v is not None}
    if not present:
        return 0.0, {"note": "insufficient data"}

    total_weight = sum(WEIGHTS[k] for k in present)
    score = sum(WEIGHTS[k] * v for k, v in present.items()) / total_weight * 100.0

    breakdown = {k: round(v * 100.0, 1) for k, v in present.items()}
    breakdown["_weights"] = {k: round(WEIGHTS[k] / total_weight, 3) for k in present}
    return round(score, 1), breakdown
