from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional

class NoteBase(BaseModel):
    content: str
    timestamp: float = 0.0
    tags: Optional[List[str]] = []

class NoteCreate(NoteBase):
    video_id: int

class NoteUpdate(BaseModel):
    content: Optional[str] = None
    timestamp: Optional[float] = None
    tags: Optional[List[str]] = None

class StudyNote(NoteBase):
    id: int
    user_id: int
    video_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

