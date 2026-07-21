"""Normalise provider-specific activity payloads into our common shape."""
from __future__ import annotations

from datetime import datetime, timezone

from app.services.runna import is_runna_activity


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    txt = value.replace("Z", "+00:00")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            dt = datetime.strptime(txt, fmt)
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        dt = datetime.fromisoformat(txt)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _pace(distance_m: float | None, duration_s: float | None) -> float | None:
    if not distance_m or not duration_s or distance_m <= 0:
        return None
    return round(duration_s / (distance_m / 1000.0), 1)


def normalize_garmin(a: dict) -> dict | None:
    activity_id = a.get("activityId")
    start = _dt(a.get("startTimeGMT") or a.get("startTimeLocal"))
    if activity_id is None or start is None:
        return None
    distance = a.get("distance")
    duration = a.get("duration")
    name = a.get("activityName")
    return {
        "source": "garmin",
        "source_id": str(activity_id),
        "name": name,
        "sport_type": (a.get("activityType") or {}).get("typeKey", "running"),
        "start_time": start,
        "distance_m": distance,
        "duration_s": duration,
        "moving_time_s": a.get("movingDuration"),
        "avg_pace_s_per_km": _pace(distance, a.get("movingDuration") or duration),
        "avg_hr": a.get("averageHR"),
        "max_hr": a.get("maxHR"),
        "avg_cadence": a.get("averageRunningCadenceInStepsPerMinute"),
        "elevation_gain_m": a.get("elevationGain"),
        "calories": a.get("calories"),
        "aerobic_te": a.get("aerobicTrainingEffect"),
        "anaerobic_te": a.get("anaerobicTrainingEffect"),
        "training_load": a.get("activityTrainingLoad"),
        "start_lat": a.get("startLatitude"),
        "start_lon": a.get("startLongitude"),
        "is_runna": is_runna_activity(name, a.get("description")),
        "raw": a,
    }


def normalize_strava(a: dict) -> dict | None:
    activity_id = a.get("id")
    start = _dt(a.get("start_date"))
    if activity_id is None or start is None:
        return None
    distance = a.get("distance")
    duration = a.get("moving_time")
    name = a.get("name")
    latlng = a.get("start_latlng") or [None, None]
    return {
        "source": "strava",
        "source_id": str(activity_id),
        "name": name,
        "sport_type": (a.get("sport_type") or a.get("type") or "Run").lower(),
        "start_time": start,
        "distance_m": distance,
        "duration_s": a.get("elapsed_time"),
        "moving_time_s": duration,
        "avg_pace_s_per_km": _pace(distance, duration),
        "avg_hr": a.get("average_heartrate"),
        "max_hr": a.get("max_heartrate"),
        "avg_cadence": (a.get("average_cadence") or 0) * 2 or None,  # Strava reports per-leg
        "elevation_gain_m": a.get("total_elevation_gain"),
        "calories": a.get("calories"),
        "aerobic_te": None,
        "anaerobic_te": None,
        "training_load": None,
        "start_lat": latlng[0] if latlng else None,
        "start_lon": latlng[1] if len(latlng) > 1 else None,
        "is_runna": is_runna_activity(name, a.get("description")),
        "raw": a,
    }
