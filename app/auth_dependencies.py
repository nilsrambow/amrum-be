"""
Authentication dependencies for FastAPI endpoints.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.models import AdminUser

# Security scheme
security = HTTPBearer()


async def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> AdminUser:
    """Dependency to get current authenticated admin user."""
    auth_service = AuthService(db)
    
    # Extract token from Authorization header
    token = credentials.credentials
    
    # Verify token and get admin
    admin = auth_service.get_current_admin(token)
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    return admin


async def get_current_superuser(
    current_admin: AdminUser = Depends(get_current_admin)
) -> AdminUser:
    """Dependency to get current authenticated superuser."""
    if not current_admin.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_admin


def get_optional_admin(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[AdminUser]:
    """Optional dependency to get current admin (returns None if not authenticated)."""
    if credentials is None:
        return None
    
    auth_service = AuthService(db)
    admin = auth_service.get_current_admin(credentials.credentials)
    return admin if admin and admin.is_active else None
