from __future__ import annotations

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..db import get_db
from ..domain.planner import PlanSpec, generate_plan
from ..models import CapabilitySnapshot, Goal, Plan, User, Workout
from ..schemas import PlanOut, WorkoutOut


router = APIRouter(prefix="/plans", tags=["plans"])


@router.post("/goals/{goal_id}/generate-plan", response_model=PlanOut)
def generate_plan_for_goal(goal_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
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
        raise HTTPException(status_code=400, detail="No capability snapshot")

    # Archive existing active plans for the goal
    db.query(Plan).filter(and_(Plan.goal_id == goal.id, Plan.status == "active")).update({Plan.status: "superseded"})

    start_date = snap.date
    end_date = goal.target_date
    spec = PlanSpec(start_date=start_date, end_date=end_date, running_days_per_week=4, phases={})
    start_weekly_vol = max(snap.comfortable_distance_m * 3.0, 10000)
    workouts_specs = generate_plan(
        goal_distance_m=goal.distance_m, start_weekly_vol=start_weekly_vol, cap_growth=0.10, spec=spec
    )
    plan = Plan(user_id=user.id, goal_id=goal.id, start_date=start_date, end_date=end_date, status="active")
    db.add(plan)
    db.flush()
    # Persist workouts
    for ws in workouts_specs:
        db.add(
            Workout(
                plan_id=plan.id,
                wdate=ws.wdate,
                wtype=ws.wtype,
                target_distance_m=ws.target_distance_m,
                target_duration_sec=ws.target_duration_sec,
                target_zone=ws.target_zone,
                description=ws.description,
                is_key=ws.is_key,
            )
        )
    db.commit()
    db.refresh(plan)
    workouts = db.scalars(select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.wdate.asc())).all()
    return PlanOut(
        id=plan.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        status=plan.status,
        workouts=[
            WorkoutOut(
                id=w.id,
                wdate=w.wdate,
                wtype=w.wtype,
                target_distance_m=w.target_distance_m,
                target_duration_sec=w.target_duration_sec,
                target_zone=w.target_zone,
                description=w.description,
                is_key=w.is_key,
            )
            for w in workouts
        ],
    )


@router.get("/current", response_model=PlanOut)
def get_current_plan(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    plan = db.query(Plan).filter(and_(Plan.user_id == user.id, Plan.status == "active")).order_by(Plan.created_at.desc()).first()
    if not plan:
        raise HTTPException(status_code=404, detail="No active plan")
    workouts = db.scalars(select(Workout).where(Workout.plan_id == plan.id).order_by(Workout.wdate.asc())).all()
    return PlanOut(
        id=plan.id,
        start_date=plan.start_date,
        end_date=plan.end_date,
        status=plan.status,
        workouts=[
            WorkoutOut(
                id=w.id,
                wdate=w.wdate,
                wtype=w.wtype,
                target_distance_m=w.target_distance_m,
                target_duration_sec=w.target_duration_sec,
                target_zone=w.target_zone,
                description=w.description,
                is_key=w.is_key,
            )
            for w in workouts
        ],
    )


@router.get("/{plan_id}/workouts", response_model=list[WorkoutOut])
def list_workouts(
    plan_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    from_date: Optional[date] = Query(default=None, alias="from"),
    to_date: Optional[date] = Query(default=None, alias="to"),
):
    plan = db.get(Plan, plan_id)
    if not plan or plan.user_id != user.id:
        raise HTTPException(status_code=404, detail="Plan not found")
    stmt = select(Workout).where(Workout.plan_id == plan_id)
    if from_date:
        stmt = stmt.where(Workout.wdate >= from_date)
    if to_date:
        stmt = stmt.where(Workout.wdate <= to_date)
    stmt = stmt.order_by(Workout.wdate.asc())
    workouts = db.scalars(stmt).all()
    return [
        WorkoutOut(
            id=w.id,
            wdate=w.wdate,
            wtype=w.wtype,
            target_distance_m=w.target_distance_m,
            target_duration_sec=w.target_duration_sec,
            target_zone=w.target_zone,
            description=w.description,
            is_key=w.is_key,
        )
        for w in workouts
    ]

