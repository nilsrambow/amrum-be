from datetime import datetime

from app.booking_repository import BookingRepository
from app.guest_repository import GuestRepository
from app.schemas import BookingCreate, BookingUpdate
from app.services.communication_service import CommunicationService


class BookingService:
    def __init__(
        self,
        booking_repository: BookingRepository,
        guest_repository: GuestRepository,
        communication_service: CommunicationService,
    ):
        self.booking_repository = booking_repository
        self.guest_repository = guest_repository
        self.communication_service = communication_service

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

    def update_booking(self, booking_id: int, booking_data: BookingUpdate):
        booking = self.get_booking_by_id(booking_id)
        for field, value in booking_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)
        booking.modified_at = datetime.utcnow()
        return self.booking_repository.update(booking)

    def confirm_booking(self, booking_id: int):
        # TODO send notification
        booking_update = BookingUpdate(confirmed=True)
        updated_booking = self.update_booking(booking_id, booking_update)
        guest = self.guest_repository.get_by_id(guest_id=updated_booking.guest_id)
        self._send_booking_confirmation(updated_booking, guest)
        return updated_booking

    def _send_booking_confirmation(
        self, booking: BookingRepository, guest: GuestRepository
    ):
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in": booking.check_in.strftime("%Y-%m-%d"),
            "check_out": booking.check_out.strftime("%Y-%m-%d"),
            "booking_id": booking.id,
            "property_name": "Your Beautiful House",
        }
        self.communication_service.send_email(
            recipient=guest.email,
            subject="Booking confirmation",
            template_name="bkg_confirmation_template",
            context=context,
        )
        pass
