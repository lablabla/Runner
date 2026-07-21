from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas.tracker import SyncResult
from app.services.sync import sync_user

router = APIRouter(prefix="/sync", tags=["sync"])


@router.post("", response_model=SyncResult)
async def trigger_sync(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> SyncResult:
    """Run a full sync for the current user (activities, wellness, weather, scoring)."""
    result = await sync_user(db, current)
    return SyncResult(**result)
