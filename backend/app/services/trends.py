"""Training-load and trend analytics built on pandas.

All functions take plain lists of dicts (so they're easy to unit-test and reuse
from routes) and return JSON-serialisable structures for the frontend charts.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd


def _activities_frame(activities: list[dict]) -> pd.DataFrame:
    if not activities:
        return pd.DataFrame(
            columns=["date", "distance_m", "duration_s", "avg_hr", "training_load", "difficulty_score"]
        )
    df = pd.DataFrame(activities)
    df["date"] = pd.to_datetime(df["start_time"]).dt.tz_localize(None).dt.normalize()
    for col in ["distance_m", "duration_s", "avg_hr", "training_load", "difficulty_score", "avg_pace_s_per_km"]:
        if col not in df:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def weekly_mileage(activities: list[dict]) -> list[dict]:
    """Distance (km) and moving time per ISO week."""
    df = _activities_frame(activities)
    if df.empty:
        return []
    df["week"] = df["date"].dt.strftime("%G-W%V")
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

    We report an efficiency index = (avg_hr * avg_pace_s_per_km) / 1000 for runs with
    both HR and pace; a downward trend indicates improving aerobic fitness.
    """
    df = _activities_frame(activities)
    if df.empty:
        return []
    mask = df["avg_hr"].notna() & df["avg_pace_s_per_km"].notna() & (df["avg_pace_s_per_km"] > 0)
    df = df.loc[mask].sort_values("date")
    if df.empty:
        return []
    df["efficiency_index"] = (df["avg_hr"] * df["avg_pace_s_per_km"] / 1000.0).round(1)
    return [
        {"date": d.strftime("%Y-%m-%d"), "efficiency_index": float(e)}
        for d, e in zip(df["date"], df["efficiency_index"])
    ]


def sleep_vs_performance(activities: list[dict], daily: list[dict]) -> list[dict]:
    """Join each run's difficulty with the prior night's sleep score."""
    adf = _activities_frame(activities)
    if adf.empty or not daily:
        return []
    ddf = pd.DataFrame(daily)
    ddf["date"] = pd.to_datetime(ddf["date"]).dt.normalize()
    ddf = ddf[["date", "sleep_score", "body_battery_high"]]

    adf = adf[["date", "difficulty_score", "avg_hr"]].dropna(subset=["difficulty_score"])
    merged = adf.merge(ddf, on="date", how="inner").dropna(subset=["sleep_score"])
    return [
        {
            "date": d.strftime("%Y-%m-%d"),
            "sleep_score": round(float(s), 1),
            "difficulty_score": round(float(diff), 1),
            "body_battery_high": None if pd.isna(bb) else round(float(bb), 1),
        }
        for d, s, diff, bb in zip(
            merged["date"], merged["sleep_score"], merged["difficulty_score"], merged["body_battery_high"]
        )
    ]


def summary_stats(activities: list[dict], daily: list[dict]) -> dict:
    """High-level tiles for the dashboard header."""
    df = _activities_frame(activities)
    last7 = df.loc[df["date"] > df["date"].max() - pd.Timedelta(days=7)] if not df.empty else df

    total_km = round(float(df["distance_m"].sum()) / 1000.0, 1) if not df.empty else 0.0
    week_km = round(float(last7["distance_m"].sum()) / 1000.0, 1) if not last7.empty else 0.0

    latest_readiness = None
    if daily:
        ddf = pd.DataFrame(daily)
        ddf["date"] = pd.to_datetime(ddf["date"])
        ddf = ddf.sort_values("date")
        if "training_readiness" in ddf and ddf["training_readiness"].notna().any():
            latest_readiness = float(ddf["training_readiness"].dropna().iloc[-1])
        elif "body_battery_high" in ddf and ddf["body_battery_high"].notna().any():
            latest_readiness = float(ddf["body_battery_high"].dropna().iloc[-1])

    return {
        "total_runs": int(df.shape[0]) if not df.empty else 0,
        "total_distance_km": total_km,
        "this_week_km": week_km,
        "acwr": acwr(activities),
        "latest_readiness": latest_readiness,
    }
