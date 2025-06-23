import logging
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
import crud
import schemas
import deps

from schemas import PasswordResetRequest, PasswordReset

from deps import get_db
from core.email import send_reset_email

router = APIRouter(prefix='/api/auth', tags=['auth', 'passwords'])
logger = logging.getLogger("app.routers.auth")


@router.post('/signup', response_model=schemas.UserOut)
def signup(u: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    logger.info("signup called with username=%s", u.username)
    try:
        user = crud.create_user(db, u)
        logger.info("signup succeeded id=%s username=%s",
                    user.id, user.username)
        return user
    except HTTPException:
        # e.g. username already taken
        logger.warning(
            "signup failed for username=%s: username taken", u.username)
        raise
    except Exception as e:
        logger.exception(
            "unexpected error in signup for username=%s: %s", u.username, e)
        raise HTTPException(500, "Internal server error")


@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    logger.info("login attempt for username=%s", form_data.username)
    try:
        user = crud.authenticate_user(
            db, form_data.username, form_data.password)
        if not user:
            logger.warning(
                "login failed for username=%s: bad credentials", form_data.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = crud.create_access_token({'sub': user.username})
        logger.info("login succeeded for username=%s, token issued",
                    form_data.username)
        return {'access_token': token}

    except HTTPException:
        # pass through our 401
        raise
    except Exception as e:
        logger.exception(
            "unexpected error in login for username=%s: %s", form_data.username, e)
        raise HTTPException(500, "Internal server error")


@router.post("/password-reset/request", status_code=202)
def password_reset_request(
    payload: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    pr = crud.create_password_reset(db, payload.email)
    if pr:
        background_tasks.add_task(send_reset_email, pr.token, payload.email)
    # Always 202 so as not to leak which emails exist
    return {"msg": "If an account exists, you will receive a reset link."}


@router.post("/password-reset", status_code=200)
def password_reset(
    payload: PasswordReset,
    db: Session = Depends(get_db)
):
    pr = crud.verify_reset_token(db, payload.token)
    if not pr:
        raise HTTPException(400, "Invalid or expired token")
    crud.change_password_by_user_id(db, pr.user_id, payload.new_password)
    crud.mark_token_used(db, pr)
    return {"msg": "Password has been reset"}
