from sqlalchemy.orm import Session

from app.models import Guest


class GuestRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, guest_data: dict) -> Guest:
        """Create a new guest in the database."""
        guest = Guest(**guest_data)
        self.db.add(guest)
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def get_by_email(self, email: str) -> Guest:
        """Get a guest by email."""
        return self.db.query(Guest).filter(Guest.email == email).first()

    def get_by_id(self, guest_id: int) -> Guest:
        """Get a guest by ID."""
        return self.db.query(Guest).filter(Guest.id == guest_id).first()

    def get_all(self) -> list[Guest]:
        """Get all guests."""
        return self.db.query(Guest).all()

    def update(self, guest: Guest) -> Guest:
        """Update a guest."""
        self.db.commit()
        self.db.refresh(guest)
        return guest

    def delete(self, guest: Guest) -> None:
        """Delete a guest."""
        self.db.delete(guest)
        self.db.commit()
