from datetime import date
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Booking

router = APIRouter(tags=["availability"])


class BookingDateRange(BaseModel):
    start: date
    end: date


@router.get("/availability", response_model=List[BookingDateRange])
def get_availability(db: Session = Depends(get_db)):
    year = date.today().year
    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)

    bookings = (
        db.query(Booking)
        .filter(Booking.check_in <= year_end, Booking.check_out >= year_start)
        .all()
    )

    return [BookingDateRange(start=b.check_in, end=b.check_out) for b in bookings]
