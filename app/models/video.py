from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class SavedVideo(Base):
    __tablename__ = "saved_videos"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    youtube_id = Column(String, nullable=False, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    thumbnail_url = Column(String)
    channel_title = Column(String)
    duration = Column(String)
    published_at = Column(DateTime)
    category = Column(String, default="general")
    
    # Study progress tracking
    watch_progress = Column(Float, default=0.0)  # 0.0 to 1.0
    total_watch_time = Column(Integer, default=0)  # in seconds
    last_watched = Column(DateTime)
    
    # Timestamps
    saved_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="saved_videos")
    study_notes = relationship("StudyNote", back_populates="video")
