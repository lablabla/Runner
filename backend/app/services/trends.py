"""Training-load and trend analytics built on pandas.

All functions take plain lists of dicts (so they're easy to unit-test and reuse
from routes) and return JSON-serialisable structures for the frontend charts.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from app.config import settings


def _activities_frame(activities: list[dict]) -> pd.DataFrame:
    if not activities:
        return pd.DataFrame(
            columns=[
                "date", "distance_m", "duration_s", "avg_hr", "training_load",
                "difficulty_score", "sport_type",
            ]
        )
    df = pd.DataFrame(activities)
    df["date"] = pd.to_datetime(df["start_time"]).dt.tz_localize(None).dt.normalize()
    for col in ["distance_m", "duration_s", "avg_hr", "training_load", "difficulty_score", "avg_pace_s_per_km"]:
        if col not in df:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "sport_type" not in df:
        df["sport_type"] = "running"
    return df


def _running(df: pd.DataFrame) -> pd.DataFrame:
    """Only running-type activities count toward mileage (swims/rides excluded)."""
    if df.empty:
        return df
    return df[df["sport_type"].fillna("").str.contains("run", case=False)]


def _week_start(ts: pd.Timestamp) -> pd.Timestamp:
    """Normalise a timestamp back to the start of its week per configured convention."""
    ts = pd.Timestamp(ts).normalize()
    # weekday(): Mon=0 .. Sun=6
    if settings.week_starts_on.lower() == "sunday":
        offset = (ts.weekday() + 1) % 7
    else:
        offset = ts.weekday()
    return ts - pd.Timedelta(days=offset)


def weekly_mileage(activities: list[dict]) -> list[dict]:
    """Distance (km) and moving time per ISO week."""
    df = _running(_activities_frame(activities))
    if df.empty:
        return []
    df = df.copy()
    df["week"] = df["date"].map(lambda d: _week_start(d).strftime("%Y-%m-%d"))
    grouped = df.groupby("week").agg(
        distance_km=("distance_m", lambda s: round(s.sum() / 1000.0, 1)),
        duration_h=("duration_s", lambda s: round(s.sum() / 3600.0, 2)),
        runs=("distance_m", "count"),
        avg_difficulty=("difficulty_score", lambda s: round(s.mean(), 1) if s.notna().any() else None),
    )
    records = grouped.reset_index().to_dict("records")
    # Cast numpy scalars to native Python types for clean JSON serialisation.
    for r in records:
        r["distance_km"] = float(r["distance_km"])
        r["duration_h"] = float(r["duration_h"])
        r["runs"] = int(r["runs"])
        r["avg_difficulty"] = None if r["avg_difficulty"] is None else float(r["avg_difficulty"])
    return records


def acwr(activities: list[dict], as_of: date | None = None) -> dict:
    """Acute:Chronic Workload Ratio.

    Acute = last 7 days of training load; chronic = trailing 28-day daily average * 7.
    A ratio in ~0.8-1.3 is the commonly cited "sweet spot"; >1.5 flags spike risk.
    Falls back to distance when explicit training_load is unavailable.
    """
    df = _activities_frame(activities)
    if df.empty:
        return {"acute": 0.0, "chronic": 0.0, "ratio": None, "zone": "no-data"}

    load = df["training_load"]
    if load.notna().sum() == 0:
        # Fallback: use km as a rough load proxy.
        df["load"] = df["distance_m"] / 1000.0
    else:
        df["load"] = load.fillna(df["distance_m"] / 1000.0)

    ref = pd.Timestamp(as_of) if as_of else df["date"].max()
    acute = df.loc[df["date"] > ref - pd.Timedelta(days=7), "load"].sum()
    chronic_total = df.loc[df["date"] > ref - pd.Timedelta(days=28), "load"].sum()
    chronic = chronic_total / 4.0  # average weekly load over 4 weeks

    ratio = round(float(acute / chronic), 2) if chronic > 0 else None
    if ratio is None:
        zone = "no-data"
    elif ratio < 0.8:
        zone = "detraining"
    elif ratio <= 1.3:
        zone = "optimal"
    elif ratio <= 1.5:
        zone = "caution"
    else:
        zone = "high-risk"

    return {"acute": round(float(acute), 1), "chronic": round(float(chronic), 1), "ratio": ratio, "zone": zone}


def aerobic_efficiency(activities: list[dict]) -> list[dict]:
    """Pace-per-heartbeat trend: lower pace (s/km) at a given HR over time == fitter.

    Efficiency index = (avg_hr * avg_pace_s_per_km) / 1000 for runs with both HR and
    pace; a downward trend indicates improving aerobic fitness. Restricted to running
    activities within plausible ranges so a bad-GPS run or a mislabelled swim/walk
    (tiny distance -> huge pace) can't blow up the scale.
    """
    df = _running(_activities_frame(activities))
    if df.empty:
        return []
    mask = (
        df["avg_hr"].notna()
        & df["avg_pace_s_per_km"].notna()
        & df["avg_pace_s_per_km"].between(150, 600)  # 2:30 – 10:00 /km
        & df["avg_hr"].between(90, 210)
    )
    df = df.loc[mask].sort_values("date")
    if df.empty:
        return []
    df["efficiency_index"] = (df["avg_hr"] * df["avg_pace_s_per_km"] / 1000.0).round(1)
    return [
        {"date": d.strftime("%Y-%m-%d"), "efficiency_index": float(e)}
        for d, e in zip(df["date"], df["efficiency_index"])
    ]


def sleep_vs_performance(activities: list[dict], daily: list[dict]) -> list[dict]:
    """Join each run's difficulty with that day's sleep.

    Uses sleep *duration* (hours) as the x-axis — it's universally available,
    whereas a numeric sleep score isn't reported by every device (e.g. FR245).
    """
    adf = _running(_activities_frame(activities))
    if adf.empty or not daily:
        return []
    ddf = pd.DataFrame(daily)
    ddf["date"] = pd.to_datetime(ddf["date"]).dt.normalize()
    for col in ("sleep_seconds", "sleep_score", "body_battery_high"):
        if col not in ddf:
            ddf[col] = None
    ddf["sleep_hours"] = pd.to_numeric(ddf["sleep_seconds"], errors="coerce") / 3600.0

    adf = adf[["date", "difficulty_score"]].dropna(subset=["difficulty_score"])
    merged = adf.merge(
        ddf[["date", "sleep_hours", "sleep_score", "body_battery_high"]], on="date", how="inner"
    ).dropna(subset=["sleep_hours"])
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "sleep_hours": round(float(h), 2),
            "sleep_score": None if pd.isna(s) else round(float(s), 1),
            "difficulty_score": round(float(diff), 1),
            "body_battery_high": None if pd.isna(bb) else round(float(bb), 1),
        }
        for d, h, s, diff, bb in zip(
            merged["date"], merged["sleep_hours"], merged["sleep_score"],
            merged["difficulty_score"], merged["body_battery_high"],
        )
    ]


def summary_stats(activities: list[dict], daily: list[dict]) -> dict:
    """High-level tiles for the dashboard header."""
    runs = _running(_activities_frame(activities))
    # "This week" = current calendar week (start day per WEEK_STARTS_ON), relative to today.
    week_start = _week_start(pd.Timestamp(date.today()))
    this_week = runs.loc[runs["date"] >= week_start] if not runs.empty else runs

    total_km = round(float(runs["distance_m"].sum()) / 1000.0, 1) if not runs.empty else 0.0
    week_km = round(float(this_week["distance_m"].sum()) / 1000.0, 1) if not this_week.empty else 0.0

    latest_readiness = None
    recovery: dict = {}
    if daily:
        ddf = pd.DataFrame(daily)
        ddf["date"] = pd.to_datetime(ddf["date"])
        ddf = ddf.sort_values("date")
        if "training_readiness" in ddf and ddf["training_readiness"].notna().any():
            latest_readiness = float(ddf["training_readiness"].dropna().iloc[-1])
        elif "body_battery_high" in ddf and ddf["body_battery_high"].notna().any():
            latest_readiness = float(ddf["body_battery_high"].dropna().iloc[-1])

        # Most recent non-null value for each recovery metric (for the dashboard panel).
        def latest(col: str):
            if col in ddf and ddf[col].notna().any():
                return float(ddf[col].dropna().iloc[-1])
            return None

        recovery = {
            "date": ddf["date"].dropna().iloc[-1].strftime("%Y-%m-%d") if ddf["date"].notna().any() else None,
            "sleep_seconds": latest("sleep_seconds"),
            "resting_hr": latest("resting_hr"),
            "body_battery_high": latest("body_battery_high"),
            "stress_avg": latest("stress_avg"),
            "steps": latest("steps"),
            "respiration_avg": latest("respiration_avg"),
            "intensity_minutes": latest("intensity_minutes"),
            "active_calories": latest("active_calories"),
        }

    return {
        "total_runs": int(runs.shape[0]) if not runs.empty else 0,
        "total_distance_km": total_km,
        "this_week_km": week_km,
        "acwr": acwr(activities),
        "latest_readiness": latest_readiness,
        "recovery": recovery,
    }
