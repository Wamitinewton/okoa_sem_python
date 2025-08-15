from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

class VideoBase(BaseModel):
    youtube_id: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    channel_title: Optional[str] = None
    duration: Optional[str] = None
    category: str = "general"

class VideoCreate(VideoBase):
    pass

class VideoUpdate(BaseModel):
    category: Optional[str] = None
    watch_progress: Optional[float] = None
    total_watch_time: Optional[int] = None

class SavedVideo(VideoBase):
    id: int
    user_id: int
    watch_progress: float
    total_watch_time: int
    last_watched: Optional[datetime]
    saved_at: datetime
    published_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class YouTubeSearchResult(BaseModel):
    id: str
    title: str
    description: str
    thumbnail_url: str
    channel_title: str
    published_at: str
    duration: Optional[str] = None
    view_count: Optional[str] = None

class YouTubeSearchResponse(BaseModel):
    videos: List[YouTubeSearchResult]
    total_results: int
    next_page_token: Optional[str] = None
