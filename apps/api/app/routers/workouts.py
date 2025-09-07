from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..db import get_db
from ..models import SessionLog, User, Workout
from ..schemas import LogCreate, WorkoutOut


router = APIRouter(prefix="/workouts", tags=["workouts"])


@router.get("/{workout_id}", response_model=WorkoutOut)
def get_workout(workout_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    w = db.get(Workout, workout_id)
    if not w:
        raise HTTPException(status_code=404, detail="Workout not found")
    plan_user_id = w.plan.user_id  # requires relationship load
    if plan_user_id != user.id:
        raise HTTPException(status_code=404, detail="Workout not found")
    return WorkoutOut(
        id=w.id,
        wdate=w.wdate,
        wtype=w.wtype,
        target_distance_m=w.target_distance_m,
        target_duration_sec=w.target_duration_sec,
        target_zone=w.target_zone,
        description=w.description,
        is_key=w.is_key,
    )


@router.post("/{workout_id}/log")
def log_workout(
    workout_id: str, payload: LogCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    w = db.get(Workout, workout_id)
    if not w or w.plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Workout not found")
    log = SessionLog(
        workout_id=w.id,
        actual_distance_m=payload.actual_distance_m,
        actual_time_sec=payload.actual_time_sec,
        rpe=payload.rpe,
        notes=payload.notes,
    )
    db.add(log)
    db.commit()
    return {"ok": True}

