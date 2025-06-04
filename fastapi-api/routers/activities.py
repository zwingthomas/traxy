import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import crud, schemas, deps
from datetime import datetime, timezone, date
from typing import Optional

from models import Activity

router = APIRouter(prefix='/api/activities', tags=['activities'])
logger = logging.getLogger("app.routers.activities")


@router.post("", status_code=201)
def record_activity(
    a: schemas.ActivityCreate,
    db: Session = Depends(deps.get_db),
    current = Depends(deps.get_current_user),
):
    logger.info(
        "record_activity called by user_id=%s for tracker_id=%s "
        "value=%s date=%s",
        current.id, a.tracker_id, a.value, a.day
    )

    tracker = crud.get_tracker(db, a.tracker_id)
    if not tracker or tracker.user_id != current.id:
        logger.warning("Tracker not found or unauthorized")
        raise HTTPException(status_code=404, detail="Tracker not found")

    # convert the LocalDate to a start-of-day UTC timestamp
    ts = datetime.combine(a.day, datetime.min.time(), tzinfo=timezone.utc)

    try:
        activity = crud.create_activity(db, a.tracker_id, a.value, ts)
        return activity

    except Exception as e:
        logger.exception("unexpected error in record_activity: %s", e)
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.delete("/reset")
def reset_activity(
    tracker_id: int,
    day: Optional[date] = None,
    db: Session = Depends(deps.get_db),
    current = Depends(deps.get_current_user),
):
    
    if day is None:
        day = date.today() 

    tracker = crud.get_tracker(db, tracker_id)
    if not tracker or tracker.user_id != current.id:
        raise HTTPException(status_code=404, detail="Tracker not found")
    
    crud.delete_activities_for_day(db, tracker_id, day)
    return {"ok": True}