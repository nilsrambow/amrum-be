import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr, Field

from app.models import PriceType, BookingStatus


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


class GuestUpdate(BaseModel):
    """Schema for partial guest updates - excludes system-managed fields"""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    pays_dayrate: Optional[bool] = None
    is_admin: Optional[bool] = None

    class Config:
        extra = "forbid"


# Meter Reading Schemas
class MeterReadingBase(BaseModel):
    electricity_start: Optional[float] = None
    electricity_end: Optional[float] = None
    gas_start: Optional[float] = None
    gas_end: Optional[float] = None
    firewood_boxes: Optional[int] = None


class MeterReadingCreate(MeterReadingBase):
    booking_id: int


class MeterReadingUpdate(MeterReadingBase):
    pass


class MeterReadingResponse(MeterReadingBase):
    id: int
    booking_id: int
    created_at: datetime.datetime
    modified_at: datetime.datetime

    class Config:
        from_attribute = True


# Payment Schemas
class PaymentBase(BaseModel):
    amount: float
    payment_date: datetime.date
    payment_method: Optional[str] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


class PaymentCreate(PaymentBase):
    booking_id: int


class PaymentResponse(PaymentBase):
    id: int
    booking_id: int
    created_at: datetime.datetime
    modified_at: datetime.datetime

    class Config:
        from_attribute = True


# Unit Price Schemas - Base
class UnitPriceBase(BaseModel):
    price_per_unit: float = Field(..., gt=0, description="Price must be greater than 0")
    currency: str = "EUR"
    effective_from: datetime.date
    effective_to: Optional[datetime.date] = None
    description: Optional[str] = None


class UnitPriceResponse(UnitPriceBase):
    id: int
    price_type: PriceType
    created_at: datetime.datetime
    modified_at: datetime.datetime

    class Config:
        from_attribute = True


# Specific Unit Price Schemas
class ElectricityPriceCreate(UnitPriceBase):
    """Create electricity price in EUR per kWh"""
    price_per_unit: float = Field(..., gt=0, description="Price in EUR per kWh")

    class Config:
        json_schema_extra = {
            "example": {
                "price_per_unit": 0.32,
                "effective_from": "2024-01-01",
                "description": "Electricity rate for 2024"
            }
        }


class StayPriceCreate(UnitPriceBase):
    """Create accommodation price in EUR per night"""
    price_per_unit: float = Field(..., gt=0, description="Price in EUR per night")

    class Config:
        json_schema_extra = {
            "example": {
                "price_per_unit": 85.0,
                "effective_from": "2024-01-01", 
                "description": "Nightly accommodation rate for 2024"
            }
        }


class GasPriceCreate(UnitPriceBase):
    """Create gas price in EUR per cubic meter"""
    price_per_unit: float = Field(..., gt=0, description="Price in EUR per cubic meter")

    class Config:
        json_schema_extra = {
            "example": {
                "price_per_unit": 1.25,
                "effective_from": "2024-01-01",
                "description": "Gas rate for 2024"
            }
        }


class FirewoodPriceCreate(UnitPriceBase):
    """Create firewood price in EUR per box"""
    price_per_unit: float = Field(..., gt=0, description="Price in EUR per box")

    class Config:
        json_schema_extra = {
            "example": {
                "price_per_unit": 12.50,
                "effective_from": "2024-01-01",
                "description": "Firewood cost per box for 2024"
            }
        }


# Updated Booking Schemas
class BookingBase(BaseModel):
    guest_id: int
    check_in: datetime.date
    check_out: datetime.date


class BookingUpdate(BaseModel):
    confirmed: Optional[bool] = None
    kurtaxe_amount: Optional[float] = None
    kurtaxe_notes: Optional[str] = None

    class Config:
        extra = "forbid"


class BookingPartialUpdate(BaseModel):
    """Schema for partial booking updates - excludes system-managed fields"""
    guest_id: Optional[int] = None
    check_in: Optional[datetime.date] = None
    check_out: Optional[datetime.date] = None
    kurtaxe_amount: Optional[float] = None
    kurtaxe_notes: Optional[str] = None

    class Config:
        extra = "forbid"


class KurtaxeUpdate(BaseModel):
    kurtaxe_amount: Optional[float] = None
    kurtaxe_notes: Optional[str] = None


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
    
    # Booking status
    status: BookingStatus = BookingStatus.NEW
    
    # New fields
    kurkarten_email_sent: bool = False
    kurkarten_email_sent_date: Optional[datetime.datetime] = None
    pre_arrival_email_sent: bool = False
    pre_arrival_email_sent_date: Optional[datetime.datetime] = None
    kurtaxe_amount: Optional[float] = None
    kurtaxe_notes: Optional[str] = None
    invoice_id: Optional[str] = None
    invoice_sent_date: Optional[datetime.datetime] = None
    
    created_at: datetime.datetime
    modified_at: datetime.datetime
    
    # Relationships
    meter_readings: Optional[MeterReadingResponse] = None
    payments: Optional[List[PaymentResponse]] = None
    
    # Invoice details (calculated)
    invoice_details: Optional[dict] = None
    
    # Token information
    access_token: Optional[str] = None
    token_expires_at: Optional[datetime.datetime] = None

    class Config:
        from_attribute = True


# Token Schemas
class BookingTokenResponse(BaseModel):
    token: str
    expires_at: datetime.datetime
    created_at: datetime.datetime
    last_used_at: Optional[datetime.datetime] = None

    class Config:
        from_attribute = True


class GuestBookingResponse(BaseModel):
    """Response for guest access via magic link - limited booking info"""
    id: int
    check_in: datetime.date
    check_out: datetime.date
    confirmed: bool
    status: BookingStatus
    kurtaxe_amount: Optional[float] = None
    kurtaxe_notes: Optional[str] = None
    created_at: datetime.datetime
    
    # Guest info (limited)
    guest_name: str
    guest_email: str
    
    # Meter readings (if any)
    meter_readings: Optional[MeterReadingResponse] = None
    
    # Payments (if any)
    payments: Optional[List[PaymentResponse]] = None
    
    # Invoice details (calculated)
    invoice_details: Optional[dict] = None

    class Config:
        from_attribute = True


# Authentication Schemas
class AdminUserBase(BaseModel):
    username: str
    email: EmailStr


class AdminUserCreate(AdminUserBase):
    password: str


class AdminUserResponse(AdminUserBase):
    id: int
    is_active: bool
    is_superuser: bool
    created_at: datetime.datetime
    last_login: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str
