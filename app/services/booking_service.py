from sqlalchemy.orm import Session

from app.models import Booking
from app.schemas import BookingCreate


def create_booking(db: Session, booking_data: BookingCreate):
    new_booking = Booking(
        guest_id=booking_data.guest_id,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
        confirmed=booking_data.confirmed,
        final_info_sent=booking_data.final_info_sent,
        invoice_created=booking_data.invoice_created,
        invoice_sent=booking_data.invoice_sent,
        paid=booking_data.paid,
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


def get_all_bookings(db: Session):
    return db.query(Booking).all()
