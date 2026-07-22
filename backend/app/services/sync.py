"""Per-user sync orchestration.

Pulls activities and wellness from connected providers, normalises and upserts
them, enriches runs with weather, and computes difficulty scores. Designed to be
called from both the API (manual sync) and the scheduler (nightly).
"""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.core.crypto import decrypt_json, encrypt_json
from app.models import Activity, DailyMetric, IntegrationCredential, User, Weather
from app.services import strava as strava_svc
from app.services.difficulty import DifficultyInputs, compute_difficulty
from app.services.garmin import GarminAuthError, GarminClient
from app.services.normalize import normalize_garmin, normalize_strava
from app.services.weather import fetch_weather_at

logger = logging.getLogger(__name__)


async def _get_cred(db: AsyncSession, user_id: int, provider: str) -> IntegrationCredential | None:
    return await db.scalar(
        select(IntegrationCredential).where(
            IntegrationCredential.user_id == user_id,
            IntegrationCredential.provider == provider,
        )
    )


async def _mark(db: AsyncSession, cred: IntegrationCredential, status: str, detail: str | None) -> None:
    cred.status = status
    cred.status_detail = detail
    cred.last_sync_at = datetime.now(timezone.utc)
    await db.commit()


async def sync_user(db: AsyncSession, user: User) -> dict:
    result = {
        "activities_added": 0,
        "activities_updated": 0,
        "daily_metrics_upserted": 0,
        "weather_enriched": 0,
        "errors": [],
    }
    since = date.today() - timedelta(days=settings.activity_backfill_days)

    await _sync_garmin(db, user, since, result)
    await _sync_strava(db, user, since, result)
    await _enrich_and_score(db, user, result)
    return result


async def _upsert_activity(db: AsyncSession, user_id: int, norm: dict, result: dict) -> None:
    existing = await db.scalar(
        select(Activity).where(
            Activity.user_id == user_id,
            Activity.source == norm["source"],
            Activity.source_id == norm["source_id"],
        )
    )
    if existing:
        for key, value in norm.items():
            setattr(existing, key, value)
        result["activities_updated"] += 1
    else:
        db.add(Activity(user_id=user_id, **norm))
        result["activities_added"] += 1


async def _sync_garmin(db: AsyncSession, user: User, since: date, result: dict) -> None:
    cred = await _get_cred(db, user.id, "garmin")
    if not cred:
        return
    try:
        payload = decrypt_json(cred.encrypted_payload)
        client = await asyncio.to_thread(GarminClient.from_payload, payload)
        # Persist refreshed tokens if the login updated them.
        new_payload = client.export_payload()
        if new_payload != payload:
            cred.encrypted_payload = encrypt_json(new_payload)

        activities = await asyncio.to_thread(client.get_activities_since, since)
        for raw in activities:
            norm = normalize_garmin(raw)
            if norm:
                await _upsert_activity(db, user.id, norm, result)

        # Daily wellness for the recent window (last 60 days to bound API calls).
        # Throttle slightly between days so Garmin doesn't rate-limit the loop —
        # that throttling is what previously left most days without wellness data.
        wellness_start = max(since, date.today() - timedelta(days=60))
        for day in _date_range(wellness_start, date.today()):
            data = await asyncio.to_thread(client.get_daily_wellness, day)
            await _upsert_daily_metric(db, user.id, day, data, result)
            await asyncio.sleep(0.25)

        await _mark(db, cred, "connected", None)
    except GarminAuthError as exc:
        await _mark(db, cred, "error", str(exc))
        result["errors"].append(f"garmin: {exc}")
    except Exception as exc:  # noqa: BLE001
        logger.exception("Garmin sync failed")
        await _mark(db, cred, "error", str(exc))
        result["errors"].append(f"garmin: {exc}")


async def _sync_strava(db: AsyncSession, user: User, since: date, result: dict) -> None:
    cred = await _get_cred(db, user.id, "strava")
    if not cred:
        return
    try:
        payload = decrypt_json(cred.encrypted_payload)
        after = int(time.mktime(since.timetuple()))
        activities, payload = await strava_svc.fetch_activities(payload, after)
        cred.encrypted_payload = encrypt_json(payload)
        for raw in activities:
            norm = normalize_strava(raw)
            # Prefer Garmin for the same run; skip Strava dup only if a Garmin one
            # exists at the same start minute.
            if norm and not await _garmin_duplicate(db, user.id, norm["start_time"]):
                await _upsert_activity(db, user.id, norm, result)
        await _mark(db, cred, "connected", None)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Strava sync failed")
        await _mark(db, cred, "error", str(exc))
        result["errors"].append(f"strava: {exc}")


async def _garmin_duplicate(db: AsyncSession, user_id: int, start: datetime) -> bool:
    window = timedelta(minutes=5)
    found = await db.scalar(
        select(Activity).where(
            Activity.user_id == user_id,
            Activity.source == "garmin",
            Activity.start_time >= start - window,
            Activity.start_time <= start + window,
        )
    )
    return found is not None


async def _upsert_daily_metric(db: AsyncSession, user_id: int, day: date, data: dict, result: dict) -> None:
    if not data:
        return
    existing = await db.scalar(
        select(DailyMetric).where(DailyMetric.user_id == user_id, DailyMetric.date == day)
    )
    fields = {
        "sleep_seconds": data.get("sleep_seconds"),
        "sleep_score": data.get("sleep_score"),
        "resting_hr": data.get("resting_hr"),
        "hrv_overnight": data.get("hrv_overnight"),
        "stress_avg": data.get("stress_avg"),
        "body_battery_high": data.get("body_battery_high"),
        "body_battery_low": data.get("body_battery_low"),
        "steps": data.get("steps"),
        "training_readiness": data.get("training_readiness"),
        "raw": data.get("raw"),
    }
    if existing:
        for key, value in fields.items():
            if value is not None:
                setattr(existing, key, value)
    else:
        db.add(DailyMetric(user_id=user_id, date=day, **fields))
    result["daily_metrics_upserted"] += 1


async def _enrich_and_score(db: AsyncSession, user: User, result: dict) -> None:
    # Estimate the athlete's max HR from observed data (fallback handled downstream).
    max_hr_user = await db.scalar(
        select(Activity.max_hr).where(Activity.user_id == user.id).order_by(Activity.max_hr.desc())
    )

    # Eager-load weather: async SQLAlchemy forbids the lazy load that
    # `act.weather` would otherwise trigger (raises MissingGreenlet).
    activities = (
        await db.scalars(
            select(Activity)
            .where(Activity.user_id == user.id)
            .options(selectinload(Activity.weather))
            .order_by(Activity.start_time.desc())
        )
    ).all()

    for act in activities:
        weather = await _ensure_weather(db, user, act, result)
        apparent = weather.apparent_temp_c if weather else None

        day_metric = await db.scalar(
            select(DailyMetric).where(
                DailyMetric.user_id == user.id, DailyMetric.date == act.start_time.date()
            )
        )
        score, breakdown = compute_difficulty(
            DifficultyInputs(
                duration_s=act.duration_s,
                distance_m=act.distance_m,
                avg_hr=act.avg_hr,
                max_hr_user=max_hr_user,
                elevation_gain_m=act.elevation_gain_m,
                apparent_temp_c=apparent,
                body_battery_high=day_metric.body_battery_high if day_metric else None,
                sleep_score=day_metric.sleep_score if day_metric else None,
            )
        )
        act.difficulty_score = score
        act.difficulty_breakdown = breakdown

    await db.commit()


async def _ensure_weather(db: AsyncSession, user: User, act: Activity, result: dict) -> Weather | None:
    if act.weather is not None:
        return act.weather
    lat = act.start_lat if act.start_lat is not None else user.home_lat
    lon = act.start_lon if act.start_lon is not None else user.home_lon
    if lat is None or lon is None:
        return None
    data = await fetch_weather_at(lat, lon, act.start_time)
    if not data:
        return None
    weather = Weather(activity_id=act.id, **data)
    db.add(weather)
    act.weather = weather
    result["weather_enriched"] += 1
    return weather


def _date_range(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)
