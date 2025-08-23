from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from .video import SavedVideo

class PlaylistBase(BaseModel):
    name: str
    description: Optional[str] = None

class PlaylistCreate(PlaylistBase):
    user_id:int

class PlaylistUpdate(BaseModel):
    user_id:int
    name: Optional[str] = None
    description: Optional[str] = None

class Playlist(PlaylistBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PlaylistWithVideos(Playlist):
    videos: List[SavedVideo] = []

class PlaylistVideoAdd(BaseModel):
    user_id:int
    video_id: int
    order_index: Optional[int] = None