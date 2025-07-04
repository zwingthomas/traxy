import os
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
import crud
import database
import models
from typing import Optional

import secrets_manager


def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        SECRET_KEY = secrets_manager.get_secret('BACKEND_SECRET_KEY')
        payload = jwt.decode(token, SECRET_KEY, algorithms=[
                             os.getenv('ALGORITHM', 'HS256')])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc
    user = crud.get_user_by_username(db, username)
    if user is None:
        raise credentials_exc
    return user


oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/auth/login",
    auto_error=False,
)


def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db),
):
    if not token:
        return None
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None
