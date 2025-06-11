import asyncio
import schedule
import time
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.config.config import get_email_config
from app.services.communication_service import CommunicationService
from app.services.kurkarten_service import KurkartenService
from app.services.meter_service import MeterService
from app.services.invoice_service import InvoiceService


class SchedulerService:
    def __init__(self):
        self.running = False
    
    def get_db_session(self) -> Session:
        """Get a database session for scheduled tasks."""
        return SessionLocal()
    
    def run_kurkarten_emails(self):
        """Run kurkarten email check (25 days before arrival)."""
        print(f"[{datetime.now()}] Running kurkarten email check...")
        
        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            kurkarten_service = KurkartenService(db, communication_service)
            
            count = kurkarten_service.check_and_send_kurkarten_emails()
            print(f"[{datetime.now()}] Sent {count} kurkarten emails")
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in kurkarten email check: {e}")
        finally:
            db.close()
    
    def run_pre_arrival_emails(self):
        """Run pre-arrival email check (5 days before arrival)."""
        print(f"[{datetime.now()}] Running pre-arrival email check...")
        
        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            kurkarten_service = KurkartenService(db, communication_service)
            
            count = kurkarten_service.check_and_send_pre_arrival_emails()
            print(f"[{datetime.now()}] Sent {count} pre-arrival emails")
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in pre-arrival email check: {e}")
        finally:
            db.close()
    
    def run_invoice_generation(self):
        """Run invoice generation check (3 days after departure)."""
        print(f"[{datetime.now()}] Running invoice generation check...")
        
        db = self.get_db_session()
        try:
            email_config = get_email_config()
            communication_service = CommunicationService(email_config)
            meter_service = MeterService(db)
            invoice_service = InvoiceService(db, communication_service, meter_service)
            
            count = invoice_service.check_and_generate_invoices()
            print(f"[{datetime.now()}] Generated {count} invoices")
            
        except Exception as e:
            print(f"[{datetime.now()}] Error in invoice generation: {e}")
        finally:
            db.close()
    
    def setup_schedule(self):
        """Setup the scheduled tasks."""
        # Run all checks daily at 9:00 AM
        schedule.every().day.at("09:00").do(self.run_kurkarten_emails)
        schedule.every().day.at("09:15").do(self.run_pre_arrival_emails)
        schedule.every().day.at("09:30").do(self.run_invoice_generation)
        
        print("Scheduler setup complete. Tasks will run daily at:")
        print("- 09:00: Kurkarten emails (25 days before arrival)")
        print("- 09:15: Pre-arrival emails (5 days before arrival)")
        print("- 09:30: Invoice generation (3 days after departure)")
    
    async def start_scheduler(self):
        """Start the scheduler in the background."""
        if self.running:
            return
        
        self.running = True
        self.setup_schedule()
        
        print(f"[{datetime.now()}] Scheduler started")
        
        # Run scheduler in background
        while self.running:
            schedule.run_pending()
            await asyncio.sleep(60)  # Check every minute
    
    def stop_scheduler(self):
        """Stop the scheduler."""
        self.running = False
        schedule.clear()
        print(f"[{datetime.now()}] Scheduler stopped")


# Global scheduler instance
scheduler_service = SchedulerService() 