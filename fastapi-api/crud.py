import os
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Date
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import jwt

import models, schemas

# Setup security
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.getenv('SECRET_KEY', 'CHANGE_ME')
ALGORITHM = os.getenv('ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', 60 * 24 * 7))


def get_password_hash(password: str) -> str:
    return pwd_ctx.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_ctx.verify(plain, hashed)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# User
def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    db_user = models.User(
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def authenticate_user(db: Session, username: str, password: str) -> Optional[models.User]:
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


# Tracker
def get_trackers_for_user(db: Session, user_id: int, visibility: List[str], current_user: Optional[models.User] = None) -> List[models.Tracker]:
    q = db.query(models.Tracker).filter(
        models.Tracker.user_id == user_id,
        models.Tracker.visibility.in_(visibility)
    )
    return q.all()

def get_tracker(db: Session, tracker_id: int) -> Optional[models.Tracker]:
    return db.query(models.Tracker).filter(models.Tracker.id == tracker_id).first()

def create_tracker(db: Session, user_id: int, t: schemas.TrackerCreate) -> models.Tracker:
    db_t = models.Tracker(
        user_id=user_id,
        name=t.name,
        color=t.color,
        rule=t.rule,
        visibility=t.visibility
    )
    db.add(db_t)
    db.commit()
    db.refresh(db_t)
    return db_t

def update_tracker(db: Session, user_id: int, tracker_id: int, t: schemas.TrackerCreate) -> models.Tracker:
    db_t = get_tracker(db, tracker_id)
    if not db_t or db_t.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker not found")
    db_t.name = t.name
    db_t.color = t.color
    db_t.rule = t.rule
    db_t.visibility = t.visibility
    db.commit()
    db.refresh(db_t)
    return db_t

def delete_tracker(db: Session, user_id: int, tracker_id: int) -> None:
    db_t = get_tracker(db, tracker_id)
    if not db_t or db_t.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker not found")
    db.delete(db_t)
    db.commit()

# Activity and aggregates

def create_activity(db: Session, a: schemas.ActivityCreate) -> models.Activity:
    db_a = models.Activity(tracker_id=a.tracker_id, value=a.value)
    db.add(db_a)
    db.commit()
    db.refresh(db_a)
    return db_a


def get_daily_aggregates(db: Session, tracker_id: int, days: int = 365) -> List[dict]:
    cutoff = datetime.utcnow() - timedelta(days=days)
    rows = (
        db.query(
            cast(models.Activity.timestamp, Date).label('date'),
            func.sum(models.Activity.value).label('total')
        )
        .filter(models.Activity.tracker_id == tracker_id, models.Activity.timestamp >= cutoff)
        .group_by(cast(models.Activity.timestamp, Date))
        .order_by(cast(models.Activity.timestamp, Date))
        .all()
    )
    return [{'date': r.date.isoformat(), 'total': r.total} for r in rows]