"""Weather enrichment via Open-Meteo (free, no API key).

Historical archive is used for past runs; the forecast endpoint for upcoming
planned workouts. Coordinates come from the activity's GPS start point, falling
back to the user's configured home location.
"""
from __future__ import annotations

from datetime import date, datetime

import httpx

from app.config import settings

# WMO weather interpretation codes -> short summary.
_WMO = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Heavy drizzle",
    61: "Light rain",
    63: "Rain",
    65: "Heavy rain",
    66: "Freezing rain",
    71: "Light snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Rain showers",
    82: "Violent showers",
    95: "Thunderstorm",
    96: "Thunderstorm w/ hail",
}

_HOURLY = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "wind_speed_10m",
    "wind_gusts_10m",
    "precipitation",
    "weather_code",
]


def summarise_code(code: int | None) -> str | None:
    return _WMO.get(code) if code is not None else None


def _nearest_hour_index(times: list[str], target: datetime) -> int:
    target_key = target.strftime("%Y-%m-%dT%H:00")
    for i, t in enumerate(times):
        if t.startswith(target_key):
            return i
    # Fall back to the closest by absolute hour difference.
    best_i, best_diff = 0, None
    for i, t in enumerate(times):
        try:
            dt = datetime.fromisoformat(t)
        except ValueError:
            continue
        diff = abs((dt - target.replace(tzinfo=None)).total_seconds())
        if best_diff is None or diff < best_diff:
            best_i, best_diff = i, diff
    return best_i


async def fetch_weather_at(lat: float, lon: float, when: datetime) -> dict | None:
    """Return a weather snapshot dict for a given point and time.

    Chooses the archive or forecast endpoint depending on whether ``when`` is in
    the past. Returns None on failure (weather is best-effort enrichment).
    """
    is_past = when.date() < date.today()
    url = settings.open_meteo_archive_url if is_past else settings.open_meteo_forecast_url
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": ",".join(_HOURLY),
        "timezone": "UTC",
        "start_date": when.strftime("%Y-%m-%d"),
        "end_date": when.strftime("%Y-%m-%d"),
        "wind_speed_unit": "kmh",
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
    except (httpx.HTTPError, ValueError):
        return None

    hourly = data.get("hourly") or {}
    times = hourly.get("time") or []
    if not times:
        return None
    idx = _nearest_hour_index(times, when)

    def val(key: str):
        series = hourly.get(key) or []
        return series[idx] if idx < len(series) else None

    code = val("weather_code")
    return {
        "temp_c": val("temperature_2m"),
        "apparent_temp_c": val("apparent_temperature"),
        "humidity_pct": val("relative_humidity_2m"),
        "wind_speed_kmh": val("wind_speed_10m"),
        "wind_gust_kmh": val("wind_gusts_10m"),
        "precip_mm": val("precipitation"),
        "weather_code": int(code) if code is not None else None,
        "summary": summarise_code(int(code) if code is not None else None),
    }
