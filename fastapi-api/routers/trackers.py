from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, deps

router = APIRouter(prefix='/api/trackers', tags=['trackers'])

@router.get('', response_model=List[schemas.TrackerOut])
def list_trackers(db: Session = Depends(deps.get_db), current=Depends(deps.get_current_user)):
    trackers = crud.get_trackers_for_user(db, current.id, ['private','friends','public'], current)
    out = []
    for t in trackers:
        t_dict = schemas.TrackerOut.from_orm(t).dict()
        t_dict['aggregate'] = crud.get_daily_aggregates(db, t.id)
        out.append(t_dict)
    return out

@router.post('', response_model=schemas.TrackerOut)
def create_tracker(t: schemas.TrackerCreate,
                   db: Session = Depends(deps.get_db),
                   current=Depends(deps.get_current_user)):
    return crud.create_tracker(db, current.id, t)

@router.put('/{tracker_id}', response_model=schemas.TrackerOut)
def update_tracker(tracker_id: int, t: schemas.TrackerCreate,
                   db: Session = Depends(deps.get_db),
                   current=Depends(deps.get_current_user)):
    return crud.update_tracker(db, current.id, tracker_id, t)

@router.delete('/{tracker_id}', status_code=204)
def delete_tracker(tracker_id: int,
                   db: Session = Depends(deps.get_db),
                   current=Depends(deps.get_current_user)):
    crud.delete_tracker(db, current.id, tracker_id)