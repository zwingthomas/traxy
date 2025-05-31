import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import crud, schemas, deps
from datetime import datetime

router = APIRouter(prefix='/api/activities', tags=['activities'])
logger = logging.getLogger("app.routers.activities")


@router.post("", status_code=201)
def record_activity(
    a: schemas.ActivityCreate,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user),
):
    logger.info(
        "record_activity called by user_id=%s for tracker_id=%s with value=%s",
        current.id,
        a.tracker_id,
        a.value,
    )

    tracker = crud.get_tracker(db, a.tracker_id)
    if not tracker or tracker.user_id != current.id:
        logger.warning(
            "record_activity unauthorized or not found: user_id=%s tracker_id=%s",
            current.id,
            a.tracker_id,
        )
        raise HTTPException(status_code=404, detail="Tracker not found")

    try:
        activity = crud.create_activity(db, a)
        logger.info(
            "record_activity succeeded: activity_id=%s tracker_id=%s user_id=%s",
            activity.id,
            a.tracker_id,
            current.id,
        )
        return activity

    except Exception as e:
        logger.exception(
            "unexpected error in record_activity for user_id=%s tracker_id=%s: %s",
            current.id,
            a.tracker_id,
            e,
        )
        raise HTTPException(status_code=500, detail="Internal server error")
    
@router.delete("/reset", status_code=204)
def reset_today(
    tracker_id: int = Query(..., description="ID of the tracker"),
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user),
):
    tracker = crud.get_tracker(db, tracker_id)
    if not tracker or tracker.user_id != current.id:
        raise HTTPException(404, "Tracker not found")

    # delete all activities for today
    crud.delete_activities_for_day(db, tracker_id, datetime.today())