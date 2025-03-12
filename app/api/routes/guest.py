from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import GuestCreate, GuestResponse
from app.services.guest_service import create_guest

router = APIRouter()


@router.post("/guests", response_model=GuestResponse)
def add_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    try:
        return create_guest(db, guest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    pass
