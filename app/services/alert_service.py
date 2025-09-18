import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models import Booking
from app.services.kurkarten_service import KurkartenService
from app.services.invoice_service import InvoiceService


class AlertService:
    def __init__(self, db: Session):
        self.db = db
    
    @classmethod
    def get_kurkarten_response_delay_days(cls) -> int:
        """Get the number of days to wait for kurkarten response after email sent."""
        return 5
    
    @classmethod
    def get_readings_delay_days(cls) -> int:
        """Get the number of days after departure to expect meter readings."""
        return 3
    
    @classmethod
    def get_payment_delay_days(cls) -> int:
        """Get the number of days after invoice sent to expect payment."""
        return 14
    
    def get_pending_emails(self) -> Dict[str, Any]:
        """Get all pending email alerts calculated on the fly."""
        emails = []
        email_id = 1
        
        # 1. Check for pending booking confirmations
        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=36)
        pending_confirmations = self.db.query(Booking).filter(
            Booking.confirmed == False,
            Booking.modified_at <= cutoff_time
        ).all()
        
        for booking in pending_confirmations:
            emails.append({
                "id": email_id,
                "booking_id": booking.id,
                "email_type": "booking_confirmation"
            })
            email_id += 1
        
        # 2. Check for kurkarten emails (25 days before arrival)
        pending_kurkarten = KurkartenService.get_pending_kurkarten_bookings(self.db)
        
        for booking in pending_kurkarten:
            emails.append({
                "id": email_id,
                "booking_id": booking.id,
                "email_type": "kurkarten_request"
            })
            email_id += 1
        
        # 3. Check for pre-arrival emails (5 days before arrival)
        pending_pre_arrival = KurkartenService.get_pending_pre_arrival_bookings(self.db)
        
        for booking in pending_pre_arrival:
            emails.append({
                "id": email_id,
                "booking_id": booking.id,
                "email_type": "pre_arrival_info"
            })
            email_id += 1
        
        # 4. Check for invoice generation (3 days after departure)
        pending_invoices = InvoiceService.get_pending_invoice_bookings(self.db)
        
        for booking in pending_invoices:
            emails.append({
                "id": email_id,
                "booking_id": booking.id,
                "email_type": "invoice_generation"
            })
            email_id += 1
        
        return {
            "total_count": len(emails),
            "emails": emails
        }
    
    def get_outstanding_guest_actions(self) -> Dict[str, Any]:
        """Get all outstanding guest actions that need attention."""
        actions = []
        action_id = 1
        
        # 1. Check for missing kurkarten data (kurkarten email sent >5 days ago but kurtaxe_amount is empty)
        kurkarten_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=self.get_kurkarten_response_delay_days())
        missing_kurkarten = self.db.query(Booking).filter(
            Booking.kurkarten_email_sent == True,
            Booking.kurkarten_email_sent_date <= kurkarten_cutoff,
            (Booking.kurtaxe_amount.is_(None) | (Booking.kurtaxe_amount == 0))
        ).all()
        
        for booking in missing_kurkarten:
            actions.append({
                "id": action_id,
                "booking_id": booking.id,
                "action_type": "missing_kurkarten_data"
            })
            action_id += 1
        
        # 2. Check for missing readings (departure >3 days ago but no meter readings)
        # Only for bookings that have been through the proper workflow
        readings_cutoff = datetime.date.today() - datetime.timedelta(days=self.get_readings_delay_days())
        missing_readings = self.db.query(Booking).filter(
            Booking.confirmed == True,  # Must be confirmed
            Booking.pre_arrival_email_sent == True,  # Must have gone through the workflow
            Booking.check_out <= readings_cutoff,  # Departed more than 3 days ago
            ~Booking.meter_readings.has()  # No meter readings exist (scalar relationship)
        ).all()
        
        for booking in missing_readings:
            actions.append({
                "id": action_id,
                "booking_id": booking.id,
                "action_type": "missing_readings"
            })
            action_id += 1
        
        # 3. Check for missing payment (invoice sent >14 days ago but no payment registered)
        payment_cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=self.get_payment_delay_days())
        missing_payments = self.db.query(Booking).filter(
            Booking.invoice_sent == True,
            Booking.invoice_sent_date <= payment_cutoff,
            ~Booking.payments.any()  # No payments exist (collection relationship)
        ).all()
        
        for booking in missing_payments:
            actions.append({
                "id": action_id,
                "booking_id": booking.id,
                "action_type": "missing_payment"
            })
            action_id += 1
        
        return {
            "total_count": len(actions),
            "actions": actions
        } 