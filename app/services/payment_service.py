from typing import List, Optional
from sqlalchemy.orm import Session

from app.models import Payment, Booking
from app.schemas import PaymentCreate
from app.services.booking_status_service import BookingStatusService


class PaymentService:
    def __init__(self, db: Session):
        self.db = db
    
    def register_payment(self, payment_data: PaymentCreate) -> Payment:
        """Register a new payment for a booking."""
        payment = Payment(**payment_data.dict())
        self.db.add(payment)
        self.db.commit()
        self.db.refresh(payment)
        
        # Update booking status when payment is registered
        booking = self.db.query(Booking).filter(Booking.id == payment.booking_id).first()
        if booking:
            status_service = BookingStatusService(self.db)
            status_service.update_status_on_payment_received(booking)
        
        return payment
    
    def get_payments_for_booking(self, booking_id: int) -> List[Payment]:
        """Get all payments for a specific booking."""
        return self.db.query(Payment).filter(
            Payment.booking_id == booking_id
        ).order_by(Payment.payment_date.desc()).all()
    
    def get_total_paid(self, booking_id: int) -> float:
        """Get total amount paid for a booking."""
        payments = self.get_payments_for_booking(booking_id)
        return sum(payment.amount for payment in payments)
    
    def update_booking_paid_status(self, booking_id: int, total_due: float) -> bool:
        """Update booking paid status based on total payments vs amount due."""
        total_paid = self.get_total_paid(booking_id)
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        
        if booking:
            booking.paid = total_paid >= total_due
            self.db.commit()
            return True
        return False 