from datetime import datetime

from app.booking_repository import BookingRepository
from app.schemas import BookingCreate, BookingUpdate


class BookingService:
    def __init__(
        self, booking_repository: BookingRepository, guest_repository: GuestRepository
    ):
        self.booking_repository = (booking_repository,)
        self.guest_repository = guest_repository

    def create_booking(self, booking_data: BookingCreate):
        # TODO: Check if guest exists
        # TODO: validate booking dates
        booking_dict = booking_data.dict()
        return self.booking_repository.create(booking_dict)

    def get_all_bookings(self):
        return self.booking_repository.get_all()

    def get_booking_by_id(self, booking_id: int):
        booking = self.booking_repository.get_by_id(booking_id)
        if not booking:
            raise ValueError(f"Booking with ID {booking_id} not found ")
        return booking

    def confirm_booking(self, booking_id: int, booking_data: BookingUpdate):
        booking = self.get_booking_by_id(booking_id)
        for field, value in booking_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)
        # TODO: send notification
        booking.modified_at = datetime.utcnow()
        return self.booking_repository.update(booking)

        return None
