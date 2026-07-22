"""Regression test for the async sync/enrich path.

Guards against the MissingGreenlet error that occurred when `_enrich_and_score`
accessed the lazily-loaded `Activity.weather` relationship in async context.
"""
from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 - register tables
import app.services.sync as sync
from app.database import Base
from app.models import Activity, User


@pytest.fixture
async def session():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    maker = async_sessionmaker(engine, expire_on_commit=False)
    async with maker() as s:
        yield s
    await engine.dispose()


async def _fake_weather(lat, lon, when):
    return {
        "temp_c": 15,
        "apparent_temp_c": 18,
        "humidity_pct": 60,
        "wind_speed_kmh": 10,
        "wind_gust_kmh": 15,
        "precip_mm": 0,
        "weather_code": 1,
        "summary": "Mainly clear",
    }


async def test_enrich_and_score_no_greenlet_error(session, monkeypatch):
    monkeypatch.setattr(sync, "fetch_weather_at", _fake_weather)

    user = User(email="e@x.com", hashed_password="h", home_lat=51.5, home_lon=-0.12)
    session.add(user)
    await session.commit()
    await session.refresh(user)

    session.add(
        Activity(
            user_id=user.id, source="garmin", source_id="1",
            start_time=datetime(2026, 7, 1, 7, tzinfo=timezone.utc),
            distance_m=10000, duration_s=3000, avg_hr=150, max_hr=175,
            elevation_gain_m=80, start_lat=51.5, start_lon=-0.12,
        )
    )
    # No GPS -> exercises the home-location weather fallback.
    session.add(
        Activity(
            user_id=user.id, source="garmin", source_id="2",
            start_time=datetime(2026, 7, 3, 7, tzinfo=timezone.utc),
            distance_m=8000, duration_s=2400, avg_hr=140, max_hr=170,
            elevation_gain_m=40,
        )
    )
    await session.commit()

    result = {"weather_enriched": 0}
    await sync._enrich_and_score(session, user, result)  # must not raise MissingGreenlet

    acts = (await session.scalars(select(Activity).options(selectinload(Activity.weather)))).all()
    assert len(acts) == 2
    assert all(a.difficulty_score is not None for a in acts)
    assert all(a.weather is not None for a in acts)
    assert result["weather_enriched"] == 2
