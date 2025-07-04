from pydantic import BaseModel, Field, validator, EmailStr, constr, root_validator
from datetime import datetime, date, timedelta
from typing import Annotated, List, Dict, Optional
from enum import Enum


class UserCreate(BaseModel):
    username: Annotated[str, Field(min_length=3)]
    password: Annotated[str, Field(min_length=6)]
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    email:      Optional[EmailStr] = None
    phone:      Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class FriendOut(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = {
        "from_attributes": True
    }


class UserOut(BaseModel):
    id: int
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    friends: List[FriendOut] = Field(
        default_factory=list,
        description="List of this user’s friends"
    )

    model_config = {
        "from_attributes": True
    }


class DailyAggregate(BaseModel):
    date: datetime
    total: int


class WidgetType(str, Enum):
    boolean = "boolean"
    counter = "counter"
    input = "input"


class TrackerBase(BaseModel):
    name: str
    color: str
    rule: Dict[str, int] = Field(default_factory=dict)
    visibility: str = Field("private")
    widget_type: WidgetType = Field(WidgetType.boolean)


class TrackerCreate(TrackerBase):
    pass


class TrackerOut(TrackerBase):
    id: int
    user_id: int
    aggregate: List[DailyAggregate] = Field(
        default_factory=list,
        description="List of (date,total) for this tracker"
    )
    model_config = {
        "from_attributes": True
    }


class TrackerReorder(BaseModel):
    ordered_ids: List[int]


class ActivityCreate(BaseModel):
    tracker_id: int
    value: int = 1
    day: Optional[date] = None

    # ensure the client can only write today / yesterday / 2-days-ago
    # do not have access to user's timezone here thus validation is done in routers/activities.py
    # @validator("day", pre=True, always=True)
    # def _validate_date(cls, v):
    #     if v is None:
    #         return date.today()

    #     if isinstance(v, str):
    #         v = date.fromisoformat(v)

    #     if v < date.today() - timedelta(days=2) or v > date.today():
    #         raise ValueError("date must be today or within the last 2 days")
    #     return v


class DailyAggregate(BaseModel):
    date: datetime
    total: int


class ProfileOut(BaseModel):
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    email:      Optional[EmailStr] = None
    phone:      Optional[str] = None


class ProfileUpdate(BaseModel):
    username:   Optional[str] = None
    first_name: Optional[str] = None
    last_name:  Optional[str] = None
    email:      Optional[EmailStr] = None
    phone:      Optional[str] = None

    @root_validator(pre=True)
    def blank_strings_to_none(cls, values):
        return {k: (v or None) for k, v in values.items()}

    class Config:
        # ignore any fields not sent
        extra = "ignore"


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordReset(BaseModel):
    token: str
    new_password: str
