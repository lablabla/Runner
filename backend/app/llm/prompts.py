"""Prompt construction for training insights."""
from __future__ import annotations

import json

SYSTEM = (
    "You are an elite running coach analysing a runner's Garmin, weather and "
    "training-load data as they work toward their running goals. Write like a "
    "sharp, experienced coach talking to an athlete you respect.\n\n"
    "Rules:\n"
    "- Be specific and quantitative. Cite the actual numbers you were given "
    "(distances, paces, HR, ACWR, sleep). Never invent data you were not given; "
    "if something important is missing, say so briefly.\n"
    "- Lead with what matters most (injury/overtraining risk, or the biggest "
    "positive signal), not generic praise. Skip filler like 'great job'.\n"
    "- Interpret, don't just restate: explain what the trend means for their "
    "training and race readiness.\n"
    "- Give 2-3 concrete, actionable recommendations for the coming week.\n"
    "- Flag risk explicitly when the acute:chronic workload ratio (ACWR) is above "
    "1.3 (elevated) or 1.5 (high injury risk), or when weekly volume jumped more "
    "than ~10%.\n"
    "- Keep it tight: ~150-220 words, a short opening read plus a few bullet points."
)


def _round_list(items: list[dict], keys: list[str]) -> list[dict]:
    out = []
    for it in items:
        row = {}
        for k in keys:
            v = it.get(k)
            row[k] = round(v, 2) if isinstance(v, float) else v
        out.append(row)
    return out


def weekly_summary_prompt(
    stats: dict,
    weekly: list[dict],
    efficiency: list[dict],
    sleep_perf: list[dict],
    recent: list[dict],
    recovery: dict | None,
) -> str:
    recent_rows = [
        {
            "date": r.get("start_time"),
            "km": round((r.get("distance_m") or 0) / 1000.0, 2),
            "pace_s_per_km": r.get("avg_pace_s_per_km"),
            "avg_hr": r.get("avg_hr"),
            "difficulty": r.get("difficulty_score"),
        }
        for r in recent[-8:]
    ]
    blocks = {
        "summary": stats,
        "weekly_mileage_recent": weekly[-6:],
        "aerobic_efficiency_recent": efficiency[-8:],
        "sleep_vs_difficulty": sleep_perf[-8:],
        "recent_runs": recent_rows,
        "latest_recovery": recovery or {},
    }
    return (
        "Analyse this athlete's recent running training. Data as JSON "
        "(nulls mean not recorded by the device):\n\n"
        f"{json.dumps(blocks, indent=2, default=str)}\n\n"
        "Write the weekly coaching summary: (1) the headline read on load and "
        "recovery, with explicit ACWR risk framing; (2) how mileage, pace-at-HR "
        "efficiency and difficulty are trending; (3) 2-3 specific actions for next "
        "week. Reference the actual numbers."
    )


def activity_prompt(activity: dict, day_metric: dict | None, weather: dict | None) -> str:
    return (
        "Analyse this single run and explain how hard it was and why.\n\n"
        f"Activity:\n{json.dumps(activity, indent=2, default=str)}\n\n"
        f"That day's recovery metrics:\n{json.dumps(day_metric, indent=2, default=str)}\n\n"
        f"Weather at start:\n{json.dumps(weather, indent=2, default=str)}\n\n"
        "In 4-6 sentences: explain the difficulty score's main drivers (intensity, "
        "heat, elevation, fatigue), whether the effort looks appropriate for the "
        "session, and one takeaway. Cite the actual numbers."
    )
