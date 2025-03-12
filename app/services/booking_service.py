from sqlalchemy.orm import Session

from app.crud import create_booking as crud_create_booking
from app.models import Guest
from app.schemas import BookingCreate


def create_booking(db: Session, booking_data: BookingCreate):
    """Handles business logic before creating a booking."""

    # ✅ 1. Check if Guest Exists
    guest = db.query(Guest).filter(Guest.id == booking_data.guest_id).first()
    if not guest:
        raise ValueError("Guest does not exist")

    # ✅ 2. Validate Check-in & Check-out Dates
    if booking_data.check_out < booking_data.check_in:
        raise ValueError("Check-out date must be after check-in date")

    # ✅ 3. Call the CRUD function (since data is now valid)
    return crud_create_booking(db, booking_data)

