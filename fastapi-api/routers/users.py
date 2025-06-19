import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
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

@router.patch("/me", response_model=schemas.UserOut)
def update_me(
    patch: dict,
    db: Session = Depends(deps.get_db),
    current=Depends(deps.get_current_user),
):
    # only allow timezone field
    if "timezone" in patch:
        current.timezone = patch["timezone"]
        db.commit()
        db.refresh(current)
    return current

@router.get("/me/profile", response_model=schemas.ProfileOut)
def read_my_profile(current = Depends(deps.get_current_user)):
    return current  # FastAPI will filter via the schema

@router.patch("/me/profile", response_model=schemas.ProfileOut)
def update_my_profile(payload: schemas.ProfileUpdate, db: Session = Depends(deps.get_db), current = Depends(deps.get_current_user)):
    crud.update_profile(db, current.id, payload)
    return crud.get_user_by_id(db, current.id)

@router.put("/me/password", status_code=204)
def update_my_password(payload: schemas.PasswordChange, db: Session = Depends(deps.get_db), current = Depends(deps.get_current_user)):
    crud.change_password(db, current, payload.old_password, payload.new_password)


# @router.get(
#     '/{username}/trackers',
#     response_model=List[schemas.TrackerOut]
# )
# def read_user_trackers(
#     username: str,
#     visibility: List[str] = Query(["public"], description="Comma‐separated list of visibilities"),
#     db: Session = Depends(deps.get_db),
#     current=Depends(deps.get_current_user_optional)
# ):
#     logger.info(
#         "read_user_trackers called for username=%s by user_id=%s visibility=%s",
#         username, getattr(current, "id", None), visibility
#     )

#     if any(v in ("friends", "private") for v in visibility) and not current:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="You must be authenticated to see friends- or private-only trackers",
#         )

#     # First, resolve the requested user
#     user = crud.get_user_by_username(db, username)
#     if not user:
#         logger.warning("read_user_trackers: user not found username=%s", username)
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

#     if "private" in visibility and current.id != user.id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You may only view your own private trackers",
#         )

#     try:
#         trackers = crud.get_trackers_for_user(
#             db,
#             user.id,
#             visibility,
#             current
#         )
#         out = []
#         for t in trackers:
#             t_dict = schemas.TrackerOut.from_orm(t).dict()
#             t_dict['aggregate'] = crud.get_daily_aggregates(db, t.id)
#             out.append(t_dict)
#         logger.info(
#             "read_user_trackers returning %d trackers for username=%s",
#             len(out), username
#         )
#         return out

#     except Exception as e:
#         logger.exception(
#             "Error fetching trackers for username=%s by user_id=%s: %s",
#             username, getattr(current, "id", None), e
#         )
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                             detail="Internal server error")
    
@router.get("/search", response_model=List[schemas.UserOut])
def search_users(prefix: str, db: Session = Depends(deps.get_db)):
    return crud.search_users_by_prefix(db, prefix, limit=10)

@router.get("/{username}/friends", response_model=list[schemas.UserOut])
def read_user_friends(
    username: str,
    db: Session = Depends(deps.get_db),
    current    = Depends(deps.get_current_user_optional)   # may be None (anonymous)
):
    user = crud.get_user_by_username(db, username)
    if not user:
        raise HTTPException(404, "User not found")

    # anonymous: only allowed if username has public profile (TODO)
    if current is None:
        raise HTTPException(401, "Login required")

    # asking for to see someone else's friends → must already be friends
    if current.id != user.id:
        friend_ids = {f.id for f in crud.get_friends(db, user.id)}
        if current.id not in friend_ids:
            raise HTTPException(403, "Friends list is private")

    return crud.get_friends(db, user.id)


@router.post("/{username}/friends", status_code=201)
def add_friend(
    username: str,
    db: Session = Depends(deps.get_db),
    current    = Depends(deps.get_current_user)
):
    crud.add_friend(db, current.id, username)
    return {"added": username}

@router.delete("/{username}/friends")
def delete_friend(
    username: str,
    username_to_remove: str = Query(..., alias="username"),
    db: Session = Depends(deps.get_db),
    current = Depends(deps.get_current_user),
):
    # current.username is “you”
    crud.remove_friend(db, current.id, username_to_remove)
    return {"removed": username_to_remove}