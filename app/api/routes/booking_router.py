from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.booking_repository import BookingRepository
from app.database import get_db
from app.guest_repository import GuestRepository
from app.schemas import BookingCreate, BookingResponse
from app.services.booking_service import BookingService
from app.services.communication_service import CommunicationService

router = APIRouter()


def get_booking_repository(db: Session = Depends(get_db)):
    return BookingRepository(db)


def get_guest_repository(db: Session = Depends(get_db)):
    return GuestRepository(db)


def get_email_config():
    return {
        "sender": "bookings@yourhouse.com",
        "smtp_server": "smtp.yourprovider.com",
        "smtp_port": 587,
        "username": "your_username",
        "password": "your_password",
    }


def get_communication_service(email_config=Depends(get_email_config)):
    return CommunicationService(email_config)


def get_booking_service(
    booking_repository=Depends(get_booking_repository),
    guest_repository=Depends(get_guest_repository),
    communication_service=Depends(get_communication_service),
):
    return BookingService(booking_repository, guest_repository, communication_service)


# def get_booking_service(
#     repository: BookingRepository = Depends(get_booking_repository),
#     guest_repository: GuestRepository = Depends(get_guest_repository),
# ):
#     return BookingService(repository, guest_repository)
#


@router.post("/bookings", response_model=BookingResponse)
def add_booking(
    booking: BookingCreate,
    booking_service: BookingService = Depends(get_booking_service),
):
    try:
        return booking_service.create_booking(booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        pass


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(booking_service: BookingService = Depends(get_booking_service)):
    try:
        return booking_service.get_all_bookings()
    except ValueError as e:
        raise HTTPException(status_code=400, details=str(e))


@router.patch("/booking/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(
    booking_id: int, booking_service: BookingService = Depends(get_booking_service)
):
    try:
        return booking_service.confirm_booking(booking_id)
    except ValueError:
        raise HTTPException(status_code=404)
