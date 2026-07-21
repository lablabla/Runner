"""Prompt construction for training insights."""
from __future__ import annotations

import json

SYSTEM = (
    "You are an experienced running coach analysing a runner's Garmin and weather "
    "data as they train for a half marathon. Be concise, specific and encouraging. "
    "Ground every observation in the numbers provided. Use short paragraphs and, "
    "where useful, a few bullet points. Flag injury/overtraining risk if the "
    "acute:chronic workload ratio is high. Do not invent data you were not given."
)


def weekly_summary_prompt(stats: dict, weekly: list[dict], sleep_perf: list[dict]) -> str:
    return (
        "Here is the athlete's recent training data as JSON.\n\n"
        f"Summary stats:\n{json.dumps(stats, indent=2, default=str)}\n\n"
        f"Weekly mileage/load:\n{json.dumps(weekly[-6:], indent=2, default=str)}\n\n"
        f"Sleep vs run difficulty:\n{json.dumps(sleep_perf[-10:], indent=2, default=str)}\n\n"
        "Write a weekly training summary: what went well, how load and recovery are "
        "trending, any risks, and one concrete focus for next week."
    )


def activity_prompt(activity: dict, day_metric: dict | None, weather: dict | None) -> str:
    return (
        "Analyse this single run and explain how hard it was and why.\n\n"
        f"Activity:\n{json.dumps(activity, indent=2, default=str)}\n\n"
        f"That day's recovery metrics:\n{json.dumps(day_metric, indent=2, default=str)}\n\n"
        f"Weather at start:\n{json.dumps(weather, indent=2, default=str)}\n\n"
        "In 3-4 sentences, explain the difficulty score's main drivers "
        "(intensity, heat, elevation, fatigue) and whether the effort looks appropriate."
    )
