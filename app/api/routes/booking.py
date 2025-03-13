from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import get_all_bookings
from app.database import get_db
from app.schemas import BookingCreate, BookingResponse, BookingUpdate
from app.services.booking_service import confirm_booking, create_booking

router = APIRouter()


@router.post("/bookings", response_model=BookingResponse)
def add_booking(booking: BookingCreate, db: Session = Depends(get_db)):
    try:
        return create_booking(db, booking)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        pass


@router.get("/bookings", response_model=list[BookingResponse])
def list_bookings(db: Session = Depends(get_db)):
    return get_all_bookings(db)


@router.patch("/bookings/{booking_id}", response_model=BookingResponse)
def update_booking(
    booking_id: int, update_data: BookingUpdate, db: Session = Depends(get_db)
):
    # TODO: improve below. The check needs to be if ocnfirmed==True and either to not return or make sure that only one parameter is patched
    if update_data.confirmed is not None:
        try:
            return confirm_booking(db, booking_id)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
