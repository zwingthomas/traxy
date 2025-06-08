from sqlalchemy import Table, Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base, engine

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
    hashed_password = Column(String)
    timezone = Column(String)

    # self-referential many-to-many
    friends = relationship(
        'User',
        secondary=friendships,
        primaryjoin=(friendships.c.user_id == id),
        secondaryjoin=(friendships.c.friend_id == id),
        backref='friended_by'
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

def init_db():
    Base.metadata.create_all(bind=engine)
