from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.crud import create_guest
from app.database import get_db
from app.schemas import GuestCreate, GuestResponse
from app.services.guest_service import get_all_guests

router = APIRouter()


@router.post("/guests", response_model=GuestResponse)
def add_guest(guest: GuestCreate, db: Session = Depends(get_db)):
    try:
        return create_guest(db, guest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        pass


@router.get("/guests", response_model=list[GuestResponse])
def list_guests(db: Session = Depends(get_db)):
    return get_all_guests(db)
