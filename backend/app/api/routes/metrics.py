from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.api.routes._common import load_activity_dicts, load_daily_dicts
from app.database import get_db
from app.models import DailyMetric, User
from app.schemas.tracker import DailyMetricOut
from app.services import trends

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/daily", response_model=list[DailyMetricOut])
async def daily_metrics(
    days: int = Query(60, le=400),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[DailyMetric]:
    stmt = (
        select(DailyMetric)
        .where(DailyMetric.user_id == current.id)
        .order_by(DailyMetric.date.desc())
        .limit(days)
    )
    rows = list((await db.scalars(stmt)).all())
    return list(reversed(rows))


@router.get("/summary")
async def summary(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    activities = await load_activity_dicts(db, current.id)
    daily = await load_daily_dicts(db, current.id)
    return trends.summary_stats(activities, daily)


@router.get("/trends")
async def training_trends(
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    activities = await load_activity_dicts(db, current.id)
    daily = await load_daily_dicts(db, current.id)
    return {
        "weekly_mileage": trends.weekly_mileage(activities),
        "acwr": trends.acwr(activities),
        "aerobic_efficiency": trends.aerobic_efficiency(activities),
        "sleep_vs_performance": trends.sleep_vs_performance(activities, daily),
    }
