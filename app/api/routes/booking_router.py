from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.booking_repository import BookingRepository
from app.config.config import get_email_config
from app.database import get_db
from app.guest_repository import GuestRepository
from app.schemas import (
    BookingCreate, BookingResponse, BookingUpdate, KurtaxeUpdate,
    MeterReadingCreate, MeterReadingUpdate, MeterReadingResponse,
    PaymentCreate, PaymentResponse
)
from app.services.booking_service import BookingService
from app.services.communication_service import CommunicationService
from app.services.kurkarten_service import KurkartenService
from app.services.meter_service import MeterService
from app.services.payment_service import PaymentService
from app.services.invoice_service import InvoiceService

router = APIRouter()


def get_booking_repository(db: Session = Depends(get_db)):
    return BookingRepository(db)


def get_guest_repository(db: Session = Depends(get_db)):
    return GuestRepository(db)


def get_communication_service(email_config=Depends(get_email_config)):
    return CommunicationService(email_config)


def get_booking_service(
    booking_repository=Depends(get_booking_repository),
    guest_repository=Depends(get_guest_repository),
    communication_service=Depends(get_communication_service),
):
    return BookingService(booking_repository, guest_repository, communication_service)


def get_kurkarten_service(
    db: Session = Depends(get_db),
    communication_service: CommunicationService = Depends(get_communication_service)
):
    return KurkartenService(db, communication_service)


def get_meter_service(db: Session = Depends(get_db)):
    return MeterService(db)


def get_payment_service(db: Session = Depends(get_db)):
    return PaymentService(db)


def get_invoice_service(
    db: Session = Depends(get_db),
    communication_service: CommunicationService = Depends(get_communication_service),
    meter_service: MeterService = Depends(get_meter_service)
):
    return InvoiceService(db, communication_service, meter_service)


@router.post("/bookings", response_model=BookingResponse)
def add_booking(
    booking: BookingCreate,
    booking_service: BookingService = Depends(get_booking_service),
):
    try:
        return booking_service.create_booking(booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(booking_service: BookingService = Depends(get_booking_service)):
    try:
        return booking_service.get_all_bookings()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/booking/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(
    booking_id: int, booking_service: BookingService = Depends(get_booking_service)
):
    try:
        return booking_service.confirm_booking(booking_id)
    except ValueError:
        raise HTTPException(status_code=404)


@router.post("/booking/{booking_id}/kurkarten/send")
def send_kurkarten_email(
    booking_id: int,
    kurkarten_service: KurkartenService = Depends(get_kurkarten_service)
):
    """Send kurkarten request email to guest (for testing)."""
    if kurkarten_service.send_kurkarten_request_email(booking_id):
        return {"message": "Kurkarten email sent successfully"}
    raise HTTPException(status_code=400, detail="Failed to send kurkarten email")


@router.post("/booking/{booking_id}/pre-arrival/send")
def send_pre_arrival_email(
    booking_id: int,
    kurkarten_service: KurkartenService = Depends(get_kurkarten_service)
):
    """Send pre-arrival information email to guest (for testing)."""
    if kurkarten_service.send_pre_arrival_email(booking_id):
        return {"message": "Pre-arrival email sent successfully"}
    raise HTTPException(status_code=400, detail="Failed to send pre-arrival email")


@router.post("/booking/{booking_id}/invoice/generate")
def generate_invoice(
    booking_id: int,
    invoice_service: InvoiceService = Depends(get_invoice_service)
):
    """Generate and send invoice for a booking (for testing)."""
    invoice_id = invoice_service.generate_invoice_for_booking(booking_id)
    if invoice_id:
        return {"message": "Invoice generated and sent", "invoice_id": invoice_id}
    raise HTTPException(status_code=400, detail="Failed to generate invoice")


@router.patch("/booking/{booking_id}/kurtaxe", response_model=BookingResponse)
def update_kurtaxe(
    booking_id: int,
    kurtaxe_data: KurtaxeUpdate,
    db: Session = Depends(get_db)
):
    """Update kurtaxe (tourist tax) information for a booking."""
    from app.models import Booking
    
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    if kurtaxe_data.kurtaxe_amount is not None:
        booking.kurtaxe_amount = kurtaxe_data.kurtaxe_amount
    if kurtaxe_data.kurtaxe_notes is not None:
        booking.kurtaxe_notes = kurtaxe_data.kurtaxe_notes
    
    db.commit()
    db.refresh(booking)
    return booking


@router.post("/booking/{booking_id}/meter-readings", response_model=MeterReadingResponse)
def create_or_update_meter_reading(
    booking_id: int,
    meter_data: MeterReadingUpdate,
    meter_service: MeterService = Depends(get_meter_service)
):
    """Create or update meter readings for a booking."""
    meter_create_data = MeterReadingCreate(
        booking_id=booking_id,
        **meter_data.dict(exclude_unset=True)
    )
    
    meter_reading = meter_service.create_meter_reading(meter_create_data)
    if not meter_reading:
        raise HTTPException(status_code=400, detail="Failed to create/update meter reading")
    
    return meter_reading


@router.get("/booking/{booking_id}/meter-readings", response_model=MeterReadingResponse)
def get_meter_reading(
    booking_id: int,
    meter_service: MeterService = Depends(get_meter_service)
):
    """Get meter readings for a booking."""
    meter_reading = meter_service.get_meter_reading(booking_id)
    if not meter_reading:
        raise HTTPException(status_code=404, detail="Meter readings not found")
    
    return meter_reading


@router.post("/booking/{booking_id}/payments", response_model=PaymentResponse)
def register_payment(
    booking_id: int,
    payment_data: PaymentCreate,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """Register a payment for a booking."""
    payment_data.booking_id = booking_id
    return payment_service.register_payment(payment_data)


@router.get("/booking/{booking_id}/payments", response_model=list[PaymentResponse])
def list_payments(
    booking_id: int,
    payment_service: PaymentService = Depends(get_payment_service)
):
    """List all payments for a booking."""
    return payment_service.get_payments_for_booking(booking_id)
