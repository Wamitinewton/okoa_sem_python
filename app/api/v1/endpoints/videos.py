from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.video import SavedVideo
from app.schemas.video import (
    VideoCreate, SavedVideo as SavedVideoSchema, VideoUpdate,
    YouTubeSearchResponse,YouTubeSearchRequest,SaveVideo,SavedVideoRequest
)
from app.services.youtube_service import youtube_service
from datetime import datetime

router = APIRouter()

@router.get("/search", response_model=YouTubeSearchResponse)
async def search_youtube_videos(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(20, le=50),
    page_token: Optional[str] = Query(None),
    order: str = Query("relevance", regex="^(relevance|date|rating|viewCount|title)$"),
    # current_user: User = Depends(get_current_user)
):
    """Search YouTube videos"""
    return await youtube_service.search_videos(q, max_results, page_token, order)

@router.get("/search/educational", response_model=YouTubeSearchResponse)
async def search_educational_videos(
    q: str = Query(..., description="Search query"),
    max_results: int = Query(20, le=50),
    # current_user: User = Depends(get_current_user)
):
    """Search specifically for educational content"""
    return await youtube_service.search_educational_videos(q, max_results)

@router.post("/save", response_model=SavedVideoSchema)
async def save_video(
    request: SaveVideo,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Save a video to user's library"""
    # Check if video is already saved
    existing_video = db.query(SavedVideo).filter(
        SavedVideo.user_id == request.user_id,
        SavedVideo.youtube_id == request.youtube_id
    ).first()
    
    if existing_video:
        raise HTTPException(status_code=400, detail="Video already saved")
    
    # Get additional video details from YouTube
    video_info = await youtube_service.get_video_info(request.youtube_id)
    
    db_video = SavedVideo(
        user_id=request.user_id,
        youtube_id=request.youtube_id,
        title=request.title,
        description=request.description,
        thumbnail_url=request.thumbnail_url,
        channel_title=request.channel_title,
        duration=video_info.get("duration") if video_info else request.duration,
        category=request.category,
        published_at=datetime.fromisoformat(video_info["published_at"].replace("Z", "+00:00")) if video_info and video_info.get("published_at") else None
    )
    
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video

@router.get("/saved/{user_id}", response_model=List[SavedVideoSchema])
def get_saved_videos(
    user_id: int,
    category: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get user's saved videos"""
    query = db.query(SavedVideo).filter(SavedVideo.user_id == user_id)
    
    if category:
        query = query.filter(SavedVideo.category == category)
    
    videos = query.offset(skip).limit(limit).all()
    return videos

@router.get("/saved/{video_id}/user/{user_id}", response_model=SavedVideoSchema)
def get_saved_video(
    video_id: int,
    user_id:int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get a specific saved video"""
    video = db.query(SavedVideo).filter(
        SavedVideo.id == video_id,
        SavedVideo.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video

@router.put("/saved/{video_id}", response_model=SavedVideoSchema)
def update_saved_video(
    # request: SavedVideoRequest,
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Update video progress and metadata"""
    video = db.query(SavedVideo).filter(
        SavedVideo.id == video_id,
        SavedVideo.user_id == video_update.user_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    update_data = video_update.dict(exclude_unset=True)
    
    # Update last_watched if watch_progress is updated
    if "watch_progress" in update_data:
        update_data["last_watched"] = datetime.utcnow()
    
    for field, value in update_data.items():
        setattr(video, field, value)
    
    db.commit()
    db.refresh(video)
    return video

@router.delete("/saved/{video_id}")
def delete_saved_video(
    request:SavedVideoRequest,
    video_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Delete a saved video"""
    video = db.query(SavedVideo).filter(
        SavedVideo.id == video_id,
        SavedVideo.user_id == request.user_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    db.delete(video)
    db.commit()
    return {"message": "Video deleted successfully"}

@router.get("/categories/{user_id}")
def get_video_categories(
    user_id:int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get all categories used by the user"""
    categories = db.query(SavedVideo.category).filter(
        SavedVideo.user_id == user_id
    ).distinct().all()
    
    return {"categories": [cat[0] for cat in categories if cat[0]]}
