from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = (
        UniqueConstraint("user_id", "source", "source_id", name="uq_activity_source"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)

    source: Mapped[str] = mapped_column(String(16))  # garmin | strava | manual
    source_id: Mapped[str] = mapped_column(String(64))

    name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sport_type: Mapped[str] = mapped_column(String(48), default="running")
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    distance_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    moving_time_s: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_pace_s_per_km: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_hr: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_cadence: Mapped[float | None] = mapped_column(Float, nullable=True)
    elevation_gain_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    calories: Mapped[float | None] = mapped_column(Float, nullable=True)
    aerobic_te: Mapped[float | None] = mapped_column(Float, nullable=True)
    anaerobic_te: Mapped[float | None] = mapped_column(Float, nullable=True)
    training_load: Mapped[float | None] = mapped_column(Float, nullable=True)

    start_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    start_lon: Mapped[float | None] = mapped_column(Float, nullable=True)

    is_runna: Mapped[bool] = mapped_column(Boolean, default=False)
    difficulty_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    difficulty_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    raw: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    user = relationship("User", back_populates="activities")
    weather = relationship(
        "Weather", back_populates="activity", uselist=False, cascade="all, delete-orphan"
    )
