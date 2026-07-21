from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class WeatherOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    temp_c: float | None = None
    apparent_temp_c: float | None = None
    humidity_pct: float | None = None
    wind_speed_kmh: float | None = None
    precip_mm: float | None = None
    summary: str | None = None


class ActivityOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    name: str | None
    sport_type: str
    start_time: datetime
    distance_m: float | None
    duration_s: float | None
    avg_pace_s_per_km: float | None
    avg_hr: float | None
    max_hr: float | None
    elevation_gain_m: float | None
    aerobic_te: float | None
    is_runna: bool
    difficulty_score: float | None
    difficulty_breakdown: dict | None
    weather: WeatherOut | None = None


class DailyMetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    date: date
    sleep_seconds: float | None
    sleep_score: float | None
    resting_hr: float | None
    hrv_overnight: float | None
    stress_avg: float | None
    body_battery_high: float | None
    body_battery_low: float | None
    steps: int | None
    training_readiness: float | None


class PlannedWorkoutIn(BaseModel):
    date: date
    workout_type: str = "run"
    title: str | None = None
    description: str | None = None
    distance_target_m: float | None = None
    duration_target_s: float | None = None


class PlannedWorkoutOut(PlannedWorkoutIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    source: str
    completed_activity_id: int | None = None


class IntegrationStatusOut(BaseModel):
    provider: str
    status: str
    status_detail: str | None = None
    last_sync_at: datetime | None = None


class GarminConnectRequest(BaseModel):
    username: str
    password: str


class LLMConfigRequest(BaseModel):
    provider: str  # none | anthropic | openai | ollama
    api_key: str | None = None
    model: str | None = None


class InsightOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    kind: str
    period: str | None
    content: str
    model: str | None
    created_at: datetime


class SyncResult(BaseModel):
    activities_added: int = 0
    activities_updated: int = 0
    daily_metrics_upserted: int = 0
    weather_enriched: int = 0
    errors: list[str] = []
