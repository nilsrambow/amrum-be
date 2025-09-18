from passlib.context import CryptContext

from app.guest_repository import GuestRepository
from app.schemas import GuestCreate, GuestUpdate


class GuestService:
    def __init__(self, guest_repository: GuestRepository):
        self.repository = guest_repository
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        """Hash a password using bcrypt."""
        return self.pwd_context.hash(password)

    def create_guest(self, guest_data: GuestCreate):
        """Create a new guest."""
        # Check if guest already exists
        existing_guest = self.repository.get_by_email(guest_data.email)
        if existing_guest:
            raise ValueError(f"Guest with email {guest_data.email} already exists")

        # Prepare guest data
        guest_dict = guest_data.dict()
        guest_dict.pop("password")  # Remove plain password
        guest_dict["hashed_password"] = self.hash_password(guest_data.password)

        # Create guest
        return self.repository.create(guest_dict)

    def get_all_guests(self):
        """Get all guests."""
        return self.repository.get_all()

    def get_guest_by_id(self, guest_id: int):
        """Get a guest by ID."""
        guest = self.repository.get_by_id(guest_id)
        if not guest:
            raise ValueError(f"Guest with ID {guest_id} not found")
        return guest

    def update_guest(self, guest_id: int, guest_data: GuestUpdate):
        """Update a guest by ID."""
        from datetime import datetime
        
        guest = self.get_guest_by_id(guest_id)
        
        # Check if email is being updated and if it already exists
        if guest_data.email and guest_data.email != guest.email:
            existing_guest = self.repository.get_by_email(guest_data.email)
            if existing_guest:
                raise ValueError(f"Guest with email {guest_data.email} already exists")
        
        # Update the provided fields
        for field, value in guest_data.dict(exclude_unset=True).items():
            setattr(guest, field, value)
        
        # Update the modified timestamp
        guest.modified_at = datetime.utcnow()
        
        return self.repository.update(guest)
