import os
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import func, cast, Date, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from passlib.context import CryptContext
from jose import jwt

import secrets_manager

import models, schemas
from models import friendships, Activity, Tracker, PasswordResetToken, User

# Setup security
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = secrets_manager.get_secret('BACKEND_SECRET_KEY')
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
def get_user_by_username(db: Session, uname: str) -> Optional[models.User]:
    return (
        db.query(models.User)
        .filter(func.lower(models.User.username) == uname.lower())
        .first()
    )

def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).get(user_id)

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    if get_user_by_username(db, user.username):
        raise HTTPException(status_code=400, detail="Username already taken")
    db_user = models.User(
        username=user.username,
        usernameLower=func.lower(user.username),
        hashed_password=get_password_hash(user.password),

        # the following may be None
        first_name     = user.first_name,
        last_name      = user.last_name,
        email          = user.email,
        phone          = user.phone
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError as e:
        db.rollback()
        # you can catch UNIQUE‐constraint on email/phone here
        # and reraise HTTPException(409, …) if you like
        raise
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
        func.lower(models.Tracker.visibility).in_(visibility)
    ).order_by(models.Tracker.position)
    return q.all()

def get_tracker(db: Session, tracker_id: int) -> Optional[models.Tracker]:
    return db.query(models.Tracker).filter(models.Tracker.id == tracker_id).first()

def create_tracker(db: Session, user_id: int, t: schemas.TrackerCreate) -> models.Tracker:
    db_t = models.Tracker(
        user_id=user_id,
        name=t.name,
        color=t.color,
        rule=t.rule,
        visibility=t.visibility,
        widget_type=t.widget_type.value
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
    db_t.widget_type = t.widget_type.value
    db.commit()
    db.refresh(db_t)
    return db_t

def delete_tracker(db: Session, user_id: int, tracker_id: int) -> None:
    db_t = get_tracker(db, tracker_id)
    if not db_t or db_t.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tracker not found")
    db.delete(db_t)
    db.commit()

def reorder_trackers(db: Session, user_id: int, ordered_ids: List[int]) -> None:
    # fetch only this user’s trackers in the given list
    trackers = (
        db.query(models.Tracker)
          .filter(
            models.Tracker.user_id == user_id,
            models.Tracker.id.in_(ordered_ids)
          )
          .all()
    )
    id_to_obj = {t.id: t for t in trackers}

    # assign the new positions
    for new_pos, tid in enumerate(ordered_ids):
        if tid in id_to_obj:
            id_to_obj[tid].position = new_pos

    db.commit()

# Activity and aggregates

def create_activity(db, tracker_id: int, value: int, ts):
    # floor ts → date; we store everything at midnight so comparisons are easy
    day_start = ts.replace(hour=0, minute=0, second=0, microsecond=0)

    # look up the tracker so we know its type
    tracker = db.query(Tracker).filter(Tracker.id == tracker_id).one()

    existing = db.query(Activity).filter(
        and_(
            Activity.tracker_id == tracker_id,
            func.date(Activity.timestamp) == day_start.date()
        )
    ).first()

    if existing:
        if tracker.widget_type == 'counter':
            # counters accumulate
            existing.value += value
        else:
            # booleans and inputs overwrite
            existing.value = value
        db.commit()
        db.refresh(existing)
        return existing

    # no activity row yet → create one
    new = Activity(
        tracker_id = tracker_id,
        timestamp   = day_start,
        value       = value
    )
    db.add(new)
    db.commit()
    db.refresh(new)
    return new


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

def delete_activities_for_day(db: Session, tracker_id: int, day: Date) -> None:
    start = datetime.combine(day, datetime.min.time())
    end   = datetime.combine(day, datetime.max.time())
    db.query(models.Activity)\
      .filter(models.Activity.tracker_id == tracker_id,
              models.Activity.timestamp >= start,
              models.Activity.timestamp <= end)\
      .delete(synchronize_session=False)
    db.commit()

# Friends

def search_users_by_prefix(db: Session, prefix: str, limit: int = 10):
    return db.query(models.User)\
             .filter(models.User.username.ilike(f"{prefix}%"))\
             .limit(limit)\
             .all()

def add_friend(db: Session, user_id: int, friend_username: str) -> None:
    """Add <friend_username> as mutual friend of <user_id> (idempotent)."""
    me      = db.get(models.User, user_id)
    friend  = get_user_by_username(db, friend_username)
    if not friend or me.id == friend.id:
        raise HTTPException(404, "User not found")

    if friend not in me.friends:     # many-to-many append is idempotent
        me.friends.append(friend)
        friend.friends.append(me)    # mutual
        db.commit()

def get_friends(db: Session, user_id: int) -> list[models.User]:
    u = db.get(models.User, user_id)
    return u.friends if u else []

def are_friends(db: Session, user_id: int, other_id: int) -> bool:
    me    = db.get(models.User, user_id)
    other = db.get(models.User, other_id)
    if not me or not other:
        return False
    return other in me.friends

def remove_friend(db: Session, user_id: int, friend_username: str) -> None:
    me     = db.get(models.User, user_id)
    friend = get_user_by_username(db, friend_username)
    if not friend or me.id == friend.id:
        raise HTTPException(404, "User not found")
    # remove both sides
    if friend in me.friends:
        me.friends.remove(friend)
    if me in friend.friends:
        friend.friends.remove(me)
    db.commit()

def update_profile(db: Session, user_id: int, data: schemas.ProfileUpdate):
    # Dump only the non-None fields
    payload = data.model_dump(exclude_none=True)

    # Normalize: drop empty strings so we don't overwrite with ""
    payload = {
        k: v for k, v in payload.items()
        if not (isinstance(v, str) and v.strip() == "")
    }

    # Load the existing row so we can compare
    user = db.get(models.User, user_id)

    # If they passed back the same value already in their database, drop it
    for field, new_val in list(payload.items()):
        old_val = getattr(user, field, None)
        if field == "username":
            # we'll also generate usernameLower a bit later
            if new_val == old_val:
                payload.pop(field)
        else:
            if new_val == old_val:
                payload.pop(field)

    # If they really did change username, set usernameLower
    if "username" in payload:
        payload["usernameLower"] = payload["username"].lower()

    try:
        if payload:
            db.query(models.User)\
              .filter(models.User.id == user_id)\
              .update(payload, synchronize_session=False)
            db.commit()
    # This catches the UNIQUE constraint on username / email / phone
    except IntegrityError as e:
        db.rollback()
        # try Postgres-style diag
        constraint = None
        orig = getattr(e, "orig", None)
        diag  = getattr(orig, "diag", None)
        if diag and diag.constraint_name:
            constraint = diag.constraint_name.lower()
        else:
            # fallback: lower‐case the textual error
            msg = str(orig or e).lower()
            if "username_lower" in msg or "usernamelower" in msg:
                constraint = "uq_users_username_lower"
            elif "email" in msg:
                constraint = "uq_users_email"
            elif "phone" in msg:
                constraint = "uq_users_phone"

        # now map constraint → field
        if constraint == "uq_users_username_lower":
            raise HTTPException(409, "That username is already taken.")
        elif constraint == "uq_users_email":
            raise HTTPException(409, "That email address is already in use.")
        elif constraint == "uq_users_phone":
            raise HTTPException(409, "That phone number is already registered.")
        else:
            # unexpected unique‐violation
            raise HTTPException(409, "That value is already in use.")
    # A different exception occured
    except:
        db.rollback()
        raise HTTPException(500, "Something went wrong")

# Change password

def change_password(db: Session, user: models.User, old_pw: str, new_pw: str):
    if not pwd_ctx.verify(old_pw, user.hashed_password):
        raise HTTPException(400, "Old password incorrect")
    user.hashed_password = pwd_ctx.hash(new_pw)
    db.commit()

def create_password_reset(db: Session, email: str) -> PasswordResetToken:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return None
    # invalidate old tokens?
    tok = PasswordResetToken(user_id=user.id)
    db.add(tok)
    db.commit()
    db.refresh(tok)
    return tok


# Forgot password

def verify_reset_token(db: Session, token: str) -> PasswordResetToken:
    now = datetime.utcnow()
    pr = (
      db.query(PasswordResetToken)
        .filter(
           PasswordResetToken.token == token,
           PasswordResetToken.expires_at >= now,
           PasswordResetToken.used == None
        )
        .first()
    )
    return pr

def mark_token_used(db: Session, pr: PasswordResetToken):
    pr.used = datetime.utcnow()
    db.commit()

def change_password_by_user_id(db: Session, user_id: int, new_password: str):
    user = db.query(User).get(user_id)
    user.hashed_password = pwd_ctx.hash(new_password)
    db.commit()