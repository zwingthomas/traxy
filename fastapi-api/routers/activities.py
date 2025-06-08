import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import crud, schemas, deps
from datetime import datetime, timezone, date, timedelta
from typing import Optional
import pytz

from models import Activity

router = APIRouter(prefix='/api/activities', tags=['activities'])
logger = logging.getLogger("app.routers.activities")


@router.post("", status_code=201)
def record_activity(
    a: schemas.ActivityCreate,
    db: Session = Depends(deps.get_db),
    current_user = Depends(deps.get_current_user),
):
    logger.info(
        "record_activity called by user_id=%s for tracker_id=%s "
        "value=%s date=%s",
        current_user.id, a.tracker_id, a.value, a.day
    )

    # Get the tracker to ensure the tracker exists for this activity
    tracker = crud.get_tracker(db, a.tracker_id)
    if not tracker or tracker.user_id != current_user.id:
        logger.warning("Tracker not found or unauthorized")
        raise HTTPException(status_code=404, detail="Tracker not found")

    # convert the LocalDate to a start-of-day UTC timestamp
    ts = datetime.combine(a.day, datetime.min.time(), tzinfo=timezone.utc)

    tz_str = current_user.timezone or "UTC"

    # Convert the user's timezone string into a pytz timezone
    try:
        tz = pytz.timezone(tz_str)
    except pytz.UnknownTimeZoneError:
        print("Error converting to proper timezone.")
        tz = pytz.UTC

    # Get the boundaries of allowed updates
    now_local  = datetime.now(tz)
    today_loc  = now_local.date()
    min_allowed = today_loc - timedelta(days=2)

    # Default to today if no day was passed
    day = a.day or today_loc

    # Enforce a rule for "only update last three days"
    if not (min_allowed <= day <= today_loc):
        raise HTTPException(
            status_code=400,
            detail="`day` must be today or within the last 2 days in your timezone"
        )

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