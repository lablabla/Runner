"""Seed the database with a demo user and synthetic training data.

Lets you explore the dashboards without connecting a real Garmin account.

    docker compose exec backend python scripts/seed_demo.py

Creates (or reuses) demo@example.com / demopass123 with ~10 weeks of runs,
daily wellness metrics, weather and computed difficulty scores.
"""
from __future__ import annotations

import asyncio
import math
import os
import random
import sys
from datetime import date, datetime, timedelta, timezone

# Make the backend package importable when run as `python scripts/seed_demo.py`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select

from app.core.security import hash_password
from app.database import Base, SessionLocal, engine
import app.models  # noqa: F401
from app.models import Activity, DailyMetric, User, Weather
from app.services.difficulty import DifficultyInputs, compute_difficulty

EMAIL = "demo@example.com"
PASSWORD = "demopass123"
WEEKS = 10
MAX_HR = 190


async def _ensure_user(db) -> User:
    user = await db.scalar(select(User).where(User.email == EMAIL))
    if user:
        return user
    user = User(
        email=EMAIL,
        hashed_password=hash_password(PASSWORD),
        display_name="Demo Runner",
        home_lat=51.5072,
        home_lon=-0.1276,
        is_admin=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _weekly_plan(week: int) -> list[tuple[int, str, float]]:
    """(weekday, type, distance_km) — a simple progressive half-marathon block."""
    base_long = 10 + week * 1.1
    return [
        (1, "easy", 6),
        (2, "intervals", 8),
        (4, "tempo", 9),
        (6, "long", round(base_long, 1)),
    ]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        user = await _ensure_user(db)

        # Clear previous demo data so re-runs are idempotent.
        existing = (await db.scalars(select(Activity).where(Activity.user_id == user.id))).all()
        for a in existing:
            await db.delete(a)
        existing_dm = (await db.scalars(select(DailyMetric).where(DailyMetric.user_id == user.id))).all()
        for m in existing_dm:
            await db.delete(m)
        await db.commit()

        start = date.today() - timedelta(weeks=WEEKS)

        # Daily wellness for the whole window.
        metrics_by_date: dict[date, DailyMetric] = {}
        for offset in range((date.today() - start).days + 1):
            day = start + timedelta(days=offset)
            sleep_score = int(max(40, min(95, random.gauss(78, 12))))
            bb = int(max(30, min(100, random.gauss(85, 10))))
            dm = DailyMetric(
                user_id=user.id,
                date=day,
                sleep_seconds=random.randint(6, 8) * 3600 + random.randint(0, 59) * 60,
                sleep_score=sleep_score,
                resting_hr=int(random.gauss(48, 3)),
                hrv_overnight=int(random.gauss(65, 10)),
                stress_avg=int(random.gauss(35, 8)),
                body_battery_high=bb,
                body_battery_low=int(bb - random.randint(30, 60)),
                steps=random.randint(6000, 15000),
                training_readiness=int(max(30, min(99, random.gauss(70, 15)))),
            )
            db.add(dm)
            metrics_by_date[day] = dm

        # Runs.
        aid = 1
        for week in range(WEEKS):
            week_start = start + timedelta(weeks=week)
            for weekday, wtype, dist_km in _weekly_plan(week):
                run_date = week_start + timedelta(days=weekday)
                if run_date > date.today():
                    continue
                start_dt = datetime.combine(run_date, datetime.min.time(), tzinfo=timezone.utc) + timedelta(
                    hours=random.choice([6, 7, 18])
                )
                distance_m = dist_km * 1000
                base_pace = {"easy": 330, "long": 340, "tempo": 285, "intervals": 300}[wtype]
                pace = base_pace + random.randint(-8, 8)
                duration_s = pace * dist_km
                avg_hr = {"easy": 138, "long": 148, "tempo": 168, "intervals": 172}[wtype] + random.randint(-5, 5)
                elev = random.randint(20, 120)
                apparent = 12 + 10 * math.sin(week / 2) + random.uniform(-3, 3)

                dm = metrics_by_date.get(run_date)
                score, breakdown = compute_difficulty(
                    DifficultyInputs(
                        duration_s=duration_s,
                        distance_m=distance_m,
                        avg_hr=avg_hr,
                        max_hr_user=MAX_HR,
                        elevation_gain_m=elev,
                        apparent_temp_c=apparent,
                        body_battery_high=dm.body_battery_high if dm else None,
                        sleep_score=dm.sleep_score if dm else None,
                    )
                )

                activity = Activity(
                    user_id=user.id,
                    source="garmin",
                    source_id=f"demo-{aid}",
                    name=f"{wtype.title()} Run with Runna ✅" if wtype != "easy" else "Easy Run",
                    sport_type="running",
                    start_time=start_dt,
                    distance_m=distance_m,
                    duration_s=duration_s,
                    moving_time_s=duration_s,
                    avg_pace_s_per_km=pace,
                    avg_hr=avg_hr,
                    max_hr=avg_hr + random.randint(8, 20),
                    avg_cadence=random.randint(168, 182),
                    elevation_gain_m=elev,
                    calories=distance_m / 1000 * 62,
                    aerobic_te=round(random.uniform(2.0, 4.5), 1),
                    training_load=round(duration_s / 60 * (avg_hr / 100), 0),
                    start_lat=51.5072,
                    start_lon=-0.1276,
                    is_runna=wtype != "easy",
                    difficulty_score=score,
                    difficulty_breakdown=breakdown,
                )
                db.add(activity)
                await db.flush()
                db.add(
                    Weather(
                        activity_id=activity.id,
                        temp_c=round(apparent - 2, 1),
                        apparent_temp_c=round(apparent, 1),
                        humidity_pct=random.randint(50, 90),
                        wind_speed_kmh=random.randint(5, 25),
                        precip_mm=round(random.choice([0, 0, 0, 1.2, 3.5]), 1),
                        weather_code=random.choice([0, 1, 2, 3, 61]),
                        summary=random.choice(["Clear", "Partly cloudy", "Overcast", "Light rain"]),
                    )
                )
                aid += 1

        await db.commit()
    print(f"Seeded demo data. Log in with {EMAIL} / {PASSWORD}")


if __name__ == "__main__":
    asyncio.run(seed())
