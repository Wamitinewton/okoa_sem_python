# app/api/v1/endpoints/auth.py - Updated to use AuthService
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.core.database import get_db
from app.core.config import settings
from app.schemas.user import (
    UserCreate, 
    User as UserSchema, 
    Token, 
    UserLogin
)
from app.services.auth_service import auth_service

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    """Dependency to get current user from JWT token"""
    return auth_service.get_current_user_from_token(db, token)

@router.post("/register", response_model=UserSchema)
def register_user(
    user_data: UserCreate, 
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    return auth_service.create_user(db, user_data)

@router.post("/login", response_model=Token)
def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), 
    db: Session = Depends(get_db)
):
    """Login user and return access token"""
    user = auth_service.authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = auth_service.create_user_token(user)
    return {
        "access_token": token_data["access_token"],
        "token_type": token_data["token_type"]
    }

@router.post("/login-json", response_model=Dict[str, Any])
def login_user_json(
    user_credentials: UserLogin, 
    db: Session = Depends(get_db)
):
    """Login user with JSON payload (alternative to form data)"""
    user = auth_service.authenticate_user(
        db, 
        user_credentials.email, 
        user_credentials.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    return auth_service.create_user_token(user)

@router.get("/me", response_model=UserSchema)
def get_current_user_info(
    current_user = Depends(get_current_user)
):
    """Get current user information"""
    return current_user

@router.post("/refresh", response_model=Dict[str, Any])
def refresh_access_token(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    return auth_service.refresh_token(db, current_user)

@router.get("/stats", response_model=Dict[str, Any])
def get_user_statistics(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user statistics for dashboard"""
    return auth_service.get_user_statistics(db, current_user)

@router.put("/password")
def change_password(
    passwords: Dict[str, str],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change user password"""
    current_password = passwords.get("current_password")
    new_password = passwords.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both current_password and new_password are required"
        )
    
    # Verify current password
    if not auth_service.authenticate_user(db, current_user.email, current_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    auth_service.update_user_password(db, current_user, new_password)
    
    return {"message": "Password updated successfully"}

@router.put("/profile", response_model=UserSchema)
def update_user_profile(
    profile_data: Dict[str, Any],
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user profile information"""
    updated_user = auth_service.update_user_profile(db, current_user, profile_data)
    return updated_user

@router.post("/deactivate")
def deactivate_account(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deactivate user account"""
    auth_service.deactivate_user(db, current_user)
    return {"message": "Account deactivated successfully"}

# Admin endpoints (if you need them later)
@router.get("/users", response_model=list[UserSchema])
def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all users (admin only - you'd add admin check here)"""
    # Add admin permission check here
    users = db.query(auth_service.User).offset(skip).limit(limit).all()
    return users