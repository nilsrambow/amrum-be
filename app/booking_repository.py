from datetime import date

from sqlalchemy.orm import Session

from app.models import Booking


class BookingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, booking_data: dict) -> Booking:
        """Create a new booking in the database."""
        booking = Booking(**booking_data)
        self.db.add(booking)
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def get_by_id(self, booking_id: int) -> Booking:
        """Get a booking by ID."""
        return self.db.query(Booking).filter(Booking.id == booking_id).first()

    def get_all(self) -> list[Booking]:
        """Get all bookings."""
        return self.db.query(Booking).all()

    def update(self, booking: Booking) -> Booking:
        """Update a booking."""
        self.db.commit()
        self.db.refresh(booking)
        return booking

    def delete(self, booking: Booking) -> None:
        """Delete a booking."""
        self.db.delete(booking)
        self.db.commit()

    def get_by_guest_id(self, guest_id) -> list[Booking]:
        return self.db.query(Booking).filter(Booking.guest_id == guest_id).all()

    def get_by_date_range(self, start_date: date, end_date: date) -> list[Booking]:
        return (
            self.db.query(Booking)
            .filter(Booking.check_in <= end_date, Booking.check_out >= start_date)
            .all()
        )
