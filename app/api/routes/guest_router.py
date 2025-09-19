# guest_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.guest_repository import GuestRepository
from app.schemas import GuestCreate, GuestResponse, GuestUpdate
from app.services.guest_service import GuestService

router = APIRouter()


def get_guest_repository(db: Session = Depends(get_db)):
    return GuestRepository(db)


def get_guest_service(repository: GuestRepository = Depends(get_guest_repository)):
    return GuestService(repository)


@router.post("/guests", response_model=GuestResponse)
def add_guest(
    guest: GuestCreate, 
    guest_service: GuestService = Depends(get_guest_service)
):
    try:
        return guest_service.create_guest(guest)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/guests", response_model=list[GuestResponse])
def list_guests(guest_service: GuestService = Depends(get_guest_service)):
    try:
        return guest_service.get_all_guests()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/guest/{guest_id}", response_model=GuestResponse)
def get_guest_by_id(
    guest_id: int, guest_service: GuestService = Depends(get_guest_service)
):
    """Get a specific guest by ID."""
    try:
        return guest_service.get_guest_by_id(guest_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/guest/{guest_id}", response_model=GuestResponse)
def update_guest(
    guest_id: int,
    guest_update: GuestUpdate,
    guest_service: GuestService = Depends(get_guest_service)
):
    """Update a guest by ID."""
    try:
        return guest_service.update_guest(guest_id, guest_update)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
