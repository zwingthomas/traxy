from pydantic import BaseModel, Field
from datetime import datetime
from typing import Annotated, Dict

class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3)]
    password: Annotated[str, Field(min_length=6)]

class UserOut(BaseModel):
    id: int
    username: str

    model_config = {
        "from_attributes": True
    }

class TrackerBase(BaseModel):
    name: str
    color: str
    rule: Dict[str, int] = Field(default_factory=dict)
    visibility: str = Field("private")

class TrackerCreate(TrackerBase):
    pass

class TrackerOut(TrackerBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

class ActivityCreate(BaseModel):
    tracker_id: int
    value: int = 1

class DailyAggregate(BaseModel):
    date: datetime
    total: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"