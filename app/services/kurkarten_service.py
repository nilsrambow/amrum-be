import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Booking, Guest
from app.services.communication_service import CommunicationService


class KurkartenService:
    def __init__(self, db: Session, communication_service: CommunicationService):
        self.db = db
        self.communication_service = communication_service
        self.dummy_kurkarten_url = "https://example.com/kurkarten-placeholder"
        self.agent_email = "booking-agent@example.com"  # Configure this
    
    def send_kurkarten_request_email(self, booking_id: int) -> bool:
        """Send kurkarten request email with dummy URL 25 days before arrival."""
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False
            
        guest = booking.guest
        if not guest:
            return False
        
        # TODO: Fetch real kurkarten URL from external service and use instead of dummy
        kurkarten_url = self.dummy_kurkarten_url  # This will be replaced with real URL fetch
        
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in_date": booking.check_in.strftime("%B %d, %Y"),
            "check_out_date": booking.check_out.strftime("%B %d, %Y"),
            "kurkarten_url": kurkarten_url,
            "subject": "Tourist Card Information Required"
        }
        
        try:
            self.communication_service.send_email(
                recipient=guest.email,
                subject="Tourist Card Information Required",
                template_name="kurkarten_request",
                context=context
            )
            
            # Update booking record
            booking.kurkarten_email_sent = True
            booking.kurkarten_email_sent_date = datetime.datetime.utcnow()
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"Failed to send kurkarten email: {e}")
            return False
    
    def send_pre_arrival_email(self, booking_id: int) -> bool:
        """Send pre-arrival info email 5 days before arrival."""
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False
            
        guest = booking.guest
        if not guest:
            return False
        
        # Check if kurkarten info has been added (we assume it's added if email was sent)
        if not booking.kurkarten_email_sent:
            # Send reminder to agent instead
            self._send_agent_reminder(
                booking, 
                "Kurkarten information missing - cannot send pre-arrival email",
                ["Kurkarten information not completed"]
            )
            return False
        
        # TODO: Fetch real kurkarten URL from external service
        kurkarten_url = self.dummy_kurkarten_url  # This will be replaced with real URL fetch
        
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in_date": booking.check_in.strftime("%B %d, %Y"),
            "check_out_date": booking.check_out.strftime("%B %d, %Y"),
            "kurtaxe_amount": booking.kurtaxe_amount,
            "kurkarten_url": kurkarten_url,
            "subject": "Pre-Arrival Information"
        }
        
        try:
            self.communication_service.send_email(
                recipient=guest.email,
                subject="Pre-Arrival Information",
                template_name="pre_arrival_info",
                context=context
            )
            
            # Update booking record
            booking.pre_arrival_email_sent = True
            booking.pre_arrival_email_sent_date = datetime.datetime.utcnow()
            self.db.commit()
            
            return True
        except Exception as e:
            print(f"Failed to send pre-arrival email: {e}")
            return False
    
    def _send_agent_reminder(self, booking: Booking, reason: str, missing_items: list = None):
        """Send reminder email to booking agent."""
        guest = booking.guest
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "guest_email": guest.email,
            "check_in_date": booking.check_in.strftime("%B %d, %Y"),
            "check_out_date": booking.check_out.strftime("%B %d, %Y"),
            "booking_id": booking.id,
            "reminder_reason": reason,
            "missing_items": missing_items or [],
            "subject": f"Action Required - Booking {booking.id}"
        }
        
        try:
            self.communication_service.send_email(
                recipient=self.agent_email,
                subject=f"Action Required - Booking {booking.id}",
                template_name="agent_reminder",
                context=context
            )
        except Exception as e:
            print(f"Failed to send agent reminder: {e}")
    
    def check_and_send_kurkarten_emails(self) -> int:
        """Check for bookings that need kurkarten emails (25 days before arrival)."""
        target_date = datetime.date.today() + datetime.timedelta(days=25)
        
        bookings = self.db.query(Booking).filter(
            Booking.confirmed == True,
            Booking.check_in == target_date,
            Booking.kurkarten_email_sent == False
        ).all()
        
        sent_count = 0
        for booking in bookings:
            if self.send_kurkarten_request_email(booking.id):
                sent_count += 1
        
        return sent_count
    
    def check_and_send_pre_arrival_emails(self) -> int:
        """Check for bookings that need pre-arrival emails (5 days before arrival)."""
        target_date = datetime.date.today() + datetime.timedelta(days=5)
        
        bookings = self.db.query(Booking).filter(
            Booking.confirmed == True,
            Booking.check_in == target_date,
            Booking.pre_arrival_email_sent == False
        ).all()
        
        sent_count = 0
        for booking in bookings:
            if self.send_pre_arrival_email(booking.id):
                sent_count += 1
        
        return sent_count 