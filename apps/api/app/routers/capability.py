from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.dependencies import get_current_user
from ..db import get_db
from ..domain.projection import riegel_predict
from ..domain.zones import derive_zones
from ..models import CapabilitySnapshot, User
from ..schemas import CapabilityCreate, CapabilityOut


router = APIRouter(prefix="/capability", tags=["capability"])


def _projection(comfortable_distance_m: int, comfortable_time_sec: int) -> dict:
    # Predict key distances
    predictions = {}
    for d in [5000, 10000, 21097, 42195]:
        predictions[str(d)] = riegel_predict(comfortable_time_sec, comfortable_distance_m, d)
    zones = derive_zones(predictions["10000"])
    return {"predictions": predictions, "zones": zones}


@router.post("", response_model=CapabilityOut)
def create_capability(
    payload: CapabilityCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    proj = _projection(payload.comfortable_distance_m, payload.comfortable_time_sec)
    snap = CapabilitySnapshot(
        user_id=user.id,
        date=payload.date,
        comfortable_distance_m=payload.comfortable_distance_m,
        comfortable_time_sec=payload.comfortable_time_sec,
        projection=proj,
    )
    db.add(snap)
    db.commit()
    db.refresh(snap)
    return CapabilityOut(
        id=snap.id,
        date=snap.date,
        comfortable_distance_m=snap.comfortable_distance_m,
        comfortable_time_sec=snap.comfortable_time_sec,
        projection=snap.projection,
    )


@router.get("/latest", response_model=CapabilityOut)
def get_latest_capability(
    user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    stmt = (
        select(CapabilitySnapshot)
        .where(CapabilitySnapshot.user_id == user.id)
        .order_by(CapabilitySnapshot.date.desc(), CapabilitySnapshot.created_at.desc())
        .limit(1)
    )
    snap = db.scalars(stmt).first()
    if not snap:
        raise HTTPException(status_code=404, detail="No capability snapshots")
    return CapabilityOut(
        id=snap.id,
        date=snap.date,
        comfortable_distance_m=snap.comfortable_distance_m,
        comfortable_time_sec=snap.comfortable_time_sec,
        projection=snap.projection,
    )

