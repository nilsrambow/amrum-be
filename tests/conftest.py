from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import Booking, Guest
from main import app


@pytest.fixture
def test_db_engine():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    # Enable foreign key constraints for SQLite
    from sqlalchemy import event

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine

    Base.metadata.drop_all(bind=engine)  # teardown part


@pytest.fixture
def db_session(test_db_engine):
    TestingSessionLocal = sessionmaker(bind=test_db_engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_ovrrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_ovrrides.clear()


@pytest.fixture
def test_guest(db_session):
    guest = Guest(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        hashed_password="encrypted_password",
    )

    db_session.add(guest)
    db_session.commit()
    db_session.refresh(guest)

    yield guest

    db_session.delete(guest)
    db_session.commit()


@pytest.fixture
def test_booking(db_session, test_guest):
    booking = Booking(
        guest_id=test_guest.id,
        check_in=date.today(),
        check_out=date.today(),
    )
    db_session.add(booking)
    db_session.commit()
    db_session.refresh(booking)

    yield booking

    db_session.delete(booking)
    db_session.commit()
