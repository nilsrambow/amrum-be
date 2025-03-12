import datetime

import pytest
from sqlalchemy.orm import Session

from app.crud import create_booking
from app.models import Guest
from app.schemas import BookingCreate


def test_booking_guest_must_exist(db: Session):
    booking_data = BookingCreate(
        guest_id=999,
        check_in=datetime.date(2024, 6, 10),
        check_out=datetime.date(2024, 6, 15),
    )

    with pytest.raises(ValueError, match="Guest does not exist"):
        create_booking(db, booking_data)


def test_booking_invalid_dates(db: Session):
    """Should raise an error if check_out < check_in."""
    guest = Guest(
        first_name="Alice",
        last_name="Doe",
        email="alice@example.com",
        hashed_password="hashed_pw",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)

    booking_data = BookingCreate(
        guest_id=guest.id,
        check_in=datetime.date(2024, 6, 10),
        check_out=datetime.date(2024, 6, 5),  # Invalid check-out date
        status="confirmed",
    )

    with pytest.raises(ValueError, match="Check-out date must be after check-in date"):
        create_booking(db, booking_data)
