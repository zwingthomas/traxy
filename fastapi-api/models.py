from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import metadata, engine
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base(metadata=metadata)

# Friendship join table
friendships = Table(
    'friendships', metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('friend_id', Integer, ForeignKey('users.id'), primary_key=True)
)

class User(Base):
    __tablename__ = 'users'
    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    friends = relationship(
        'User',
        secondary=friendships,
        # local user.id == friendships.c.user_id
        primaryjoin=(friendships.c.user_id == id),
        # remote user.id == friendships.c.friend_id
        secondaryjoin=(friendships.c.friend_id == id),
        backref='friended_by'
    )

class Tracker(Base):
    __tablename__ = 'trackers'
    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey('users.id'))
    name       = Column(String)
    color      = Column(String)
    rule       = Column(JSON)
    visibility = Column(String, default='private')  # public, friends, private

class Activity(Base):
    __tablename__ = 'activities'
    id          = Column(Integer, primary_key=True, index=True)
    tracker_id  = Column(Integer, ForeignKey('trackers.id'))
    timestamp   = Column(DateTime(timezone=True), server_default=func.now())
    value       = Column(Integer, default=1)

def init_db():
    metadata.create_all(bind=engine)