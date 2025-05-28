from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, deps

router = APIRouter(prefix='/api/activities', tags=['activities'])

@router.post('', status_code=201)
def record_activity(a: schemas.ActivityCreate,
                    db: Session = Depends(deps.get_db),
                    current=Depends(deps.get_current_user)):
    tracker = crud.get_tracker(db, a.tracker_id)
    if not tracker or tracker.user_id != current.id:
        raise HTTPException(status_code=404, detail="Tracker not found")
    return crud.create_activity(db, a)