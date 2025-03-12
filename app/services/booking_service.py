from sqlalchemy.orm import Session

from app.crud import create_booking as crud_create_booking
from app.crud import update_booking as crud_update_booking
from app.models import Booking, Guest
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


def confirm_booking(db: Session, booking_id: int):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise ValueError("Booking not found")

    if booking.confirmed:
        raise ValueError("Booking is already confirmed")

    # TODO: send notification

    crud_update_booking(db, booking_id, {"confirmed": True})

    return booking
