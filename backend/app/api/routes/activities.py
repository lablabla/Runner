from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Activity, User
from app.schemas.tracker import ActivityOut

router = APIRouter(prefix="/activities", tags=["activities"])


@router.get("", response_model=list[ActivityOut])
async def list_activities(
    limit: int = Query(50, le=500),
    offset: int = 0,
    sport_type: str | None = None,
    runna_only: bool = False,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Activity]:
    stmt = (
        select(Activity)
        .where(Activity.user_id == current.id)
        .options(selectinload(Activity.weather))
        .order_by(Activity.start_time.desc())
        .limit(limit)
        .offset(offset)
    )
    if sport_type:
        stmt = stmt.where(Activity.sport_type == sport_type)
    if runna_only:
        stmt = stmt.where(Activity.is_runna.is_(True))
    return list((await db.scalars(stmt)).all())


@router.get("/{activity_id}", response_model=ActivityOut)
async def get_activity(
    activity_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Activity:
    act = await db.scalar(
        select(Activity)
        .where(Activity.id == activity_id, Activity.user_id == current.id)
        .options(selectinload(Activity.weather))
    )
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    return act


@router.get("/{activity_id}/weather-debug")
async def weather_debug(
    activity_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Diagnostic: show what each weather provider returns for this run's point/time
    and which one the app would use."""
    from app.services.weather import debug_weather_at

    act = await db.scalar(
        select(Activity).where(Activity.id == activity_id, Activity.user_id == current.id)
    )
    if not act:
        raise HTTPException(status_code=404, detail="Activity not found")
    lat = act.start_lat if act.start_lat is not None else current.home_lat
    lon = act.start_lon if act.start_lon is not None else current.home_lon
    if lat is None or lon is None:
        raise HTTPException(status_code=400, detail="Activity has no GPS and no home location set")
    result = await debug_weather_at(lat, lon, act.start_time)
    result["activity_start_utc"] = act.start_time.isoformat()
    result["coords_from"] = "gps" if act.start_lat is not None else "home"
    return result
