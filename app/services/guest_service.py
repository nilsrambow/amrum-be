from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.models import Guest

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def check_guest_exists(db, guest_data):
    existing_guest = db.query(Guest).filter(Guest.email == guest_data.email).first()
    return existing_guest

def get_all_guests(db: Session):
    return db.query(Guest).all()
