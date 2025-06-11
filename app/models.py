import datetime
from enum import Enum

from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, Float, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship

from app.database import Base


class PriceType(str, Enum):
    ELECTRICITY_PER_KWH = "electricity_per_kwh"
    STAY_PER_NIGHT = "stay_per_night" 
    GAS_PER_CUBIC_METER = "gas_per_cubic_meter"
    FIREWOOD_PER_BOX = "firewood_per_box"


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    guest_id = Column(Integer, ForeignKey("guests.id"))
    check_in = Column(Date)
    check_out = Column(Date)
    confirmed = Column(Boolean, default=False)
    final_info_sent = Column(Boolean, default=False)
    invoice_created = Column(Boolean, default=False)
    invoice_sent = Column(Boolean, default=False)
    paid = Column(Boolean, default=False)
    
    # Kurkarten email tracking
    kurkarten_email_sent = Column(Boolean, default=False)
    kurkarten_email_sent_date = Column(DateTime, nullable=True)
    
    # Pre-arrival email tracking
    pre_arrival_email_sent = Column(Boolean, default=False)
    pre_arrival_email_sent_date = Column(DateTime, nullable=True)
    
    # Kurtaxe (tourist tax) information
    kurtaxe_amount = Column(Float, nullable=True)
    kurtaxe_notes = Column(Text, nullable=True)
    
    # Invoice tracking
    invoice_id = Column(String, nullable=True)
    invoice_sent_date = Column(DateTime, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)

    guest = relationship("Guest", back_populates="bookings")
    meter_readings = relationship("MeterReading", back_populates="booking", uselist=False)
    payments = relationship("Payment", back_populates="booking")


class Guest(Base):
    __tablename__ = "guests"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    pays_dayrate = Column(Boolean, default=True)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)

    bookings = relationship("Booking", back_populates="guest")


class MeterReading(Base):
    __tablename__ = "meter_readings"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"), unique=True)
    
    # Electricity readings
    electricity_start = Column(Float, nullable=True)
    electricity_end = Column(Float, nullable=True)
    
    # Gas readings
    gas_start = Column(Float, nullable=True) 
    gas_end = Column(Float, nullable=True)
    
    # Firewood
    firewood_boxes = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)

    booking = relationship("Booking", back_populates="meter_readings")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id"))
    
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    payment_method = Column(String, nullable=True)  # bank transfer, cash, etc.
    reference = Column(String, nullable=True)  # bank reference or note
    notes = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)

    booking = relationship("Booking", back_populates="payments")


class UnitPrice(Base):
    __tablename__ = "unit_prices"

    id = Column(Integer, primary_key=True, index=True)
    
    # Specific price types with units
    price_type = Column(SQLEnum(PriceType), nullable=False)
    price_per_unit = Column(Float, nullable=False)
    currency = Column(String, default="EUR")
    
    # Effective date range
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    
    # Metadata
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.datetime.utcnow)
