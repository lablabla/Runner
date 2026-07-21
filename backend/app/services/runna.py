"""Runna helpers: detect Runna-tagged runs and parse an exported plan PDF.

Runna has no public API. Completed Runna workouts arrive through Garmin/Strava
with a recognisable tag ("with Runna"). The forward-looking plan can be entered
manually or extracted best-effort from an exported PDF (users can then correct it
in the UI).
"""
from __future__ import annotations

import io
import re
from datetime import date, datetime

_RUNNA_MARKERS = ("runna", "with runna")

_TYPE_KEYWORDS = {
    "tempo": "tempo",
    "threshold": "tempo",
    "interval": "intervals",
    "speed": "intervals",
    "long": "long",
    "easy": "easy",
    "recovery": "easy",
    "rest": "rest",
}

# Matches things like "5 km", "10km", "3.5 mi", "8 miles"
_DIST_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(km|kms|k|mi|miles|mile)\b", re.I)
# Matches an ISO or common date at the start of a plan line
_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})|(\d{1,2}/\d{1,2}/\d{2,4})")


def is_runna_activity(name: str | None, description: str | None = None) -> bool:
    haystack = f"{name or ''} {description or ''}".lower()
    return any(marker in haystack for marker in _RUNNA_MARKERS)


def classify_workout(text: str) -> str:
    low = text.lower()
    for keyword, wtype in _TYPE_KEYWORDS.items():
        if keyword in low:
            return wtype
    return "run"


def _to_metres(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit.startswith("mi") or unit == "mile":
        return value * 1609.34
    return value * 1000.0  # km / k


def _parse_date(token: str) -> date | None:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d/%m/%y", "%m/%d/%y"):
        try:
            return datetime.strptime(token, fmt).date()
        except ValueError:
            continue
    return None


def parse_plan_pdf(data: bytes) -> list[dict]:
    """Best-effort extraction of planned workouts from a Runna PDF export.

    Returns a list of dicts shaped like ``PlannedWorkoutIn``. Layouts vary, so this
    is deliberately forgiving — anything it can't confidently parse is skipped for
    the user to add manually.
    """
    try:
        import pdfplumber
    except ImportError:  # pragma: no cover
        return []

    workouts: list[dict] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            for line in text.splitlines():
                line = line.strip()
                if not line:
                    continue
                date_match = _DATE_RE.search(line)
                if not date_match:
                    continue
                parsed = _parse_date(date_match.group(0))
                if not parsed:
                    continue
                dist_match = _DIST_RE.search(line)
                distance_m = (
                    _to_metres(float(dist_match.group(1)), dist_match.group(2))
                    if dist_match
                    else None
                )
                workouts.append(
                    {
                        "date": parsed.isoformat(),
                        "workout_type": classify_workout(line),
                        "title": line[:120],
                        "description": line,
                        "distance_target_m": round(distance_m, 0) if distance_m else None,
                        "duration_target_s": None,
                    }
                )
    return workouts
