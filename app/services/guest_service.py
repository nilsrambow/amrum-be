from sqlalchemy.orm import Session

from app.models import Guest
from app.schemas import GuestCreate


def create_guest(db: Session, guest_data: GuestCreate):
    existing_guest = db.queary(Guest).filter(Guest.email == guest_data.email).first()
    if existing_guest:
        raise ValueError("Guest with this email already exists")

    new_guest = Guest(guest_data)
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest
