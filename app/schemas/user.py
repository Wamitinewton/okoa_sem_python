from pydantic import BaseModel, EmailStr, validator
from datetime import datetime
from typing import Optional, Dict, Any

class UserBase(BaseModel):
    email: EmailStr
    username: str

class UserCreate(UserBase):
    password: str
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters')
        # Add more username validation as needed
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserWithStats(User):
    """User model with additional statistics"""
    saved_videos_count: Optional[int] = 0
    notes_count: Optional[int] = 0
    playlists_count: Optional[int] = 0
    total_watch_time_seconds: Optional[int] = 0

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenWithUser(Token):
    """Token response with user information"""
    expires_in: int
    user: Dict[str, Any]

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None

class UserStats(BaseModel):
    """User statistics for dashboard"""
    saved_videos: int
    study_notes: int
    playlists: int
    total_watch_time_seconds: int
    total_watch_time_formatted: str
    account_created: datetime
    last_activity: Optional[datetime] = None