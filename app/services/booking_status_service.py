import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Booking, BookingStatus


class BookingStatusService:
    def __init__(self, db: Session):
        self.db = db
    
    def update_booking_status(self, booking: Booking) -> BookingStatus:
        """Update booking status based on current state and dates."""
        today = datetime.date.today()
        
        # First, check workflow state (priority over dates)
        if not booking.confirmed:
            # If not confirmed, always stay NEW regardless of dates
            new_status = BookingStatus.NEW
        elif booking.pre_arrival_email_sent:
            # Pre-arrival email sent - check if we're at arrival date or later
            if booking.check_in == today:
                new_status = BookingStatus.ARRIVING
            elif booking.check_in < today and booking.check_out > today:
                new_status = BookingStatus.ON_SITE
            elif booking.check_out == today:
                new_status = BookingStatus.DEPARTING
            elif booking.check_out < today:
                # Post-departure workflow
                if booking.paid:
                    new_status = BookingStatus.DEPARTED_DONE
                elif booking.invoice_sent:
                    new_status = BookingStatus.DEPARTED_PAYMENT_DUE
                elif booking.invoice_created:
                    new_status = BookingStatus.DEPARTED_INVOICE_DUE
                elif booking.meter_readings:
                    new_status = BookingStatus.DEPARTED_INVOICE_DUE
                else:
                    new_status = BookingStatus.DEPARTED_READINGS_DUE
            else:
                new_status = BookingStatus.READY_FOR_ARRIVAL
        elif booking.kurkarten_email_sent:
            # Kurkarten email sent but pre-arrival not sent yet
            new_status = BookingStatus.KURKARTEN_REQUESTED
        else:
            # Confirmed but no emails sent yet
            new_status = BookingStatus.CONFIRMED
        
        # Update the booking status if it changed
        if booking.status != new_status:
            booking.status = new_status
            booking.modified_at = datetime.datetime.utcnow()
            self.db.commit()
        
        return new_status
    
    def update_status_on_confirmation(self, booking: Booking) -> BookingStatus:
        """Update status when booking is confirmed."""
        booking.confirmed = True
        booking.status = BookingStatus.CONFIRMED
        booking.modified_at = datetime.datetime.utcnow()
        self.db.commit()
        return booking.status
    
    def update_status_on_kurkarten_sent(self, booking: Booking) -> BookingStatus:
        """Update status when kurkarten email is sent."""
        booking.kurkarten_email_sent = True
        booking.kurkarten_email_sent_date = datetime.datetime.utcnow()
        booking.status = BookingStatus.KURKARTEN_REQUESTED
        booking.modified_at = datetime.datetime.utcnow()
        self.db.commit()
        return booking.status
    
    def update_status_on_pre_arrival_sent(self, booking: Booking) -> BookingStatus:
        """Update status when pre-arrival email is sent."""
        booking.pre_arrival_email_sent = True
        booking.pre_arrival_email_sent_date = datetime.datetime.utcnow()
        booking.status = BookingStatus.READY_FOR_ARRIVAL
        booking.modified_at = datetime.datetime.utcnow()
        self.db.commit()
        return booking.status
    
    def update_status_on_readings_added(self, booking: Booking) -> BookingStatus:
        """Update status when meter readings are added."""
        # Check if we're in post-departure phase
        if booking.check_out < datetime.date.today():
            booking.status = BookingStatus.DEPARTED_INVOICE_DUE
            booking.modified_at = datetime.datetime.utcnow()
            self.db.commit()
        return booking.status
    
    def update_status_on_invoice_created(self, booking: Booking) -> BookingStatus:
        """Update status when invoice is created."""
        # Check if we're in post-departure phase
        if booking.check_out < datetime.date.today():
            booking.status = BookingStatus.DEPARTED_INVOICE_DUE
            booking.modified_at = datetime.datetime.utcnow()
            self.db.commit()
        return booking.status
    
    def update_status_on_invoice_sent(self, booking: Booking) -> BookingStatus:
        """Update status when invoice is sent."""
        # Check if we're in post-departure phase
        if booking.check_out < datetime.date.today():
            booking.status = BookingStatus.DEPARTED_PAYMENT_DUE
            booking.modified_at = datetime.datetime.utcnow()
            self.db.commit()
        return booking.status
    
    def update_status_on_payment_received(self, booking: Booking) -> BookingStatus:
        """Update status when payment is received."""
        # Check if we're in post-departure phase
        if booking.check_out < datetime.date.today():
            booking.status = BookingStatus.DEPARTED_DONE
            booking.modified_at = datetime.datetime.utcnow()
            self.db.commit()
        return booking.status
    
    def update_all_booking_statuses(self) -> int:
        """Update status for all bookings based on current state."""
        bookings = self.db.query(Booking).all()
        updated_count = 0
        
        for booking in bookings:
            old_status = booking.status
            new_status = self.update_booking_status(booking)
            if old_status != new_status:
                updated_count += 1
        
        return updated_count 