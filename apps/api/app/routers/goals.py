from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..db import get_db
from ..domain.feasibility import assess_feasibility
from ..models import CapabilitySnapshot, Goal, User
from ..schemas import FeasibilityResult, GoalCreate, GoalOut


router = APIRouter(prefix="/goals", tags=["goals"])


@router.post("", response_model=GoalOut)
def create_goal(payload: GoalCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = Goal(
        user_id=user.id,
        distance_m=payload.distance_m,
        target_time_sec=payload.target_time_sec,
        target_date=payload.target_date,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return GoalOut(id=goal.id, distance_m=goal.distance_m, target_time_sec=goal.target_time_sec, target_date=goal.target_date)


@router.post("/{goal_id}/feasibility", response_model=FeasibilityResult)
def goal_feasibility(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    goal = db.get(Goal, goal_id)
    if not goal or goal.user_id != user.id:
        raise HTTPException(status_code=404, detail="Goal not found")
    snap = (
        db.query(CapabilitySnapshot)
        .filter(CapabilitySnapshot.user_id == user.id)
        .order_by(CapabilitySnapshot.date.desc(), CapabilitySnapshot.created_at.desc())
        .first()
    )
    if not snap:
        raise HTTPException(status_code=400, detail="No capability snapshot; create one first")
    today = date.today()
    res = assess_feasibility(
        today=today,
        target_date=goal.target_date,
        goal_distance_m=goal.distance_m,
        target_time_sec=goal.target_time_sec,
        comfortable_distance_m=snap.comfortable_distance_m,
        comfortable_time_sec=snap.comfortable_time_sec,
    )
    return FeasibilityResult(feasible=res.feasible, reasons=res.reasons, tradeoffs=res.tradeoffs)

