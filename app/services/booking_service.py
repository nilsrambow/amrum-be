from datetime import datetime, date, timedelta

from app.booking_repository import BookingRepository
from app.guest_repository import GuestRepository
from app.schemas import BookingCreate, BookingUpdate, BookingPartialUpdate
from app.services.communication_service import CommunicationService
from app.services.booking_status_service import BookingStatusService
from app.services.token_service import TokenService


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
        self.status_service = BookingStatusService(booking_repository.db)

    def create_booking(self, booking_data: BookingCreate):
        # Validate booking dates
        self._validate_booking_dates(booking_data)
        
        # Check for overlapping bookings
        self._check_booking_overlap(booking_data)
        
        # TODO: Check if guest exists
        booking_dict = booking_data.dict()
        booking = self.booking_repository.create(booking_dict)
        
        # Update status after creation
        self.status_service.update_booking_status(booking)
        
        # Generate access token for guest
        token_service = TokenService(self.booking_repository.db)
        token_service.generate_token(booking.id)
        
        return booking

    def _validate_booking_dates(self, booking_data: BookingCreate):
        """Validate booking dates."""
        if booking_data.check_in >= booking_data.check_out:
            raise ValueError("Check-out date must be after check-in date")
        
        if booking_data.check_in < date.today():
            pass # not active for now for better manual testing
            #raise ValueError("Check-in date cannot be in the past")

    def _check_booking_overlap(self, booking_data: BookingCreate):
        """Check if the booking dates overlap with existing bookings."""
        # Find any existing bookings that overlap with the new booking
        # Overlap occurs when:
        # - New check-in is before existing check-out AND new check-out is after existing check-in
        overlapping_bookings = self.booking_repository.db.query(
            self.booking_repository.model
        ).filter(
            # Check if the new booking overlaps with any existing booking
            self.booking_repository.model.check_in < booking_data.check_out,
            self.booking_repository.model.check_out > booking_data.check_in
        ).all()
        
        if overlapping_bookings:
            # Get details of overlapping bookings for the error message
            overlap_details = []
            for booking in overlapping_bookings:
                guest = self.guest_repository.get_by_id(booking.guest_id)
                guest_name = f"{guest.first_name} {guest.last_name}" if guest else f"Guest {booking.guest_id}"
                overlap_details.append({
                    "booking_id": booking.id,
                    "guest_name": guest_name,
                    "check_in": booking.check_in.strftime("%Y-%m-%d"),
                    "check_out": booking.check_out.strftime("%Y-%m-%d")
                })
            
            # Create a meaningful error message
            error_msg = "Booking dates overlap with existing bookings:\n"
            for overlap in overlap_details:
                error_msg += f"- Booking {overlap['booking_id']} ({overlap['guest_name']}): {overlap['check_in']} to {overlap['check_out']}\n"
            
            raise ValueError(error_msg.strip())

    def get_all_bookings(self):
        bookings = self.booking_repository.get_all()
        
        # Update status for all bookings
        for booking in bookings:
            self.status_service.update_booking_status(booking)
        
        return bookings

    def get_booking_by_id(self, booking_id: int):
        booking = self.booking_repository.get_by_id(booking_id)
        if not booking:
            raise ValueError(f"Booking with ID {booking_id} not found ")
        
        # Update status
        self.status_service.update_booking_status(booking)
        
        return booking

    def get_booking_by_id_with_invoice(self, booking_id: int):
        """Get a booking by ID with calculated invoice details."""
        booking = self.booking_repository.get_by_id(booking_id)
        if not booking:
            raise ValueError(f"Booking with ID {booking_id} not found")
        
        # Update status
        self.status_service.update_booking_status(booking)
        
        # Calculate invoice details
        from app.services.invoice_service import InvoiceService
        from app.services.meter_service import MeterService
        from app.config.config import get_email_config
        
        # Create temporary services for calculation
        email_config = get_email_config()
        meter_service = MeterService(self.booking_repository.db)
        invoice_service = InvoiceService(self.booking_repository.db, None, meter_service)
        
        try:
            invoice_data = invoice_service._calculate_invoice_amounts(booking)
            booking.invoice_details = invoice_data
        except Exception as e:
            # If invoice calculation fails, set empty details
            booking.invoice_details = {
                'accommodation_cost': 0,
                'electricity_cost': 0,
                'gas_cost': 0,
                'firewood_cost': 0,
                'kurtaxe_cost': 0,
                'total_cost': 0,
                'consumption': {},
                'num_days': (booking.check_out - booking.check_in).days
            }
        
        return booking

    def update_booking(self, booking_id: int, booking_data: BookingUpdate):
        booking = self.get_booking_by_id(booking_id)
        for field, value in booking_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)
        booking.modified_at = datetime.utcnow()
        
        # Update status after modification
        self.status_service.update_booking_status(booking)
        
        return self.booking_repository.update(booking)

    def update_booking_partial(self, booking_id: int, booking_data: BookingPartialUpdate):
        """Update a booking and reset all system-managed fields to initial state."""
        booking = self.get_booking_by_id(booking_id)
        
        # If dates are being updated, validate them and check for overlaps
        if booking_data.check_in is not None or booking_data.check_out is not None:
            # Create a temporary booking object with updated dates for validation
            temp_check_in = booking_data.check_in if booking_data.check_in is not None else booking.check_in
            temp_check_out = booking_data.check_out if booking_data.check_out is not None else booking.check_out
            
            # Validate dates
            if temp_check_in >= temp_check_out:
                raise ValueError("Check-out date must be after check-in date")
            
            # Check for overlaps (excluding the current booking)
            self._check_booking_overlap_for_update(booking_id, temp_check_in, temp_check_out)
        
        # Update the provided fields
        for field, value in booking_data.dict(exclude_unset=True).items():
            setattr(booking, field, value)
        
        # Reset all system-managed fields to initial state
        booking.confirmed = False
        booking.final_info_sent = False
        booking.invoice_created = False
        booking.invoice_sent = False
        booking.paid = False
        booking.kurkarten_email_sent = False
        booking.kurkarten_email_sent_date = None
        booking.pre_arrival_email_sent = False
        booking.pre_arrival_email_sent_date = None
        booking.kurtaxe_amount = None
        booking.kurtaxe_notes = None
        booking.invoice_id = None
        booking.invoice_sent_date = None
        
        # Update the modified timestamp
        booking.modified_at = datetime.utcnow()
        
        # Clear related data (meter readings and payments)
        self._clear_booking_related_data(booking_id)
        
        # Update status after reset
        self.status_service.update_booking_status(booking)
        
        return self.booking_repository.update(booking)

    def _check_booking_overlap_for_update(self, booking_id: int, check_in: datetime.date, check_out: datetime.date):
        """Check if the updated booking dates overlap with other existing bookings."""
        # Find any existing bookings that overlap with the updated booking (excluding the current booking)
        overlapping_bookings = self.booking_repository.db.query(
            self.booking_repository.model
        ).filter(
            self.booking_repository.model.id != booking_id,  # Exclude current booking
            # Check if the updated booking overlaps with any other booking
            self.booking_repository.model.check_in < check_out,
            self.booking_repository.model.check_out > check_in
        ).all()
        
        if overlapping_bookings:
            # Get details of overlapping bookings for the error message
            overlap_details = []
            for booking in overlapping_bookings:
                guest = self.guest_repository.get_by_id(booking.guest_id)
                guest_name = f"{guest.first_name} {guest.last_name}" if guest else f"Guest {booking.guest_id}"
                overlap_details.append({
                    "booking_id": booking.id,
                    "guest_name": guest_name,
                    "check_in": booking.check_in.strftime("%Y-%m-%d"),
                    "check_out": booking.check_out.strftime("%Y-%m-%d")
                })
            
            # Create a meaningful error message
            error_msg = "Updated booking dates overlap with existing bookings:\n"
            for overlap in overlap_details:
                error_msg += f"- Booking {overlap['booking_id']} ({overlap['guest_name']}): {overlap['check_in']} to {overlap['check_out']}\n"
            
            raise ValueError(error_msg.strip())

    def _clear_booking_related_data(self, booking_id: int):
        """Clear meter readings and payments for a booking."""
        from app.models import MeterReading, Payment
        from app.database import get_db
        
        db = next(get_db())
        
        # Delete meter readings
        db.query(MeterReading).filter(MeterReading.booking_id == booking_id).delete()
        
        # Delete payments
        db.query(Payment).filter(Payment.booking_id == booking_id).delete()
        
        db.commit()

    def check_and_confirm_bookings(self, auto_confirm_delay_hours: int = 36) -> int:
        """Check for bookings that need automatic confirmation."""
        from datetime import datetime, timedelta
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=auto_confirm_delay_hours)
        
        # Find bookings that haven't been confirmed and were last modified before cutoff
        bookings_to_confirm = self.booking_repository.db.query(
            self.booking_repository.model
        ).filter(
            self.booking_repository.model.confirmed == False,
            self.booking_repository.model.modified_at <= cutoff_time
        ).all()
        
        confirmed_count = 0
        for booking in bookings_to_confirm:
            try:
                self.confirm_booking(booking.id)
                confirmed_count += 1
            except Exception as e:
                print(f"Failed to confirm booking {booking.id}: {e}")
        
        return confirmed_count

    def confirm_booking(self, booking_id: int):
        booking_update = BookingUpdate(confirmed=True)
        updated_booking = self.update_booking(booking_id, booking_update)
        guest = self.guest_repository.get_by_id(guest_id=updated_booking.guest_id)
        self._send_booking_confirmation(updated_booking, guest)
        
        # Update status specifically for confirmation
        self.status_service.update_status_on_confirmation(updated_booking)
        
        return updated_booking

    def _send_booking_confirmation(
        self, booking: BookingRepository, guest: GuestRepository
    ):
        # Get the access token for this booking
        token_service = TokenService(self.booking_repository.db)
        token_info = token_service.get_token_info(booking.id)
        
        # Send confirmation email with magic link
        self.communication_service.send_booking_confirmation_email(
            booking=booking,
            guest=guest,
            token=token_info.token if token_info else None
        )
