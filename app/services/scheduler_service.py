import asyncio
import logging
import schedule
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.database import SessionLocal
from app.config.config import get_email_config
from app.services.communication_service import CommunicationService
from app.services.kurkarten_service import KurkartenService
from app.services.meter_service import MeterService
from app.services.invoice_service import InvoiceService
from app.services.booking_status_service import BookingStatusService


class SchedulerService:
    def __init__(self):
        self.running = False
    
    def get_db_session(self) -> Session:
        """Get a database session for scheduled tasks."""
        return SessionLocal()
    
    def run_booking_status_update(self):
        """Run booking status update for all bookings."""
        logger.info("Running booking status update...")

        db = self.get_db_session()
        try:
            status_service = BookingStatusService(db)
            updated_count = status_service.update_all_booking_statuses()
            logger.info("Updated %d booking statuses", updated_count)

        except Exception as e:
            logger.error("Error in booking status update: %s", e, exc_info=True)
        finally:
            db.close()

    def run_kurkarten_emails(self):
        """Run kurkarten email check (25 days before arrival)."""
        logger.info("Running kurkarten email check...")

        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            kurkarten_service = KurkartenService(db, communication_service)

            count = kurkarten_service.check_and_send_kurkarten_emails()
            logger.info("Sent %d kurkarten emails", count)

        except Exception as e:
            logger.error("Error in kurkarten email check: %s", e, exc_info=True)
        finally:
            db.close()

    def run_pre_arrival_emails(self):
        """Run pre-arrival email check (5 days before arrival)."""
        logger.info("Running pre-arrival email check...")

        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            kurkarten_service = KurkartenService(db, communication_service)

            count = kurkarten_service.check_and_send_pre_arrival_emails()
            logger.info("Sent %d pre-arrival emails", count)

        except Exception as e:
            logger.error("Error in pre-arrival email check: %s", e, exc_info=True)
        finally:
            db.close()

    def run_invoice_generation(self):
        """Run invoice generation check (3 days after departure)."""
        logger.info("Running invoice generation check...")

        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            meter_service = MeterService(db)
            invoice_service = InvoiceService(db, communication_service, meter_service)

            count = invoice_service.check_and_generate_invoices()
            logger.info("Generated %d invoices", count)

        except Exception as e:
            logger.error("Error in invoice generation: %s", e, exc_info=True)
        finally:
            db.close()

    def run_booking_confirmation(self):
        """Run booking confirmation check (24 hours after creation/modification)."""
        logger.info("Running booking confirmation check...")

        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)

            from app.booking_repository import BookingRepository
            from app.guest_repository import GuestRepository
            from app.services.booking_service import BookingService

            booking_repository = BookingRepository(db)
            guest_repository = GuestRepository(db)
            booking_service = BookingService(booking_repository, guest_repository, communication_service)

            count = booking_service.check_and_confirm_bookings(auto_confirm_delay_hours=24)
            logger.info("Confirmed %d bookings", count)

        except Exception as e:
            logger.error("Error in booking confirmation: %s", e, exc_info=True)
        finally:
            db.close()

    def setup_schedule(self):
        """Setup the scheduled tasks."""
        schedule.every().day.at("08:45").do(self.run_booking_status_update)
        schedule.every().day.at("09:00").do(self.run_booking_confirmation)
        schedule.every().day.at("09:15").do(self.run_kurkarten_emails)
        schedule.every().day.at("09:30").do(self.run_pre_arrival_emails)
        schedule.every().day.at("09:45").do(self.run_invoice_generation)

        logger.info(
            "Scheduler setup complete. Tasks will run daily at: "
            "08:45 booking status update, "
            "09:00 booking confirmation, "
            "09:15 kurkarten emails, "
            "09:30 pre-arrival emails, "
            "09:45 invoice generation"
        )

    async def start_scheduler(self):
        """Start the scheduler in the background."""
        if self.running:
            return

        self.running = True
        self.setup_schedule()

        logger.info("Scheduler started")

        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute

    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        logger.info("Scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService() 