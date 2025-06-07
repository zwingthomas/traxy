import logging
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import crud, schemas, deps
from typing import List

router = APIRouter(prefix='/api/trackers', tags=['trackers'])

# grab a logger for this module
logger = logging.getLogger("app.routers.trackers")


@router.get('', response_model=List[schemas.TrackerOut])
def list_trackers(
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user)
):
    logger.info("list_trackers called by user_id=%s", current.id)
    try:
        trackers = crud.get_trackers_for_user(db, current.id,
                                              ['private','friends','public'],
                                              current)
        out = []
        for t in trackers:
            t_dict = schemas.TrackerOut.from_orm(t).dict()
            t_dict['aggregate'] = crud.get_daily_aggregates(db, t.id)
            out.append(t_dict)
        logger.info("list_trackers returning %d items for user_id=%s", len(out), current.id)
        return out

    except Exception as e:
        logger.exception("Error in list_trackers for user_id=%s: %s", current.id, e)
        raise HTTPException(500, "Internal server error")


@router.post('', response_model=schemas.TrackerOut)
def create_tracker(
    t: schemas.TrackerCreate,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user)
):
    logger.info("create_tracker called by user_id=%s payload=%s", current.id, t.dict())
    try:
        new = crud.create_tracker(db, current.id, t)
        logger.info("create_tracker succeeded id=%s for user_id=%s", new.id, current.id)
        return new

    except Exception as e:
        logger.exception("Error in create_tracker for user_id=%s: %s", current.id, e)
        raise HTTPException(500, "Internal server error")

@router.put("/reorder", status_code=204)
def reorder_trackers(
    payload: schemas.TrackerReorder,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user),
):
    crud.reorder_trackers(db, current.id, payload.ordered_ids)
    return Response(status_code=204)

@router.put('/{tracker_id}', response_model=schemas.TrackerOut)
def update_tracker(
    tracker_id: int,
    t: schemas.TrackerCreate,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user)
):
    logger.info("update_tracker called by user_id=%s tracker_id=%s payload=%s",
                current.id, tracker_id, t.dict())
    try:
        updated = crud.update_tracker(db, current.id, tracker_id, t)
        logger.info("update_tracker succeeded id=%s for user_id=%s", updated.id, current.id)
        return updated

    except HTTPException:
        # re‐raise known 404
        logger.warning("update_tracker not found or unauthorized: user_id=%s tracker_id=%s",
                       current.id, tracker_id)
        raise
    except Exception as e:
        logger.exception("Error in update_tracker for user_id=%s tracker_id=%s: %s",
                         current.id, tracker_id, e)
        raise HTTPException(500, "Internal server error")


@router.delete('/{tracker_id}', status_code=204)
def delete_tracker(
    tracker_id: int,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user)
):
    logger.info("delete_tracker called by user_id=%s tracker_id=%s", current.id, tracker_id)
    try:
        crud.delete_tracker(db, current.id, tracker_id)
        logger.info("delete_tracker succeeded for user_id=%s tracker_id=%s", current.id, tracker_id)
    except HTTPException:
        logger.warning("delete_tracker not found or unauthorized: user_id=%s tracker_id=%s",
                       current.id, tracker_id)
        raise
    except Exception as e:
        logger.exception("Error in delete_tracker for user_id=%s tracker_id=%s: %s",
                         current.id, tracker_id, e)
        raise HTTPException(500, "Internal server error")