import datetime
import secrets
from typing import Optional

from sqlalchemy.orm import Session

from app.models import Booking, BookingToken
from app.schemas import BookingTokenResponse, GuestBookingResponse, WastePickupResponse
from app.services import waste_service


class TokenService:
    def __init__(self, db: Session):
        self.db = db

    def generate_token(self, booking_id: int, expiry_months: int = 3) -> str:
        """Generate a secure token for guest access to a booking"""
        # Generate a cryptographically secure token
        token = secrets.token_urlsafe(32)
        
        # Calculate expiry date (3 months after departure by default)
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            raise ValueError(f"Booking {booking_id} not found")
        
        # Use departure date + expiry_months, or current date + 3 months if no departure date
        base_date = booking.check_out or datetime.date.today()
        expiry_date = datetime.datetime.combine(
            base_date, 
            datetime.time.min
        ) + datetime.timedelta(days=expiry_months * 30)
        
        # Create token record
        booking_token = BookingToken(
            booking_id=booking_id,
            token=token,
            expires_at=expiry_date
        )
        
        self.db.add(booking_token)
        self.db.commit()
        self.db.refresh(booking_token)
        
        # Update booking with token info
        booking.access_token = token
        booking.token_expires_at = expiry_date
        self.db.commit()
        
        return token

    def validate_token(self, token: str) -> Optional[Booking]:
        """Validate a token and return the associated booking if valid"""
        booking_token = self.db.query(BookingToken).filter(
            BookingToken.token == token,
            BookingToken.expires_at > datetime.datetime.utcnow()
        ).first()
        
        if not booking_token:
            return None
        
        # Update last used timestamp
        booking_token.last_used_at = datetime.datetime.utcnow()
        self.db.commit()
        
        return booking_token.booking

    def get_booking_by_token(self, token: str) -> Optional[GuestBookingResponse]:
        """Get booking details for guest access via token"""
        booking = self.validate_token(token)
        if not booking:
            return None
        
        # Get invoice details from persisted snapshot if available
        invoice_details = None
        if booking.invoice_created and booking.invoice_snapshot:
            from app.services.invoice_service import InvoiceService
            invoice_service = InvoiceService(self.db, None, None)
            invoice_details = invoice_service._invoice_data_from_snapshot(booking.invoice_snapshot)
        
        waste_pickups = self._get_waste_pickups(booking)

        return GuestBookingResponse(
            id=booking.id,
            check_in=booking.check_in,
            check_out=booking.check_out,
            confirmed=booking.confirmed,
            status=booking.status,
            kurtaxe_amount=booking.kurtaxe_amount,
            kurtaxe_notes=booking.kurtaxe_notes,
            created_at=booking.created_at,
            guest_first_name=booking.guest.first_name,
            meter_readings=booking.meter_readings,
            payments=booking.payments,
            invoice_details=invoice_details,
            waste_pickups=waste_pickups
        )

    def _get_waste_pickups(self, booking: Booking) -> Optional[list]:
        """Waste collections the guest has to put bins out for, None if unknown."""
        # The window depends on whether the next guest arrives right away
        next_booking = (
            self.db.query(Booking)
            .filter(
                Booking.id != booking.id,
                Booking.confirmed == True,
                Booking.check_in >= booking.check_out,
            )
            .order_by(Booking.check_in)
            .first()
        )
        pickups = waste_service.pickups_for_stay(
            booking.check_in,
            booking.check_out,
            next_booking.check_in if next_booking else None,
        )
        if pickups is None:
            return None
        one_day = datetime.timedelta(days=1)
        return [
            WastePickupResponse(date=p.date, put_out_date=p.date - one_day, bin_type=p.bin_type)
            for p in pickups
        ]

    def revoke_token(self, booking_id: int) -> bool:
        """Revoke all tokens for a booking"""
        tokens = self.db.query(BookingToken).filter(BookingToken.booking_id == booking_id).all()
        for token in tokens:
            self.db.delete(token)
        
        # Clear token info from booking
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            booking.access_token = None
            booking.token_expires_at = None
        
        self.db.commit()
        return True

    def get_token_info(self, booking_id: int) -> Optional[BookingTokenResponse]:
        """Get token information for a booking"""
        token = self.db.query(BookingToken).filter(
            BookingToken.booking_id == booking_id
        ).order_by(BookingToken.created_at.desc()).first()
        
        if not token:
            return None
        
        return BookingTokenResponse(
            token=token.token,
            expires_at=token.expires_at,
            created_at=token.created_at,
            last_used_at=token.last_used_at
        ) 