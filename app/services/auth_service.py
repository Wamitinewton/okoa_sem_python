# app/services/auth_service.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token, 
    verify_token
)
from app.core.config import settings
from app.models.user import User
from app.schemas.user import UserCreate, UserLogin
from app.models.video import SavedVideo
from app.models.note import StudyNote
from app.models.playlist import Playlist

class AuthService:
    """Service class for handling all authentication-related operations"""
    
    def __init__(self):
        pass
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email address"""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Get user by username"""
        return db.query(User).filter(User.username == username).first()
    
    def get_user_by_id(self, db: Session, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return db.query(User).filter(User.id == user_id).first()
    
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user account"""
        
        # Check if email already exists
        if self.get_user_by_email(db, user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if username already exists
        if self.get_user_by_username(db, user_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Validate password strength
        self._validate_password(user_data.password)
        
        # Create user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            is_active=True
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        user = self.get_user_by_email(db, email)
        
        if not user:
            return None
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_user_token(self, user: User) -> Dict[str, Any]:
        """Create access token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id}, 
            expires_delta=access_token_expires
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # in seconds
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username
            }
        }
    
    def get_current_user_from_token(self, db: Session, token: str) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        # Verify token
        payload = verify_token(token)
        if payload is None:
            raise credentials_exception
        
        # Extract user email from token
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        
        # Get user from database
        user = self.get_user_by_email(db, email=email)
        if user is None:
            raise credentials_exception
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is deactivated"
            )
        
        return user
    
    def update_user_password(self, db: Session, user: User, new_password: str) -> User:
        """Update user password"""
        self._validate_password(new_password)
        
        user.hashed_password = get_password_hash(new_password)
        db.commit()
        db.refresh(user)
        
        return user
    
    def deactivate_user(self, db: Session, user: User) -> User:
        """Deactivate user account"""
        user.is_active = False
        db.commit()
        db.refresh(user)
        
        return user
    
    def activate_user(self, db: Session, user: User) -> User:
        """Activate user account"""
        user.is_active = True
        db.commit()
        db.refresh(user)
        
        return user
    
    def update_user_profile(self, db: Session, user: User, update_data: Dict[str, Any]) -> User:
        """Update user profile information"""
        allowed_fields = ['username', 'email']
        
        for field, value in update_data.items():
            if field in allowed_fields and value is not None:
                # Check for conflicts
                if field == 'email' and value != user.email:
                    if self.get_user_by_email(db, value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Email already in use"
                        )
                
                if field == 'username' and value != user.username:
                    if self.get_user_by_username(db, value):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Username already taken"
                        )
                
                setattr(user, field, value)
        
        db.commit()
        db.refresh(user)
        
        return user
    
    def _validate_password(self, password: str) -> None:
        """Validate password strength"""
        min_length = 8
        
        if len(password) < min_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Password must be at least {min_length} characters long"
            )
        
        # Add more password validation rules as needed
        # - Must contain uppercase letter
        # - Must contain lowercase letter  
        # - Must contain number
        # - Must contain special character
        
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        
        if not (has_upper and has_lower and has_digit):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least one uppercase letter, one lowercase letter, and one digit"
            )
    
    def refresh_token(self, db: Session, current_user: User) -> Dict[str, Any]:
        """Generate a new token for the user (refresh token functionality)"""
        return self.create_user_token(current_user)
    
    def get_user_statistics(self, db: Session, user: User) -> Dict[str, Any]:
        """Get user statistics for dashboard"""
        
        
        saved_videos_count = db.query(SavedVideo).filter(SavedVideo.user_id == user.id).count()
        notes_count = db.query(StudyNote).filter(StudyNote.user_id == user.id).count()
        playlists_count = db.query(Playlist).filter(Playlist.user_id == user.id).count()
        
        # Calculate total watch time
        total_watch_time = db.query(SavedVideo.total_watch_time).filter(
            SavedVideo.user_id == user.id
        ).all()
        total_seconds = sum(time[0] or 0 for time in total_watch_time)
        
        return {
            "saved_videos": saved_videos_count,
            "study_notes": notes_count,
            "playlists": playlists_count,
            "total_watch_time_seconds": total_seconds,
            "total_watch_time_formatted": self._format_duration(total_seconds),
            "account_created": user.created_at,
            "last_activity": user.updated_at
        }
    
    def _format_duration(self, seconds: int) -> str:
        """Format duration from seconds to readable format"""
        if seconds < 60:
            return f"{seconds}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes}m {secs}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours}h {minutes}m"

# Create service instance
auth_service = AuthService()