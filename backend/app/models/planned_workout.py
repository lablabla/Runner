from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class PlannedWorkout(Base):
    """A scheduled workout from the Runna plan.

    Sourced automatically from Garmin's scheduled workouts where possible, otherwise
    entered manually or parsed from an uploaded Runna PDF.
    """

    __tablename__ = "planned_workouts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)

    workout_type: Mapped[str] = mapped_column(String(48), default="run")  # easy | tempo | intervals | long | rest ...
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    distance_target_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    duration_target_s: Mapped[float | None] = mapped_column(Float, nullable=True)

    source: Mapped[str] = mapped_column(String(16), default="manual")  # garmin | manual | pdf
    completed_activity_id: Mapped[int | None] = mapped_column(
        ForeignKey("activities.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)
