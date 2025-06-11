from typing import Optional
from sqlalchemy.orm import Session

from app.models import MeterReading, Booking
from app.schemas import MeterReadingCreate, MeterReadingUpdate


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
            return existing
        else:
            # Create new record
            meter_reading = MeterReading(**meter_data.dict())
            self.db.add(meter_reading)
            self.db.commit()
            self.db.refresh(meter_reading)
            return meter_reading
    
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
        
        # Electricity consumption
        if meter_reading.electricity_start is not None and meter_reading.electricity_end is not None:
            summary['electricity_kwh'] = meter_reading.electricity_end - meter_reading.electricity_start
        
        # Gas consumption
        if meter_reading.gas_start is not None and meter_reading.gas_end is not None:
            summary['gas_kwh'] = meter_reading.gas_end - meter_reading.gas_start
        
        # Firewood
        if meter_reading.firewood_boxes is not None:
            summary['firewood_boxes'] = meter_reading.firewood_boxes
        
        return summary 