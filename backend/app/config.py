"""Application configuration loaded from environment variables."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Core ---
    app_name: str = "Half-Marathon Tracker"
    environment: str = "production"
    api_prefix: str = "/api"

    # --- Database ---
    # e.g. postgresql+asyncpg://user:pass@db:5432/tracker
    database_url: str = "postgresql+asyncpg://tracker:tracker@db:5432/tracker"

    # --- Security ---
    # openssl rand -hex 32
    jwt_secret: str = "CHANGE_ME_dev_only_secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 1 day
    # Fernet key (urlsafe base64, 32 bytes) used to encrypt integration credentials at rest.
    # Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
    encryption_key: str = ""

    # Lock registration after the first user is created (single-athlete deployments).
    allow_registration: bool = True

    # --- Strava (optional secondary source) ---
    strava_client_id: str = ""
    strava_client_secret: str = ""
    # Public URL of this app used for the OAuth callback, e.g. https://tracker.example.com
    public_base_url: str = "http://localhost:8000"

    # --- Weather (Open-Meteo, keyless) ---
    open_meteo_archive_url: str = "https://archive-api.open-meteo.com/v1/archive"
    open_meteo_forecast_url: str = "https://api.open-meteo.com/v1/forecast"

    # --- LLM (pluggable) ---
    llm_provider: str = "none"  # none | anthropic | openai | ollama
    llm_model: str = "claude-opus-4-8"
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    ollama_base_url: str = "http://ollama:11434"

    # --- Sync scheduling ---
    sync_hour_utc: int = 3  # nightly full sync
    forecast_hour_utc: int = 5  # morning forecast refresh
    activity_backfill_days: int = 120

    @property
    def cors_origins(self) -> list[str]:
        # Single-origin deployment (nginx serves SPA + proxies /api), so CORS is only
        # needed for local dev against the Vite dev server.
        return ["http://localhost:5173", self.public_base_url]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
