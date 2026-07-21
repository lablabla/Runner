"""Background scheduler process.

Runs in its own container (see docker-compose) so API restarts don't interrupt
jobs and only one instance ever schedules work. Performs a nightly full sync for
every user and refreshes forecasts in the morning.
"""
from __future__ import annotations

import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select

from app.config import settings
from app.database import Base, SessionLocal, engine
import app.models  # noqa: F401  (register tables)
from app.models import User
from app.services.sync import sync_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("worker")


async def nightly_sync() -> None:
    logger.info("Starting nightly sync for all users")
    async with SessionLocal() as db:
        users = (await db.scalars(select(User).where(User.is_active.is_(True)))).all()
        for user in users:
            try:
                result = await sync_user(db, user)
                logger.info("Synced user %s: %s", user.id, result)
            except Exception:  # noqa: BLE001
                logger.exception("Sync failed for user %s", user.id)


async def _init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def main() -> None:
    await _init_db()
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        nightly_sync,
        CronTrigger(hour=settings.sync_hour_utc, minute=0),
        id="nightly_sync",
        replace_existing=True,
    )
    # Morning refresh reuses the same full sync (weather forecasts included).
    scheduler.add_job(
        nightly_sync,
        CronTrigger(hour=settings.forecast_hour_utc, minute=0),
        id="morning_refresh",
        replace_existing=True,
    )
    scheduler.start()
    logger.info(
        "Scheduler started (nightly=%02d:00 UTC, morning=%02d:00 UTC)",
        settings.sync_hour_utc,
        settings.forecast_hour_utc,
    )
    # Keep the event loop alive forever.
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())
