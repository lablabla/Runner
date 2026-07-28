from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.api.routes._common import load_activity_dicts, load_daily_dicts
from app.database import get_db
from app.llm.factory import build_provider
from app.llm.prompts import SYSTEM, activity_prompt, format_pace, weekly_summary_prompt
from app.models import Activity, DailyMetric, Insight, User
from app.schemas.tracker import InsightOut
from app.services import trends

router = APIRouter(prefix="/analysis", tags=["analysis"])


def _round(v, n=0):
    return round(v, n) if isinstance(v, (int, float)) else None


@router.get("/insights", response_model=list[InsightOut])
async def list_insights(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[Insight]:
    rows = (
        await db.scalars(
            select(Insight)
            .where(Insight.user_id == current.id)
            .order_by(Insight.created_at.desc())
            .limit(30)
        )
    ).all()
    return list(rows)


@router.delete("/insights", status_code=204, response_class=Response)
async def clear_insights(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
):
    """Delete all of the current user's insights."""
    await db.execute(delete(Insight).where(Insight.user_id == current.id))
    await db.commit()


@router.delete("/insights/{insight_id}", status_code=204, response_class=Response)
async def delete_insight(
    insight_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    row = await db.scalar(
        select(Insight).where(Insight.id == insight_id, Insight.user_id == current.id)
    )
    if row:
        await db.delete(row)
        await db.commit()


@router.post("/weekly-summary", response_model=InsightOut)
async def generate_weekly_summary(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> Insight:
    provider = build_provider()
    activities = await load_activity_dicts(db, current.id)
    daily = await load_daily_dicts(db, current.id)

    stats = trends.summary_stats(activities, daily)
    weekly = trends.weekly_mileage(activities)
    efficiency = trends.aerobic_efficiency(activities)
    sleep_perf = trends.sleep_vs_performance(activities, daily)
    recovery = stats.get("recovery") or {}

    prompt = weekly_summary_prompt(stats, weekly, efficiency, sleep_perf, activities, recovery)
    try:
        # Generous ceiling: "thinking" models (e.g. Gemini flash) spend part of the
        # budget on reasoning, so a low cap truncates the visible answer.
        content = await provider.generate(SYSTEM, prompt, max_tokens=8192)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    period = datetime.now(timezone.utc).strftime("%G-W%V")
    insight = Insight(
        user_id=current.id, kind="weekly_summary", period=period, content=content, model=provider.model
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight


@router.post("/activity/{activity_id}", response_model=InsightOut)
async def analyse_activity(
    activity_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Insight:
    act = await db.scalar(
        select(Activity)
        .where(Activity.id == activity_id, Activity.user_id == current.id)
        .options(selectinload(Activity.weather))
    )
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")

    provider = build_provider()
    day_metric = await db.scalar(
        select(DailyMetric).where(
            DailyMetric.user_id == current.id, DailyMetric.date == act.start_time.date()
        )
    )
    breakdown = {
        k: (_round(v, 1) if isinstance(v, (int, float)) else v)
        for k, v in (act.difficulty_breakdown or {}).items()
        if k != "_weights"
    }
    activity_dict = {
        "name": act.name,
        "start_time": act.start_time,
        "distance_km": round((act.distance_m or 0) / 1000.0, 1),
        "duration_min": round((act.duration_s or 0) / 60.0, 0),
        "avg_hr": _round(act.avg_hr),
        "max_hr": _round(act.max_hr),
        "avg_cadence": _round(act.avg_cadence),
        "pace": format_pace(act.avg_pace_s_per_km),
        "elevation_gain_m": _round(act.elevation_gain_m),
        "difficulty_score": _round(act.difficulty_score, 1),
        "difficulty_breakdown": breakdown,
    }
    day_dict = (
        {
            "body_battery_high": _round(day_metric.body_battery_high),
            "resting_hr": _round(day_metric.resting_hr),
            "sleep_hours": _round((day_metric.sleep_seconds or 0) / 3600.0, 1) if day_metric.sleep_seconds else None,
            "stress_avg": _round(day_metric.stress_avg),
        }
        if day_metric
        else None
    )
    weather_dict = (
        {
            "temp_c": _round(act.weather.temp_c),
            "feels_like_c": _round(act.weather.apparent_temp_c),
            "humidity_pct": _round(act.weather.humidity_pct),
            "wind_kmh": _round(act.weather.wind_speed_kmh),
            "summary": act.weather.summary,
        }
        if act.weather
        else None
    )

    prompt = activity_prompt(activity_dict, day_dict, weather_dict)
    try:
        content = await provider.generate(SYSTEM, prompt, max_tokens=4096)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    insight = Insight(
        user_id=current.id,
        kind="activity",
        period=str(activity_id),
        content=content,
        model=provider.model,
    )
    db.add(insight)
    await db.commit()
    await db.refresh(insight)
    return insight
