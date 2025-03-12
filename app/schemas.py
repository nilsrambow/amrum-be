import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


class GuestBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    pays_dayrate: bool = True
    is_admin: Optional[bool] = False


class GuestCreate(GuestBase):
    password: str


class GuestResponse(GuestBase):
    id: int
    created_at: datetime.datetime
    modified_at: datetime.datetime

    class Config:
        from_attribute = True
