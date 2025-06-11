import datetime
import uuid
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Booking, UnitPrice, MeterReading, PriceType
from app.services.communication_service import CommunicationService
from app.services.meter_service import MeterService


class InvoiceService:
    def __init__(self, db: Session, communication_service: CommunicationService, meter_service: MeterService):
        self.db = db
        self.communication_service = communication_service
        self.meter_service = meter_service
        self.agent_email = "booking-agent@example.com"  # Configure this
    
    def generate_invoice_for_booking(self, booking_id: int) -> Optional[str]:
        """Generate invoice for a booking if all requirements are met."""
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if not booking:
            return None
        
        # Check if readings are complete
        if not self.meter_service.are_readings_complete(booking_id):
            self._send_missing_readings_reminder(booking)
            return None
        
        # Generate invoice ID
        invoice_id = f"INV-{booking.id}-{datetime.datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        
        # Calculate invoice amounts
        invoice_data = self._calculate_invoice_amounts(booking)
        
        # Generate PDF (placeholder for now)
        pdf_path = self._generate_invoice_pdf(booking, invoice_data, invoice_id)
        
        # Send invoice email
        if self._send_invoice_email(booking, invoice_id, pdf_path):
            # Update booking
            booking.invoice_id = invoice_id
            booking.invoice_created = True
            booking.invoice_sent = True
            booking.invoice_sent_date = datetime.datetime.utcnow()
            self.db.commit()
            
            return invoice_id
        
        return None
    
    def _calculate_invoice_amounts(self, booking: Booking) -> dict:
        """Calculate all amounts for the invoice."""
        consumption = self.meter_service.get_consumption_summary(booking.id)
        
        # Get current unit prices
        current_date = datetime.date.today()
        
        # Calculate accommodation costs
        num_days = (booking.check_out - booking.check_in).days
        stay_rate = self._get_unit_price(PriceType.STAY_PER_NIGHT, current_date)
        accommodation_cost = num_days * stay_rate if stay_rate else 0
        
        # Calculate utility costs
        electricity_cost = 0
        gas_cost = 0
        firewood_cost = 0
        
        if 'electricity_kwh' in consumption:
            elec_rate = self._get_unit_price(PriceType.ELECTRICITY_PER_KWH, current_date)
            electricity_cost = consumption['electricity_kwh'] * elec_rate if elec_rate else 0
        
        if 'gas_kwh' in consumption:
            gas_rate = self._get_unit_price(PriceType.GAS_PER_CUBIC_METER, current_date)
            gas_cost = consumption['gas_kwh'] * gas_rate if gas_rate else 0
        
        if 'firewood_boxes' in consumption:
            firewood_rate = self._get_unit_price(PriceType.FIREWOOD_PER_BOX, current_date)
            firewood_cost = consumption['firewood_boxes'] * firewood_rate if firewood_rate else 0
        
        # Tourist tax
        kurtaxe_cost = booking.kurtaxe_amount or 0
        
        return {
            'accommodation_cost': accommodation_cost,
            'electricity_cost': electricity_cost,
            'gas_cost': gas_cost,
            'firewood_cost': firewood_cost,
            'kurtaxe_cost': kurtaxe_cost,
            'total_cost': accommodation_cost + electricity_cost + gas_cost + firewood_cost + kurtaxe_cost,
            'consumption': consumption,
            'num_days': num_days
        }
    
    def _get_unit_price(self, price_type: PriceType, date: datetime.date) -> Optional[float]:
        """Get unit price for a specific type and date."""
        price = self.db.query(UnitPrice).filter(
            UnitPrice.price_type == price_type,
            UnitPrice.effective_from <= date,
            (UnitPrice.effective_to.is_(None) | (UnitPrice.effective_to >= date))
        ).order_by(UnitPrice.effective_from.desc()).first()
        
        return price.price_per_unit if price else None
    
    def _generate_invoice_pdf(self, booking: Booking, invoice_data: dict, invoice_id: str) -> str:
        """Generate PDF invoice (placeholder implementation)."""
        # This would integrate with a PDF generation library like reportlab
        # For now, just return a placeholder path
        pdf_path = f"/tmp/invoice_{invoice_id}.pdf"
        
        # Placeholder: In real implementation, generate actual PDF with:
        # - Guest details
        # - Booking dates
        # - Itemized consumption
        # - Unit prices
        # - Total amounts
        
        print(f"Generated invoice PDF: {pdf_path}")
        print(f"Invoice data: {invoice_data}")
        
        return pdf_path
    
    def _send_invoice_email(self, booking: Booking, invoice_id: str, pdf_path: str) -> bool:
        """Send invoice email to guest with agent in CC."""
        guest = booking.guest
        
        context = {
            "guest_name": f"{guest.first_name} {guest.last_name}",
            "check_in_date": booking.check_in.strftime("%B %d, %Y"),
            "check_out_date": booking.check_out.strftime("%B %d, %Y"),
            "invoice_id": invoice_id,
            "subject": f"Invoice {invoice_id}"
        }
        
        try:
            # In real implementation, attach PDF to email
            self.communication_service.send_email(
                recipient=guest.email,
                subject=f"Invoice {invoice_id}",
                template_name="invoice_email",  # Would need to create this template
                context=context
            )
            
            # Send copy to agent (in real implementation, use CC or BCC)
            self.communication_service.send_email(
                recipient=self.agent_email,
                subject=f"Invoice Sent - {invoice_id}",
                template_name="invoice_agent_copy",  # Would need to create this template
                context=context
            )
            
            return True
        except Exception as e:
            print(f"Failed to send invoice email: {e}")
            return False
    
    def _send_missing_readings_reminder(self, booking: Booking):
        """Send reminder to agent when readings are missing."""
        missing_items = []
        meter_reading = self.meter_service.get_meter_reading(booking.id)
        
        if not meter_reading:
            missing_items.append("All meter readings")
        else:
            if meter_reading.electricity_start is None or meter_reading.electricity_end is None:
                missing_items.append("Electricity readings")
            if meter_reading.gas_start is None or meter_reading.gas_end is None:
                missing_items.append("Gas readings")
        
        # Use kurkarten service's agent reminder method
        from app.services.kurkarten_service import KurkartenService
        kurkarten_service = KurkartenService(self.db, self.communication_service)
        kurkarten_service._send_agent_reminder(
            booking,
            "Missing meter readings - cannot generate invoice",
            missing_items
        )
    
    def check_and_generate_invoices(self) -> int:
        """Check for bookings that need invoices (3 days after departure)."""
        cutoff_date = datetime.date.today() - datetime.timedelta(days=3)
        
        bookings = self.db.query(Booking).filter(
            Booking.confirmed == True,
            Booking.check_out <= cutoff_date,
            Booking.invoice_created == False
        ).all()
        
        generated_count = 0
        for booking in bookings:
            if self.generate_invoice_for_booking(booking.id):
                generated_count += 1
        
        return generated_count 