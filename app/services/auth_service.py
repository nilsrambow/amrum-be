"""
Authentication and authorization service for API access control.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import AdminUser
from app.database import get_db

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))


class AuthService:
    """Service for handling authentication and authorization."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)
    
    def authenticate_admin(self, username: str, password: str) -> Optional[AdminUser]:
        """Authenticate an admin user."""
        admin = self.db.query(AdminUser).filter(AdminUser.username == username).first()
        if not admin:
            return None
        if not self.verify_password(password, admin.hashed_password):
            return None
        return admin
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is None:
                return None
            return payload
        except JWTError:
            return None
    
    def get_current_admin(self, token: str) -> Optional[AdminUser]:
        """Get current admin user from token."""
        payload = self.verify_token(token)
        if payload is None:
            return None
        
        username = payload.get("sub")
        admin = self.db.query(AdminUser).filter(AdminUser.username == username).first()
        return admin


def get_auth_service(db: Session = None) -> AuthService:
    """Dependency to get AuthService instance."""
    if db is None:
        db = next(get_db())
    return AuthService(db)
