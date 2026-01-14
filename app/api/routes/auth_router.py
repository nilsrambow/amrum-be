"""
Authentication router for admin login and user management.
"""
import json
from datetime import datetime as _dt
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import AuthService
from app.auth_dependencies import get_current_admin, get_current_superuser
from app.schemas import LoginRequest, Token, AdminUserCreate, AdminUserResponse
from app.models import AdminUser

router = APIRouter(prefix="/auth", tags=["authentication"])

# region agent log helpers
def _agent_log(*, hypothesisId: str, location: str, message: str, data: dict):
    # Never log secrets (passwords/tokens/PII). Keep payload small.
    try:
        payload = {
            "sessionId": "debug-session",
            "runId": "pre-fix",
            "hypothesisId": hypothesisId,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(_dt.now().timestamp() * 1000),
        }
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    except Exception:
        pass
# endregion


@router.post("/login", response_model=Token)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint for admin users."""
    auth_service = AuthService(db)

    # region agent log
    _agent_log(
        hypothesisId="D",
        location="auth_router.py:login:entered",
        message="Entered /auth/login route",
        data={
            "username_len": len(login_data.username) if isinstance(login_data.username, str) else None,
            "username_has_at": ("@" in login_data.username) if isinstance(login_data.username, str) else None,
            "password_len": len(login_data.password) if isinstance(login_data.password, str) else None,
        },
    )
    # endregion
    
    # Authenticate user
    admin = auth_service.authenticate_admin(login_data.username, login_data.password)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=30)  # 30 minutes
    access_token = auth_service.create_access_token(
        data={"sub": admin.username}, expires_delta=access_token_expires
    )
    
    # Update last login
    admin.last_login = datetime.utcnow()
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get("/me", response_model=AdminUserResponse)
def get_current_user_info(
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get current user information."""
    return current_admin


@router.post("/users", response_model=AdminUserResponse)
def create_admin_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_superuser)
):
    """Create a new admin user (superuser only)."""
    auth_service = AuthService(db)
    
    # Check if username already exists
    existing_user = db.query(AdminUser).filter(AdminUser.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(AdminUser).filter(AdminUser.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new admin user
    hashed_password = auth_service.get_password_hash(user_data.password)
    admin_user = AdminUser(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=False  # New users are not superusers by default
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return admin_user


@router.get("/users", response_model=list[AdminUserResponse])
def list_admin_users(
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_superuser)
):
    """List all admin users (superuser only)."""
    users = db.query(AdminUser).all()
    return users


@router.put("/users/{user_id}/toggle-active")
def toggle_user_active(
    user_id: int,
    db: Session = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_superuser)
):
    """Toggle user active status (superuser only)."""
    user = db.query(AdminUser).filter(AdminUser.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Prevent deactivating yourself
    if user.id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself"
        )
    
    user.is_active = not user.is_active
    db.commit()
    
    return {"message": f"User {'activated' if user.is_active else 'deactivated'} successfully"}
