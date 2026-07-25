"""Helpers shared across analytics routes."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Activity, DailyMetric


async def load_activity_dicts(db: AsyncSession, user_id: int) -> list[dict]:
    rows = (
        await db.scalars(
            select(Activity).where(Activity.user_id == user_id).order_by(Activity.start_time)
        )
    ).all()
    return [
        {
            "id": a.id,
            "start_time": a.start_time,
            "sport_type": a.sport_type,
            "distance_m": a.distance_m,
            "duration_s": a.duration_s,
            "avg_hr": a.avg_hr,
            "max_hr": a.max_hr,
            "avg_cadence": a.avg_cadence,
            "avg_pace_s_per_km": a.avg_pace_s_per_km,
            "training_load": a.training_load,
            "difficulty_score": a.difficulty_score,
        }
        for a in rows
    ]


async def load_daily_dicts(db: AsyncSession, user_id: int) -> list[dict]:
    rows = (
        await db.scalars(
            select(DailyMetric).where(DailyMetric.user_id == user_id).order_by(DailyMetric.date)
        )
    ).all()
    out = []
    for m in rows:
        raw = m.raw or {}
        out.append(
            {
                "date": m.date,
                "sleep_seconds": m.sleep_seconds,
                "sleep_score": m.sleep_score,
                "body_battery_high": m.body_battery_high,
                "training_readiness": m.training_readiness,
                "resting_hr": m.resting_hr,
                "hrv_overnight": m.hrv_overnight,
                "stress_avg": m.stress_avg,
                "steps": m.steps,
                "respiration_avg": raw.get("respiration_avg"),
                "intensity_minutes": raw.get("intensity_minutes"),
                "active_calories": raw.get("active_calories"),
            }
        )
    return out
