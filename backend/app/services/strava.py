"""Strava integration (official OAuth2 API) — optional secondary source.

Personal single-user use. We store the athlete's refreshable tokens encrypted and
refresh them on demand. Per Strava's API terms this data is for the user's own
viewing only (no redistribution / model training).
"""
from __future__ import annotations

import time
from typing import Any

import httpx

from app.config import settings

AUTH_URL = "https://www.strava.com/oauth/authorize"
TOKEN_URL = "https://www.strava.com/oauth/token"
API_BASE = "https://www.strava.com/api/v3"
SCOPE = "read,activity:read_all"


def authorize_url(state: str) -> str:
    redirect = f"{settings.public_base_url}{settings.api_prefix}/integrations/strava/callback"
    params = {
        "client_id": settings.strava_client_id,
        "response_type": "code",
        "redirect_uri": redirect,
        "approval_prompt": "auto",
        "scope": SCOPE,
        "state": state,
    }
    query = "&".join(f"{k}={httpx.QueryParams({k: v})[k]}" for k, v in params.items())
    return f"{AUTH_URL}?{query}"


async def exchange_code(code: str) -> dict[str, Any]:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "code": code,
                "grant_type": "authorization_code",
            },
        )
        resp.raise_for_status()
        data = resp.json()
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data["expires_at"],
        "athlete_id": data.get("athlete", {}).get("id"),
    }


async def _ensure_token(payload: dict[str, Any]) -> dict[str, Any]:
    """Refresh the access token if it is within 5 minutes of expiry."""
    if payload.get("expires_at", 0) - time.time() > 300:
        return payload
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(
            TOKEN_URL,
            data={
                "client_id": settings.strava_client_id,
                "client_secret": settings.strava_client_secret,
                "grant_type": "refresh_token",
                "refresh_token": payload["refresh_token"],
            },
        )
        resp.raise_for_status()
        data = resp.json()
    payload = {
        **payload,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_at": data["expires_at"],
    }
    return payload


async def fetch_activities(payload: dict[str, Any], after_epoch: int, per_page: int = 100) -> tuple[list[dict], dict]:
    """Return (activities, possibly-refreshed payload)."""
    payload = await _ensure_token(payload)
    headers = {"Authorization": f"Bearer {payload['access_token']}"}
    out: list[dict] = []
    page = 1
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            resp = await client.get(
                f"{API_BASE}/athlete/activities",
                headers=headers,
                params={"after": after_epoch, "per_page": per_page, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            out.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
    return out, payload
