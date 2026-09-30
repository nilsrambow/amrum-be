from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.token_service import TokenService
from app.services.meter_service import MeterService
from app.schemas import GuestBookingResponse, MeterReadingBase, MeterReadingCreate, MeterReadingResponse

def guest_privacy_headers(response: Response) -> None:
    """Guest pages are only meant for the holder of the secret link: keep them out of caches and search indexes."""
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    response.headers["Referrer-Policy"] = "no-referrer"


router = APIRouter(prefix="/guest", tags=["guest"], dependencies=[Depends(guest_privacy_headers)])


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
    readings: MeterReadingBase,
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

    meter_service = MeterService(db)
    if meter_service.get_meter_reading(booking.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Meter readings have already been submitted for this booking"
        )
    
    # Add the readings
    meter_service = MeterService(db)
    meter_reading = meter_service.add_meter_readings(readings)
    
    return meter_reading
