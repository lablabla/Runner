from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models import Activity, PlannedWorkout, User
from app.schemas.tracker import PlannedWorkoutIn, PlannedWorkoutOut
from app.services.runna import parse_plan_pdf

router = APIRouter(prefix="/plan", tags=["plan"])


@router.get("", response_model=list[PlannedWorkoutOut])
async def list_plan(
    start: date | None = None,
    end: date | None = None,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlannedWorkout]:
    stmt = select(PlannedWorkout).where(PlannedWorkout.user_id == current.id)
    if start:
        stmt = stmt.where(PlannedWorkout.date >= start)
    if end:
        stmt = stmt.where(PlannedWorkout.date <= end)
    stmt = stmt.order_by(PlannedWorkout.date)
    return list((await db.scalars(stmt)).all())


@router.post("", response_model=PlannedWorkoutOut, status_code=201)
async def create_workout(
    body: PlannedWorkoutIn,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlannedWorkout:
    workout = PlannedWorkout(user_id=current.id, source="manual", **body.model_dump())
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


@router.put("/{workout_id}", response_model=PlannedWorkoutOut)
async def update_workout(
    workout_id: int,
    body: PlannedWorkoutIn,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PlannedWorkout:
    workout = await db.scalar(
        select(PlannedWorkout).where(
            PlannedWorkout.id == workout_id, PlannedWorkout.user_id == current.id
        )
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Planned workout not found")
    for key, value in body.model_dump().items():
        setattr(workout, key, value)
    await db.commit()
    await db.refresh(workout)
    return workout


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: int,
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    workout = await db.scalar(
        select(PlannedWorkout).where(
            PlannedWorkout.id == workout_id, PlannedWorkout.user_id == current.id
        )
    )
    if workout:
        await db.delete(workout)
        await db.commit()


@router.post("/import-pdf", response_model=list[PlannedWorkoutOut])
async def import_plan_pdf(
    file: UploadFile = File(...),
    current: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[PlannedWorkout]:
    """Parse a Runna plan PDF and add the extracted workouts (best-effort)."""
    if file.content_type not in ("application/pdf", "application/octet-stream"):
        raise HTTPException(status_code=400, detail="Please upload a PDF file")
    data = await file.read()
    parsed = parse_plan_pdf(data)
    if not parsed:
        raise HTTPException(
            status_code=422,
            detail="Could not extract any workouts from the PDF. Add them manually instead.",
        )
    created: list[PlannedWorkout] = []
    for item in parsed:
        workout = PlannedWorkout(
            user_id=current.id,
            source="pdf",
            date=date.fromisoformat(item["date"]),
            workout_type=item["workout_type"],
            title=item.get("title"),
            description=item.get("description"),
            distance_target_m=item.get("distance_target_m"),
            duration_target_s=item.get("duration_target_s"),
        )
        db.add(workout)
        created.append(workout)
    await db.commit()
    for w in created:
        await db.refresh(w)
    return created
