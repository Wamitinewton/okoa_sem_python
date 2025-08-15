from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# Association table for many-to-many relationship
playlist_videos = Table(
    'playlist_videos',
    Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id'), primary_key=True),
    Column('video_id', Integer, ForeignKey('saved_videos.id'), primary_key=True),
    Column('order_index', Integer, default=0),
    Column('added_at', DateTime(timezone=True), server_default=func.now())
)

class Playlist(Base):
    __tablename__ = "playlists"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="playlists")
    videos = relationship("SavedVideo", secondary=playlist_videos, backref="playlists")

class PlaylistVideo(Base):
    __tablename__ = "playlist_video_order"
    
    id = Column(Integer, primary_key=True, index=True)
    playlist_id = Column(Integer, ForeignKey("playlists.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("saved_videos.id"), nullable=False)
    order_index = Column(Integer, default=0)
    added_at = Column(DateTime(timezone=True), server_default=func.now())