from pydantic import BaseModel, constr
from datetime import datetime
from typing import List, Dict, Optional

class UserCreate(BaseModel):
    username: constr(min_length=3)
    password: constr(min_length=6)

class UserOut(BaseModel):
    id: int
    username: str
    class Config: orm_mode = True

class TrackerBase(BaseModel):
    name: str
    color: str
    rule: Dict[str, int]
    visibility: str

class TrackerCreate(TrackerBase): pass
class TrackerOut(TrackerBase):
    id: int
    user_id: int
    class Config: orm_mode = True

class ActivityCreate(BaseModel):
    tracker_id: int
    value: int = 1

class DailyAggregate(BaseModel):
    date: datetime
    total: int

class Token(BaseModel):
    access_token: str
    token_type: str = 'bearer'