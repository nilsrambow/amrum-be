import pytest
from sqlalchemy.exc import IntegrityError

from app.guest_repository import GuestRepository
from app.models import Guest


def test_guest_repository_create(db_session):
    guest_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": "jane.doe@example.com",
        "hashed_password": "janes_encrypted_password",
    }
    guest_repository = GuestRepository(db_session)
    guest = guest_repository.create(guest_data)

    assert guest.first_name == guest_data["first_name"]

    assert guest.id is not None


def test_guest_repository_create_duplicate_email(db_session, test_guest):
    guest_data = {
        "first_name": "Jane",
        "last_name": "Doe",
        "email": test_guest.email,
        "hashed_password": "janes_encrypted_password",
    }
    guest_repository = GuestRepository(db_session)
    with pytest.raises(IntegrityError) as excinfo:
        guest_repository.create(guest_data)

    assert "UNIQUE constraint failed: guests.email" in str(excinfo.value)
    db_session.rollback()


def test_gest_repository_get_by_email(db_session, test_guest):
    repository = GuestRepository(db_session)
    retrieved_guest = repository.get_by_email(test_guest.email)

    assert retrieved_guest is not None
    assert retrieved_guest.id == test_guest.id
    assert retrieved_guest.email == test_guest.email


def test_gest_repository_get_by_email_nonexistent(db_session, test_guest):
    repository = GuestRepository(db_session)
    email = "nonexisting@email.domain"
    # with pytest.raises(IntegrityError) as excinfo:
    retrieved_guest = repository.get_by_email(email)
    assert retrieved_guest is None


def test_guest_repository_get_by_id(db_session, test_guest):
    repository = GuestRepository(db_session)
    retrieved_guest = repository.get_by_id(test_guest.id)

    assert retrieved_guest is not None


def test_guest_repository_get_by_id_nonexistent(db_session, test_guest):
    repository = GuestRepository(db_session)
    nonexisting_id = 9999
    retrieved_guest = repository.get_by_id(nonexisting_id)

    assert retrieved_guest is None


def test_guest_repository_update(db_session, test_guest):
    repository = GuestRepository(db_session)

    updated_email = "updated@email.address"
    test_guest.email = updated_email

    updated_guest = repository.update(test_guest)
    db_session.expunge_all()

    assert updated_guest.email == updated_email


def test_guest_repository_delete(db_session, test_guest):
    repository = GuestRepository(db_session)

    repository.delete(test_guest)

    deleted_guest = db_session.query(Guest).filter(Guest.id == test_guest.id).first()

    assert deleted_guest is None
