from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class StudyNote(Base):
    __tablename__ = "study_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    video_id = Column(Integer, ForeignKey("saved_videos.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    timestamp = Column(Float, default=0.0)  # Video timestamp in seconds
    tags = Column(String)  # JSON string of tags
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="study_notes")
    video = relationship("SavedVideo", back_populates="study_notes")
