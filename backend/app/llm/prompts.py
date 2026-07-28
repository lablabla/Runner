"""Prompt construction for training insights."""
from __future__ import annotations

import json
from typing import Any

SYSTEM = (
    "You are an elite running coach analysing a runner's Garmin, weather and "
    "training-load data as they work toward their running goals. Write like a "
    "sharp, experienced coach talking to an athlete you respect.\n\n"
    "Rules:\n"
    "- Only reference metrics that appear in the data provided. The data given is "
    "the complete set available — do NOT mention, list, or speculate about any "
    "metric that is absent (e.g. don't note that HRV, sleep score, or anything "
    "else is 'missing' or 'not provided'). Never invent numbers.\n"
    "- Lead with what matters most (injury/overtraining risk, or the biggest "
    "positive signal), not generic praise. Skip filler like 'great job'.\n"
    "- Interpret, don't just restate: explain what the trend means for their "
    "training and race readiness.\n"
    "- Give 2-3 concrete, actionable recommendations for the coming week.\n"
    "- Flag risk explicitly when the acute:chronic workload ratio (ACWR) is above "
    "1.3 (elevated) or 1.5 (high injury risk), or when weekly volume jumped more "
    "than ~10%.\n"
    "- Use human units: pace as min:sec per km (e.g. 5:30/km), distance in km, "
    "temperature in °C. Round sensibly — no false precision (say 39 m, not 39.29 m; "
    "78% humidity, not 77.82%).\n"
    "- Keep it tight: ~150-220 words, a short opening read plus a few bullet points."
)


def format_pace(sec_per_km: float | None) -> str | None:
    """Seconds/km -> 'm:ss/km' (the unit runners actually read)."""
    if not sec_per_km or sec_per_km <= 0:
        return None
    m = int(sec_per_km // 60)
    s = int(round(sec_per_km % 60))
    if s == 60:
        m, s = m + 1, 0
    return f"{m}:{s:02d}/km"


def _clean(obj: Any) -> Any:
    """Recursively drop null/empty values so the model never sees absent metrics."""
    if isinstance(obj, dict):
        cleaned = {k: _clean(v) for k, v in obj.items()}
        return {k: v for k, v in cleaned.items() if v is not None and v != {} and v != []}
    if isinstance(obj, list):
        items = [_clean(v) for v in obj]
        return [v for v in items if v is not None and v != {} and v != []]
    return obj


def weekly_summary_prompt(
    stats: dict,
    weekly: list[dict],
    efficiency: list[dict],
    sleep_perf: list[dict],
    recent: list[dict],
    recovery: dict | None,
) -> str:
    def _round(v, n=0):
        return round(v, n) if isinstance(v, (int, float)) else None

    recent_rows = [
        {
            "date": r.get("start_time"),
            "km": round((r.get("distance_m") or 0) / 1000.0, 1),
            "pace": format_pace(r.get("avg_pace_s_per_km")),
            "avg_hr": _round(r.get("avg_hr")),
            "avg_cadence": _round(r.get("avg_cadence")),
            "difficulty": _round(r.get("difficulty_score")),
        }
        for r in recent[-8:]
    ]
    blocks = _clean(
        {
            "summary": stats,
            "weekly_mileage_recent": weekly[-6:],
            "aerobic_efficiency_recent": efficiency[-8:],
            "sleep_vs_difficulty": sleep_perf[-8:],
            "recent_runs": recent_rows,
            "latest_recovery": recovery or {},
        }
    )
    return (
        "Analyse this athlete's recent running training. The JSON below contains "
        "every metric available — treat it as complete:\n\n"
        f"{json.dumps(blocks, indent=2, default=str)}\n\n"
        "Write the weekly coaching summary: (1) the headline read on load and "
        "recovery, with explicit ACWR risk framing; (2) how mileage, pace-at-HR "
        "efficiency and difficulty are trending; (3) 2-3 specific actions for next "
        "week. Reference the actual numbers."
    )


def activity_prompt(activity: dict, day_metric: dict | None, weather: dict | None) -> str:
    blocks = _clean(
        {
            "activity": activity,
            "recovery_that_day": day_metric or {},
            "weather_at_start": weather or {},
        }
    )
    return (
        "Analyse this single run and explain how hard it was and why. The JSON below "
        "contains every metric available — treat it as complete:\n\n"
        f"{json.dumps(blocks, indent=2, default=str)}\n\n"
        "In 4-6 sentences: explain the difficulty score's main drivers (intensity, "
        "heat, elevation, fatigue), whether the effort looks appropriate for the "
        "session, and one takeaway. Cite the actual numbers."
    )
