from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.crypto import decrypt_json, encrypt_json
from app.database import get_db
from app.models import IntegrationCredential, User
from app.schemas.tracker import GarminConnectRequest, IntegrationStatusOut
from app.services import strava as strava_svc
from app.services.garmin import GarminAuthError, GarminClient

router = APIRouter(prefix="/integrations", tags=["integrations"])


async def _upsert_cred(
    db: AsyncSession, user_id: int, provider: str, payload: dict, status: str = "connected"
) -> IntegrationCredential:
    cred = await db.scalar(
        select(IntegrationCredential).where(
            IntegrationCredential.user_id == user_id, IntegrationCredential.provider == provider
        )
    )
    token = encrypt_json(payload)
    if cred:
        cred.encrypted_payload = token
        cred.status = status
        cred.status_detail = None
    else:
        cred = IntegrationCredential(
            user_id=user_id, provider=provider, encrypted_payload=token, status=status
        )
        db.add(cred)
    await db.commit()
    await db.refresh(cred)
    return cred


@router.get("", response_model=list[IntegrationStatusOut])
async def list_integrations(
    current: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)
) -> list[IntegrationStatusOut]:
    rows = (
        await db.scalars(
            select(IntegrationCredential).where(IntegrationCredential.user_id == current.id)
        )
    ).all()
    return [
        IntegrationStatusOut(
            provider=c.provider, status=c.status, status_detail=c.status_detail, last_sync_at=c.last_sync_at
        )
        for c in rows
    ]


@router.post("/garmin", response_model=IntegrationStatusOut)
async def connect_garmin(
    body: GarminConnectRequest,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IntegrationStatusOut:
    """Store Garmin credentials (encrypted) and verify them by logging in once."""
    import asyncio

    payload = {"username": body.username, "password": body.password}
    try:
        client = await asyncio.to_thread(GarminClient.from_payload, payload)
        payload = client.export_payload()  # includes cached tokens on success
    except GarminAuthError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    cred = await _upsert_cred(db, current.id, "garmin", payload)
    return IntegrationStatusOut(provider="garmin", status=cred.status)


@router.get("/garmin/debug")
async def garmin_debug(
    date: str | None = None,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Diagnostic: return the raw Garmin wellness responses for a day.

    Helps map fields when a metric (sleep/HRV/steps) isn't populating. Defaults to
    yesterday. Requires a connected Garmin account.
    """
    import asyncio
    from datetime import date as date_cls, timedelta

    cred = await db.scalar(
        select(IntegrationCredential).where(
            IntegrationCredential.user_id == current.id, IntegrationCredential.provider == "garmin"
        )
    )
    if not cred:
        raise HTTPException(status_code=400, detail="Garmin is not connected")
    day = date_cls.fromisoformat(date) if date else date_cls.today() - timedelta(days=1)
    try:
        payload = decrypt_json(cred.encrypted_payload)
        client = await asyncio.to_thread(GarminClient.from_payload, payload)
        return await asyncio.to_thread(client.debug_wellness, day)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Garmin debug failed: {exc}") from exc


@router.delete("/{provider}", status_code=204, response_class=Response)
async def disconnect(
    provider: str,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cred = await db.scalar(
        select(IntegrationCredential).where(
            IntegrationCredential.user_id == current.id, IntegrationCredential.provider == provider
        )
    )
    if cred:
        await db.delete(cred)
        await db.commit()


# --- Strava OAuth ---------------------------------------------------------

# Short-lived in-memory state store keyed by random token -> user id.
_oauth_state: dict[str, int] = {}


@router.get("/strava/authorize")
async def strava_authorize(current: User = Depends(get_current_user)) -> dict:
    if not settings.strava_client_id:
        raise HTTPException(status_code=400, detail="Strava is not configured on the server")
    state = secrets.token_urlsafe(24)
    _oauth_state[state] = current.id
    return {"authorize_url": strava_svc.authorize_url(state)}


@router.get("/strava/callback")
async def strava_callback(
    code: str, state: str, db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    user_id = _oauth_state.pop(state, None)
    if user_id is None:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    try:
        payload = await strava_svc.exchange_code(code)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=f"Strava authorization failed: {exc}") from exc
    await _upsert_cred(db, user_id, "strava", payload)
    return RedirectResponse(url="/settings?strava=connected")
