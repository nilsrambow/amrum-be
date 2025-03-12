from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import Guest
from app.schemas import GuestCreate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def create_guest(db: Session, guest_data: GuestCreate):
    existing_guest = db.query(Guest).filter(Guest.email == guest_data.email).first()
    if existing_guest:
        raise ValueError("Guest with this email already exists")

    new_guest = Guest(
        first_name=guest_data.first_name,
        last_name=guest_data.last_name,
        email=guest_data.email,
        hashed_password=hash_password(guest_data.password),
        pays_dayrate=guest_data.pays_dayrate,
        is_admin=guest_data.is_admin,
    )
    db.add(new_guest)
    db.commit()
    db.refresh(new_guest)
    return new_guest


def get_all_guests(db: Session):
    return db.query(Guest).all()
