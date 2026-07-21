from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationCredential(Base):
    """Encrypted credentials / session tokens for an external provider.

    ``encrypted_payload`` is a Fernet token wrapping a JSON blob. Its shape depends
    on the provider:
      - garmin: {"username": ..., "password": ..., "tokens": {...garth oauth...}}
      - strava: {"access_token": ..., "refresh_token": ..., "expires_at": ...,
                 "athlete_id": ...}
      - llm:    {"provider": ..., "api_key": ..., "model": ...}
    """

    __tablename__ = "integration_credentials"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_user_provider"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[str] = mapped_column(String(32))  # garmin | strava | llm
    encrypted_payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="connected")  # connected | error | disconnected
    status_detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    user = relationship("User", back_populates="credentials")
