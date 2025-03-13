from sqlalchemy.orm import Session

from app.crud import create_booking as crud_create_booking
from app.crud import update_object as crud_update_object
from app.models import Booking, Guest
from app.schemas import BookingCreate


def create_booking(db: Session, booking_data: BookingCreate):
    """Handles business logic before creating a booking."""

    guest = db.query(Guest).filter(Guest.id == booking_data.guest_id).first()
    if not guest:
        raise ValueError("Guest does not exist")

    if booking_data.check_out < booking_data.check_in:
        raise ValueError("Check-out date must be after check-in date")

    return crud_create_booking(db, booking_data)


def confirm_booking(db: Session, booking_id: int):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise ValueError("Booking not found")

    if booking.confirmed:
        raise ValueError("Booking is already confirmed")

    # TODO: send notification

    crud_update_object(db, booking, {"confirmed": True})

    return booking
