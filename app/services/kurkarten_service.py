import datetime
import re
from typing import Optional, List
from sqlalchemy.orm import Session
import httpx

from app.models import Booking, Guest
from app.services.communication_service import CommunicationService
from app.services.booking_status_service import BookingStatusService
from app.config.config import get_kurkarten_config


def extract_url_group_from_html(html: str, pattern: str) -> str:
    """
    Extract URL from HTML using a regex pattern.
    
    Args:
        html: HTML string to search
        pattern: Regex pattern with a capturing group for the URL
        
    Returns:
        The extracted URL string
        
    Raises:
        ValueError: If the URL pattern is not found in the HTML
    """
    match = re.search(pattern, html)
    if not match:
        raise ValueError(f"URL pattern not found in HTML response")
    
    # Return the first capturing group (the URL)
    if match.groups():
        return match.group(1)
    else:
        raise ValueError("Regex pattern must contain a capturing group for the URL")


class KurkartenService:
    def __init__(self, db: Session, communication_service: CommunicationService):
        self.db = db
        self.communication_service = communication_service
        self.status_service = BookingStatusService(db)
        self.dummy_kurkarten_url = "https://example.com/kurkarten-placeholder"
        self.agent_email = "booking-agent@example.com"  # Configure this
    
    @classmethod
    def get_kurkarten_delay_days(cls) -> int:
        """Get the number of days before arrival to send kurkarten emails."""
        return 25
    
    @classmethod
    def get_pending_kurkarten_bookings(cls, db: Session) -> List[Booking]:
        """Get all bookings that need kurkarten emails sent."""
        target_date = datetime.date.today() + datetime.timedelta(days=cls.get_kurkarten_delay_days())
        
        return db.query(Booking).filter(
            Booking.confirmed == True,
            Booking.check_in <= target_date,
            Booking.kurkarten_email_sent == False
        ).all()
    
    @classmethod
    def get_pre_arrival_delay_days(cls) -> int:
        """Get the number of days before arrival to send pre-arrival emails."""
        return 5
    
    @classmethod
    def get_pending_pre_arrival_bookings(cls, db: Session) -> List[Booking]:
        """Get all bookings that need pre-arrival emails sent."""
        target_date = datetime.date.today() + datetime.timedelta(days=cls.get_pre_arrival_delay_days())
        
        return db.query(Booking).filter(
            Booking.confirmed == True,
            Booking.check_in <= target_date,
            Booking.pre_arrival_email_sent == False
        ).all()
    
    def send_kurkarten_request_email(self, booking_id: int) -> bool:
        """Send kurkarten request email with real URL fetched from external service 25 days before arrival."""
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return False
            
        guest = booking.guest
        if not guest:
            return False
        
        # Fetch real kurkarten URL from external service
        try:
            kurkarten_url = self._fetch_kurkarten_url(guest.email)
        except Exception as e:
            print(f"Failed to fetch kurkarten URL for booking {booking_id}: {e}")
            return False
        
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
            
            # Update booking record and status
            self.status_service.update_status_on_kurkarten_sent(booking)
            
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
        
        # Get the access token for this booking
        from app.services.token_service import TokenService
        token_service = TokenService(self.db)
        token_info = token_service.get_token_info(booking.id)
        
        # Format arrival date for subject line
        arrival_date_formatted = booking.check_in.strftime('%d. %m.')
        
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in_date": booking.check_in.strftime("%B %d, %Y"),
            "check_out_date": booking.check_out.strftime("%B %d, %Y"),
            "kurtaxe_amount": booking.kurtaxe_amount,
            "subject": f"Haus B: Letzte Infos vor Deiner Anreise am {arrival_date_formatted}"
        }
        
        # Add magic link if token is available
        if token_info:
            magic_link = self.communication_service.generate_magic_link(token_info.token)
            context["magic_link"] = magic_link
            context["has_magic_link"] = True
        else:
            context["has_magic_link"] = False
        
        try:
            self.communication_service.send_email(
                recipient=guest.email,
                subject=context["subject"],
                template_name="pre_arrival_info",
                context=context
            )
            
            # Update booking record and status
            self.status_service.update_status_on_pre_arrival_sent(booking)
            
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
    
    def _fetch_kurkarten_url(self, guest_email: str) -> str:
        """
        Fetch kurkarten URL from external AVS service.
        
        Args:
            guest_email: Email address of the guest
            
        Returns:
            The kurkarten URL string
            
        Raises:
            Exception: If URL fetching fails (network error, authentication failure, etc.)
        """
        config = get_kurkarten_config()
        
        # Validate that all required config values are present
        if not all([config.get("kennung"), config.get("passwort"), config.get("ort"), config.get("hotel")]):
            raise ValueError("Missing required kurkarten configuration. Please set KURKARTEN_KENNUNG, KURKARTEN_PASSWORT, KURKARTEN_ORT, and KURKARTEN_HOTEL environment variables.")
        
        base_url = "https://meldeschein.avs.de"
        login_url = f"{base_url}/amrum/login.do"
        form_action_url = f"{base_url}/amrum/createGastlink.do"
        
        login_data = {
            "event": "verifyLogin",
            "target": "success",
            "kennung": config["kennung"],
            "passwort": config["passwort"],
            "ort": config["ort"],
            "hotel": config["hotel"],
        }
        
        form_data = {
            "event": "Submit",
            "value(GastEmail)": guest_email,
            "value(ObjektBezeichnung)": "Brodersen-153031",
            "value(ObjektId)": "412",
            "value(hiddenFirmaName)": "Brodersen, Nils-153031",
            "value(hiddenFirmaId)": "387",
        }
        
        # Configure timeouts: connect (5s), read (30s), write (10s)
        # This ensures we wait long enough for the external API to respond
        timeout = httpx.Timeout(
            connect=5.0,  # Time to establish connection
            read=30.0,     # Time to read response data (allows for slow API responses)
            write=10.0,    # Time to write request data
            pool=5.0       # Time to get connection from pool
        )
        
        try:
            with httpx.Client(timeout=timeout, follow_redirects=True) as client:
                # Authenticate with the service
                login_response = client.post(login_url, data=login_data)
                login_response.raise_for_status()
                
                # Create guest link
                form_response = client.post(form_action_url, data=form_data)
                form_response.raise_for_status()
                
                # Extract URL from response HTML
                html_string = form_response.text
                match_string = r"copyToClipboard\('(?P<url>https://meldeschein\.avs\.de/precheckin/index\.xhtml\?hash=[a-f0-9]+)'\)"
                kurkarten_url = extract_url_group_from_html(html_string, match_string)
                
                return kurkarten_url
        except httpx.TimeoutException as e:
            raise Exception(f"Timeout while fetching kurkarten URL: {e}. The external service may be slow or unavailable.")
        except httpx.HTTPError as e:
            raise Exception(f"HTTP error while fetching kurkarten URL: {e}")
        except ValueError as e:
            raise Exception(f"Failed to extract kurkarten URL from response: {e}")
        except Exception as e:
            raise Exception(f"Unexpected error while fetching kurkarten URL: {e}")
    
    def check_and_send_kurkarten_emails(self) -> int:
        """Check for bookings that need kurkarten emails (25 days before arrival)."""
        bookings = self.get_pending_kurkarten_bookings(self.db)
        
        sent_count = 0
        for booking in bookings:
            if self.send_kurkarten_request_email(booking.id):
                sent_count += 1
        
        return sent_count
    
    def check_and_send_pre_arrival_emails(self) -> int:
        """Check for bookings that need pre-arrival emails (5 days before arrival)."""
        bookings = self.get_pending_pre_arrival_bookings(self.db)
        
        sent_count = 0
        for booking in bookings:
            if self.send_pre_arrival_email(booking.id):
                sent_count += 1
        
        return sent_count 