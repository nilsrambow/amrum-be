import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


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


class BookingBase(BaseModel):
    guest_id: int
    check_in: datetime.date
    check_out: datetime.date


class BookingUpdate(BookingBase):
    guest_id: Optional[None] = Field(None, description="Cannot never updated")
    check_in: Optional[None] = Field(None, description="Cannot be updated")
    check_out: Optional[None] = Field(None, description="Cannot be updated")
    confirmed: Optional[bool] = None
    final_info_sent: Optional[None] = Field(None, description="Cannot be updated")
    invoice_created: Optional[None] = Field(None, description="Cannot be updated")
    invoice_sent: Optional[None] = Field(None, description="Cannot be updated")
    paid: Optional[None] = Field(None, description="Cannot be updated")

    class Config:
        extra = "forbid"


class BookingCreate(BookingBase):
    class Config:
        json_schema_extra = {
            "example": {
                "guest_id": 1,
                "check_in": "2024-06-01",
                "check_out": "2024-06-15",
            }
        }


class BookingResponse(BookingBase):
    id: int
    guest_id: int
    check_in: datetime.date
    check_out: datetime.date
    confirmed: bool = False
    final_info_sent: bool = False
    invoice_created: bool = False
    invoice_sent: bool = False
    paid: bool = False
    created_at: datetime.datetime
    modified_at: datetime.datetime
