import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import crud, schemas, deps

router = APIRouter(prefix='/api/auth', tags=['auth'])
logger = logging.getLogger("app.routers.auth")


@router.post('/signup', response_model=schemas.UserOut)
def signup(u: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    logger.info("signup called with username=%s", u.username)
    try:
        user = crud.create_user(db, u)
        logger.info("signup succeeded id=%s username=%s", user.id, user.username)
        return user
    except HTTPException:
        # e.g. username already taken
        logger.warning("signup failed for username=%s: username taken", u.username)
        raise
    except Exception as e:
        logger.exception("unexpected error in signup for username=%s: %s", u.username, e)
        raise HTTPException(500, "Internal server error")


@router.post('/login', response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(deps.get_db)):
    logger.info("login attempt for username=%s", form_data.username)
    try:
        user = crud.authenticate_user(db, form_data.username, form_data.password)
        if not user:
            logger.warning("login failed for username=%s: bad credentials", form_data.username)
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = crud.create_access_token({'sub': user.username})
        logger.info("login succeeded for username=%s, token issued", form_data.username)
        return {'access_token': token}

    except HTTPException:
        # pass through our 401
        raise
    except Exception as e:
        logger.exception("unexpected error in login for username=%s: %s", form_data.username, e)
        raise HTTPException(500, "Internal server error")