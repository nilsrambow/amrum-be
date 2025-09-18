from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.token_service import TokenService
from app.services.meter_service import MeterService
from app.schemas import GuestBookingResponse, MeterReadingCreate, MeterReadingResponse

router = APIRouter(prefix="/guest", tags=["guest"])


@router.get("/booking/{token}", response_model=GuestBookingResponse)
def get_booking_by_token(token: str, db: Session = Depends(get_db)):
    """Get booking details for guest access via magic link"""
    token_service = TokenService(db)
    booking = token_service.get_booking_by_token(token)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )
    
    return booking


@router.post("/booking/{token}/readings", response_model=MeterReadingResponse)
def add_meter_readings(
    token: str, 
    readings: MeterReadingCreate, 
    db: Session = Depends(get_db)
):
    """Add meter readings for a booking via magic link"""
    token_service = TokenService(db)
    booking = token_service.validate_token(token)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )
    
    # Verify the booking ID matches the token
    if readings.booking_id != booking.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking ID mismatch"
        )
    
    # Add the readings
    meter_service = MeterService(db)
    meter_reading = meter_service.add_meter_readings(readings)
    
    return meter_reading


@router.get("/booking/{token}/readings", response_model=MeterReadingResponse)
def get_meter_readings(token: str, db: Session = Depends(get_db)):
    """Get meter readings for a booking via magic link"""
    token_service = TokenService(db)
    booking = token_service.validate_token(token)
    
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid or expired token"
        )
    
    # Get the readings
    meter_service = MeterService(db)
    meter_reading = meter_service.get_meter_readings_by_booking_id(booking.id)
    
    if not meter_reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No meter readings found for this booking"
        )
    
    return meter_reading 