"""Garmin Connect integration via the unofficial ``garminconnect`` library.

Credentials are stored encrypted (see :mod:`app.core.crypto`). On first login we
authenticate with username/password; the library's OAuth tokens are then cached
(encrypted) so subsequent syncs avoid re-entering the password and reduce login
churn. All Garmin calls are synchronous, so callers should run this in a thread.

The whole surface is intentionally isolated here: if Garmin changes their auth
flow and the library breaks, only this module is affected.
"""
from __future__ import annotations

import logging
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.core.crypto import decrypt_json, encrypt_json

logger = logging.getLogger(__name__)


class GarminAuthError(RuntimeError):
    pass


class GarminClient:
    """Thin wrapper around ``garminconnect.Garmin``.

    Use :meth:`from_payload` to build one from a decrypted credential blob; the
    (possibly refreshed) token payload is available via :meth:`export_payload`
    so callers can persist it back encrypted.
    """

    def __init__(self, api: Any, payload: dict[str, Any]):
        self._api = api
        self._payload = payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "GarminClient":
        try:
            from garminconnect import Garmin
        except ImportError as exc:  # pragma: no cover
            raise GarminAuthError("garminconnect is not installed") from exc

        tokens = payload.get("tokens")
        api: Any
        if tokens:
            # Restore a previous session from cached tokens.
            with tempfile.TemporaryDirectory() as tmp:
                _write_tokenstore(tmp, tokens)
                api = Garmin()
                try:
                    api.login(tmp)
                except Exception:  # noqa: BLE001 - token expired/invalid, fall back to password
                    api = None  # type: ignore[assignment]
            if api is not None:
                return cls(api, payload)

        # Fresh username/password login.
        username = payload.get("username")
        password = payload.get("password")
        if not username or not password:
            raise GarminAuthError("Garmin credentials are missing; please reconnect.")
        api = Garmin(email=username, password=password)
        try:
            api.login()
        except Exception as exc:  # noqa: BLE001
            raise GarminAuthError(f"Garmin login failed: {exc}") from exc

        # Cache the token store so we don't need the password next time.
        with tempfile.TemporaryDirectory() as tmp:
            try:
                api.garth.dump(tmp)
                payload = {**payload, "tokens": _read_tokenstore(tmp)}
            except Exception:  # noqa: BLE001 - non-fatal; we can log in with password next time
                logger.warning("Could not cache Garmin tokens; will re-use password next sync")
        return cls(api, payload)

    def export_payload(self) -> dict[str, Any]:
        return self._payload

    # --- Data fetchers -------------------------------------------------

    def get_activities(self, start: int = 0, limit: int = 50) -> list[dict]:
        return self._api.get_activities(start, limit) or []

    def get_activities_since(self, since: date, cap: int = 300) -> list[dict]:
        """Page through recent activities until we pass ``since``."""
        out: list[dict] = []
        start = 0
        page = 30
        while start < cap:
            batch = self.get_activities(start, page)
            if not batch:
                break
            out.extend(batch)
            last = batch[-1].get("startTimeLocal") or batch[-1].get("startTimeGMT")
            if last and _parse_dt(last).date() < since:
                break
            start += page
        return out

    def get_daily_wellness(self, day: date) -> dict:
        """Aggregate the wellness metrics we care about for a single day."""
        iso = day.isoformat()
        out: dict[str, Any] = {"date": iso}

        def safe(fn, *args):
            try:
                return fn(*args)
            except Exception:  # noqa: BLE001 - individual endpoints can be flaky
                return None

        # get_stats (the daily user summary) is the reliable one-shot source for
        # steps, resting HR, stress, sleep duration and Body Battery — confirmed
        # against a Forerunner 245. Sleep score and HRV need their own endpoints
        # and may be absent on some devices; they're best-effort extras.
        stats = safe(self._api.get_stats, iso) or {}
        sleep = safe(self._api.get_sleep_data, iso) or {}
        hrv = safe(getattr(self._api, "get_hrv_data", None), iso) or {}
        readiness = safe(getattr(self._api, "get_training_readiness", None), iso)

        daily_sleep = (sleep or {}).get("dailySleepDTO", {}) if isinstance(sleep, dict) else {}
        out.update(
            {
                "steps": _first(stats, "totalSteps", "steps"),
                "resting_hr": _first(stats, "restingHeartRate"),
                "stress_avg": _first(stats, "averageStressLevel"),
                "sleep_seconds": _first(daily_sleep, "sleepTimeSeconds")
                or _first(stats, "sleepingSeconds"),
                "sleep_score": _sleep_score(sleep),
                "hrv_overnight": _hrv_value(hrv),
                "body_battery_high": _first(stats, "bodyBatteryHighestValue"),
                "body_battery_low": _first(stats, "bodyBatteryLowestValue"),
                "training_readiness": _readiness_score(readiness),
            }
        )
        return out

    def debug_wellness(self, day: date) -> dict[str, Any]:
        """Return the raw Garmin responses for a day (lists truncated) for mapping."""
        iso = day.isoformat()
        methods = [
            "get_stats", "get_user_summary", "get_sleep_data", "get_hrv_data",
            "get_body_battery", "get_rhr_day", "get_training_readiness", "get_steps_data",
        ]
        result: dict[str, Any] = {"date": iso}
        for name in methods:
            fn = getattr(self._api, name, None)
            if fn is None:
                result[name] = "(method not available in this garminconnect version)"
                continue
            try:
                result[name] = _truncate(fn(iso))
            except Exception as exc:  # noqa: BLE001
                result[name] = f"ERROR: {type(exc).__name__}: {exc}"
        return result


# --- token store helpers (garth writes two files in a directory) ---------


def _write_tokenstore(directory: str, tokens: dict[str, str]) -> None:
    for name, content in tokens.items():
        with open(os.path.join(directory, name), "w", encoding="utf-8") as fh:
            fh.write(content)


def _read_tokenstore(directory: str) -> dict[str, str]:
    tokens: dict[str, str] = {}
    for name in os.listdir(directory):
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                tokens[name] = fh.read()
    return tokens


# --- value extraction helpers -------------------------------------------


def _parse_dt(value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return datetime.now(timezone.utc)


def _rhr_value(rhr: dict) -> float | None:
    try:
        metrics = rhr.get("allMetrics", {}).get("metricsMap", {})
        series = metrics.get("WELLNESS_RESTING_HEART_RATE", [])
        return series[0].get("value") if series else None
    except Exception:  # noqa: BLE001
        return None


def _first(d: Any, *keys: str) -> Any:
    """Return the first non-None value among the given keys of a dict."""
    if not isinstance(d, dict):
        return None
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def _steps_from(steps_data: Any) -> int | None:
    """get_steps_data returns a list of intraday buckets; sum their step counts."""
    if not isinstance(steps_data, list):
        return None
    total = 0
    found = False
    for b in steps_data:
        if isinstance(b, dict) and b.get("steps") is not None:
            total += b["steps"]
            found = True
    return total if found else None


def _sleep_score(sleep_obj: Any) -> float | None:
    """Find a sleep score whether passed the dailySleepDTO or the whole payload."""
    if not isinstance(sleep_obj, dict):
        return None
    candidates = [sleep_obj, sleep_obj.get("dailySleepDTO") or {}]
    for c in candidates:
        scores = (c or {}).get("sleepScores") or {}
        overall = scores.get("overall") or {}
        if overall.get("value") is not None:
            return overall.get("value")
    return None


def _hrv_value(hrv: Any) -> float | None:
    if not isinstance(hrv, dict):
        return None
    summary = hrv.get("hrvSummary") or {}
    return summary.get("lastNightAvg") or summary.get("weeklyAvg")


def _truncate(obj: Any, _depth: int = 0) -> Any:
    """Shrink Garmin responses for the debug endpoint (cap list length & recursion)."""
    if _depth > 4:
        return "…"
    if isinstance(obj, dict):
        return {k: _truncate(v, _depth + 1) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_truncate(x, _depth + 1) for x in obj[:2]] + (["…"] if len(obj) > 2 else [])
    return obj


def _bb_high(bb: list) -> float | None:
    vals = [p[1] for p in bb if isinstance(p, list) and len(p) > 1 and p[1] is not None] if bb else []
    return max(vals) if vals else None


def _bb_low(bb: list) -> float | None:
    vals = [p[1] for p in bb if isinstance(p, list) and len(p) > 1 and p[1] is not None] if bb else []
    return min(vals) if vals else None


def _readiness_score(readiness: Any) -> float | None:
    if isinstance(readiness, list) and readiness:
        readiness = readiness[0]
    if isinstance(readiness, dict):
        return readiness.get("score")
    return None
