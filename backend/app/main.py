"""FastAPI application entrypoint."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine

# Import models so their tables register on Base before create_all.
import app.models  # noqa: F401
from app.api.routes import (
    activities,
    analysis,
    auth,
    integrations,
    metrics,
    plan,
    sync,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on first boot. For schema evolution, Alembic migrations live in
    # backend/alembic; this create_all is idempotent and safe alongside them.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database ready")
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (auth, integrations, activities, metrics, plan, analysis, sync):
    app.include_router(module.router, prefix=settings.api_prefix)


@app.get(f"{settings.api_prefix}/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "app": settings.app_name}
