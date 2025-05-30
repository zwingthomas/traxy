import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import crud, schemas, deps
from typing import List

router = APIRouter(prefix='/api/users', tags=['users'])
logger = logging.getLogger("app.routers.users")


@router.get('/me', response_model=schemas.UserOut)
def read_current_user(
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user)
):
    logger.info("read_current_user called, user_id=%s", current.id)
    return current


@router.get(
    '/{username}/trackers',
    response_model=List[schemas.TrackerOut]
)
def read_user_trackers(
    username: str,
    visibility: str = "public",
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user_optional)
):
    logger.info(
        "read_user_trackers called for username=%s by user_id=%s visibility=%s",
        username, getattr(current, "id", None), visibility
    )

    # First, resolve the requested user
    user = crud.get_user_by_username(db, username)
    if not user:
        logger.warning("read_user_trackers: user not found username=%s", username)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    try:
        trackers = crud.get_trackers_for_user(
            db,
            user.id,
            visibility.split(','),
            current
        )
        out = []
        for t in trackers:
            t_dict = schemas.TrackerOut.from_orm(t).dict()
            t_dict['aggregate'] = crud.get_daily_aggregates(db, t.id)
            out.append(t_dict)
        logger.info(
            "read_user_trackers returning %d trackers for username=%s",
            len(out), username
        )
        return out

    except Exception as e:
        logger.exception(
            "Error fetching trackers for username=%s by user_id=%s: %s",
            username, getattr(current, "id", None), e
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="Internal server error")
    
@router.get("/search", response_model=List[schemas.UserOut])
def search_users(prefix: str, db: Session = Depends(deps.get_db)):
    return crud.search_users_by_prefix(db, prefix, limit=10)

@router.post("/{username}/friends", status_code=201)
def add_friend(username: str, db: Session = Depends(deps.get_db),
               current=Depends(deps.get_current_user)):
    crud.add_friend(db, current.id, username)
    return {"added": username}