from datetime import date, timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.booking_repository import BookingRepository
from app.models import Booking


def test_booking_repository_create(db_session, test_guest):
    guest_id = test_guest.id
    check_in = date.today()
    check_out = date.today() + timedelta(days=5)
    booking_data = {
        "guest_id": guest_id,
        "check_in": check_in,
        "check_out": check_out,
    }
    booking_repository = BookingRepository(db_session)
    booking = booking_repository.create(booking_data)

    assert booking.check_in == booking_data["check_in"]

    assert booking.id is not None


def test_booking_repository_create_missing_guest(db_session, test_guest):
    guest_id = 9999
    check_in = date.today()
    check_out = date.today() + timedelta(days=5)
    booking_data = {
        "guest_id": guest_id,
        "check_in": check_in,
        "check_out": check_out,
    }
    booking_repository = BookingRepository(db_session)
    with pytest.raises(IntegrityError) as excinfo:
        booking_repository.create(booking_data)

    assert "FOREIGN KEY constraint failed" in str(excinfo.value)
    db_session.rollback()


def test_booking_repository_get_by_guest_id(db_session, test_booking, test_guest):
    repository = BookingRepository(db_session)
    retrieved_bookings_list = repository.get_by_guest_id(test_guest.id)

    assert len(retrieved_bookings_list) > 0
    assert retrieved_bookings_list[0].check_in == test_booking.check_in


#
# def test_gest_repository_get_by_email_nonexistent(db_session, test_booking):
#     repository = BookingRepository(db_session)
#     email = "nonexisting@email.domain"
#     # with pytest.raises(IntegrityError) as excinfo:
#     retrieved_booking = repository.get_by_email(email)
#     assert retrieved_booking is None
#
#
def test_booking_repository_get_by_id(db_session, test_booking):
    repository = BookingRepository(db_session)
    retrieved_booking = repository.get_by_id(test_booking.id)

    assert retrieved_booking is not None


def test_booking_repository_get_by_id_nonexistent(db_session, test_booking):
    repository = BookingRepository(db_session)
    nonexisting_id = 9999
    retrieved_booking = repository.get_by_id(nonexisting_id)

    assert retrieved_booking is None


def test_booking_repository_update(db_session, test_booking):
    repository = BookingRepository(db_session)

    updated_check_in = date.today() - timedelta(days=10)
    test_booking.check_in = updated_check_in

    updated_booking = repository.update(test_booking)
    db_session.expunge_all()

    assert updated_booking.check_in == updated_check_in


def test_booking_repository_delete(db_session, test_booking):
    repository = BookingRepository(db_session)

    repository.delete(test_booking)

    deleted_booking = (
        db_session.query(Booking).filter(Booking.id == test_booking.id).first()
    )

    assert deleted_booking is None
