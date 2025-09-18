from typing import Optional
from sqlalchemy.orm import Session

from app.models import MeterReading, Booking
from app.schemas import MeterReadingCreate, MeterReadingUpdate
from app.services.booking_status_service import BookingStatusService


class MeterService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_meter_reading(self, meter_data: MeterReadingCreate) -> Optional[MeterReading]:
        """Create or update meter reading for a booking."""
        # Check if meter reading already exists for this booking
        existing = self.db.query(MeterReading).filter(
            MeterReading.booking_id == meter_data.booking_id
        ).first()
        
        if existing:
            # Update existing record
            for field, value in meter_data.dict(exclude={'booking_id'}).items():
                if value is not None:
                    setattr(existing, field, value)
            self.db.commit()
            self.db.refresh(existing)
            
            # Update booking status if readings were added
            self._update_booking_status_on_readings(meter_data.booking_id)
            
            return existing
        else:
            # Create new record
            meter_reading = MeterReading(**meter_data.dict())
            self.db.add(meter_reading)
            self.db.commit()
            self.db.refresh(meter_reading)
            
            # Update booking status when readings are added
            self._update_booking_status_on_readings(meter_data.booking_id)
            
            return meter_reading
    
    def _update_booking_status_on_readings(self, booking_id: int):
        """Update booking status when meter readings are added."""
        booking = self.db.query(Booking).filter(Booking.id == booking_id).first()
        if booking:
            status_service = BookingStatusService(self.db)
            status_service.update_status_on_readings_added(booking)
    
    def update_meter_reading(self, booking_id: int, meter_data: MeterReadingUpdate) -> Optional[MeterReading]:
        """Update meter reading for a booking."""
        meter_reading = self.db.query(MeterReading).filter(
            MeterReading.booking_id == booking_id
        ).first()
        
        if not meter_reading:
            return None
        
        # Update only provided fields
        for field, value in meter_data.dict(exclude_unset=True).items():
            setattr(meter_reading, field, value)
        
        self.db.commit()
        self.db.refresh(meter_reading)
        return meter_reading
    
    def get_meter_reading(self, booking_id: int) -> Optional[MeterReading]:
        """Get meter reading for a booking."""
        return self.db.query(MeterReading).filter(
            MeterReading.booking_id == booking_id
        ).first()
    
    def are_readings_complete(self, booking_id: int) -> bool:
        """Check if all required meter readings are available for invoicing."""
        meter_reading = self.get_meter_reading(booking_id)
        if not meter_reading:
            return False
        
        # Check if all critical readings are available
        required_fields = [
            meter_reading.electricity_start,
            meter_reading.electricity_end,
            meter_reading.gas_start,
            meter_reading.gas_end,
            # Note: firewood_boxes might be optional depending on booking
        ]
        
        return all(field is not None for field in required_fields)
    
    def get_consumption_summary(self, booking_id: int) -> dict:
        """Calculate consumption amounts from meter readings."""
        meter_reading = self.get_meter_reading(booking_id)
        if not meter_reading:
            return {}
        
        summary = {}
        
        # Electricity consumption (kWh)
        if meter_reading.electricity_start is not None and meter_reading.electricity_end is not None:
            summary['electricity_kwh'] = meter_reading.electricity_end - meter_reading.electricity_start
        
        # Gas consumption (convert from cubic meters to kWh)
        if meter_reading.gas_start is not None and meter_reading.gas_end is not None:
            gas_cubic_meters = meter_reading.gas_end - meter_reading.gas_start
            # Conversion factor: 1 cubic meter = 10.5 kWh (typical for natural gas)
            gas_conversion_factor = 10.5
            summary['gas_kwh'] = gas_cubic_meters * gas_conversion_factor
            summary['gas_cubic_meters'] = gas_cubic_meters  # Keep original for reference
        
        # Firewood
        if meter_reading.firewood_boxes is not None:
            summary['firewood_boxes'] = meter_reading.firewood_boxes
        
        return summary 