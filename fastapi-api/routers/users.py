from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import crud, schemas, deps

router = APIRouter(prefix='/api/users', tags=['users'])

@router.get('/me', response_model=schemas.UserOut)
def read_current_user(db: Session = Depends(deps.get_db),
                      current=Depends(deps.get_current_user)):
    return current

@router.get('/{username}/trackers', response_model=List[schemas.TrackerOut])
def read_user_trackers(username: str, visibility: str = "public",
                       db: Session = Depends(deps.get_db),
                       current=Depends(deps.get_current_user_optional)):
    trackers = crud.get_trackers_for_user(db, username.id, visibility, current)
    out = []
    for t in trackers:
        t_dict = schemas.TrackerOut.from_orm(t).dict()
        t_dict['aggregate'] = crud.get_daily_aggregates(db, t.id)
        out.append(t_dict)
    return out