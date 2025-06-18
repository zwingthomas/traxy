from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta

from database import Base, engine

import uuid

# Association table for self-referential friendships
friendships = Table(
    'friendships',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    usernameLower = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    timezone = Column(String)

    first_name     = Column(String(length=60))
    last_name      = Column(String(length=60))
    email          = Column(String, unique=True, index=True)
    phone          = Column(String, unique=True, index=True)
    timezone       = Column(String)

    # self-referential many-to-many
    friends = relationship(
        'User',
        secondary=friendships,
        back_populates="friends",
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
    )

class Tracker(Base):
    __tablename__ = 'trackers'
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    color = Column(String, nullable=True)
    rule = Column(JSON, nullable=True)
    visibility = Column(String, default='private', nullable=False)  # public, friends, private
    activities = relationship("Activity", backref="tracker", cascade="all, delete-orphan")
    position = Column(Integer, nullable=False, default=0)
    widget_type  = Column(String(16), nullable=False, default="boolean")

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True, index=True)
    tracker_id = Column(Integer, ForeignKey('trackers.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    value = Column(Integer, default=1)

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    token      = Column(String, unique=True, index=True, default=lambda: str(uuid.uuid4()))
    expires_at = Column(DateTime, nullable=False, default=lambda: datetime.utcnow() + timedelta(hours=1))
    used       = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="reset_tokens")

def init_db():
    Base.metadata.create_all(bind=engine)
