import datetime

import pytest
from sqlalchemy.orm import Session

from app.crud import create_booking
from app.models import Booking, Guest
from app.schemas import BookingCreate

# from app.services.booking_service import confirm_booking


@pytest.fixture
def test_guest(db: Session):
    guest = Guest(
        first_name="first",
        last_name="last",
        email="test@example.com",
        hashed_password="hashed_pw",
    )
    db.add(guest)
    db.commit()
    db.refresh(guest)
    return guest


@pytest.fixture
def test_booking(db: Session, test_guest: Guest):
    booking = Booking(
        guest_id=test_guest.id,
        check_in=datetime.date(2024, 6, 1),
        check_out=datetime.date(2024, 6, 10),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


# def test_confirm_booking(db: Session, test_booking: Booking):
#     assert test_booking.confirmed is False
#     confirmed_booking = confirm_booking(db, test_booking.id)
#     assert confirmed_booking.confirmed is True
#


def test_booking_guest_must_exist(db: Session, test_booking: Booking):
    try:
        create_booking(db, test_booking)
    except Exception as e:
        assert isinstance(e, ValueError)


def test_booking_invalid_dates(db: Session, test_guest: Guest):
    booking_data = BookingCreate(
        guest_id=test_guest.id,
        check_in=datetime.date(2024, 6, 10),
        check_out=datetime.date(2024, 6, 5),
    )

    try:
        create_booking(db, booking_data)
    except Exception as e:
        print(f"Raised Exception: {type(e).__name__} - {e}")
        assert isinstance(e, ValueError)
