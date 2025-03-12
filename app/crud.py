from sqlalchemy.orm import Session

from app.models import Booking, Guest
from app.schemas import BookingCreate, GuestCreate
from app.services.guest_service import check_guest_exists, hash_password


def create_booking(db: Session, booking_data: BookingCreate):
    new_booking = Booking(
        guest_id=booking_data.guest_id,
        check_in=booking_data.check_in,
        check_out=booking_data.check_out,
    )

    db.add(new_booking)
    db.commit()
    db.refresh(new_booking)
    return new_booking


def get_all_bookings(db: Session):
    return db.query(Booking).all()


def create_guest(db: Session, guest_data: GuestCreate):
    existing_guest = check_guest_exists(db, guest_data)
    if existing_guest:
        raise ValueError("Guest with this email already exists")

    new_guest = Guest(
        first_name=guest_data.first_name,
        last_name=guest_data.last_name,
        email=guest_data.email,
        hashed_password=hash_password(guest_data.password),
        pays_dayrate=guest_data.pays_dayrate,
        is_admin=guest_data.is_admin,
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest


def update_booking(db: Session, booking_id: int, update_fields: dict):
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        return None
    for key, value in update_fields.items():
        setattr(booking, key, value)
    db.commit()
    db.refresh(booking)
    return booking
