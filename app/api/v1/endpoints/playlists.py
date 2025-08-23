from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.playlist import Playlist, playlist_videos
from app.models.video import SavedVideo
from app.schemas.playlist import (
    PlaylistCreate, Playlist as PlaylistSchema, PlaylistUpdate,
    PlaylistWithVideos, PlaylistVideoAdd
)

router = APIRouter()

@router.post("/", response_model=PlaylistSchema)
def create_playlist(
    playlist: PlaylistCreate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Create a new playlist"""
    db_playlist = Playlist(
        user_id=playlist.user_id,
        name=playlist.name,
        description=playlist.description
    )
    
    db.add(db_playlist)
    db.commit()
    db.refresh(db_playlist)
    return db_playlist

@router.get("/user/{user_id}/", response_model=List[PlaylistSchema])
def get_playlists(
    user_id:int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get user's playlists"""
    playlists = db.query(Playlist).filter(
        Playlist.user_id == user_id
    ).all()
    return playlists

@router.get("/{playlist_id}/{user_id}/", response_model=PlaylistWithVideos)
def get_playlist(
    user_id:int,
    playlist_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get a specific playlist with videos"""
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == user_id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return playlist

@router.put("/{playlist_id}", response_model=PlaylistSchema)
def update_playlist(
    playlist_id: int,
    playlist_update: PlaylistUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Update a playlist"""
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == playlist_update.user_id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    update_data = playlist_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(playlist, field, value)
    
    db.commit()
    db.refresh(playlist)
    return playlist

@router.delete("/{playlist_id}/user/{user_id}/")
def delete_playlist(
    user_id :int,
    playlist_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Delete a playlist"""
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == user_id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    db.delete(playlist)
    db.commit()
    return {"message": "Playlist deleted successfully"}

@router.post("/{playlist_id}/videos")
def add_video_to_playlist(
    playlist_id: int,
    video_data: PlaylistVideoAdd,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Add a video to a playlist"""
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == video_data.user_id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Verify video ownership
    video = db.query(SavedVideo).filter(
        SavedVideo.id == video_data.video_id,
        SavedVideo.user_id == video_data.user_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Check if video is already in playlist
    if video in playlist.videos:
        raise HTTPException(status_code=400, detail="Video already in playlist")
    
    playlist.videos.append(video)
    db.commit()
    
    return {"message": "Video added to playlist successfully"}

@router.delete("/{playlist_id}/videos/{video_id}/user/{user_id}/")
def remove_video_from_playlist(
    user_id:int,
    playlist_id: int,
    video_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Remove a video from a playlist"""
    # Verify playlist ownership
    playlist = db.query(Playlist).filter(
        Playlist.id == playlist_id,
        Playlist.user_id == user_id
    ).first()
    
    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    # Find and remove video from playlist
    video = db.query(SavedVideo).filter(
        SavedVideo.id == video_id,
        SavedVideo.user_id == user_id
    ).first()
    
    if not video or video not in playlist.videos:
        raise HTTPException(status_code=404, detail="Video not found in playlist")
    
    playlist.videos.remove(video)
    db.commit()
    
    return {"message": "Video removed from playlist successfully"}