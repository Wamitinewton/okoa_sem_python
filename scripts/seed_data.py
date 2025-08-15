"""
Script to seed the database with sample data
Run with: python scripts/seed_data.py
"""
import asyncio
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.video import SavedVideo
from app.models.note import StudyNote
from app.models.playlist import Playlist
from datetime import datetime, timedelta
import json

def create_sample_user(db: Session) -> User:
    """Create a sample user"""
    user = db.query(User).filter(User.email == "demo@studyapp.com").first()
    
    if not user:
        user = User(
            email="demo@studyapp.com",
            username="demouser",
            hashed_password=get_password_hash("demopassword"),
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print("✅ Sample user created (email: demo@studyapp.com, password: demopassword)")
    else:
        print("✅ Sample user already exists")
    
    return user

def create_sample_videos(db: Session, user: User):
    """Create sample saved videos"""
    sample_videos = [
        {
            "youtube_id": "dQw4w9WgXcQ",
            "title": "Python Programming Tutorial - Learn Python in 10 Minutes",
            "description": "A comprehensive Python programming tutorial for beginners",
            "thumbnail_url": "https://img.youtube.com/vi/dQw4w9WgXcQ/mqdefault.jpg",
            "channel_title": "Programming Channel",
            "duration": "10:30",
            "category": "programming"
        },
        {
            "youtube_id": "abc123def456",
            "title": "Advanced JavaScript Concepts Explained",
            "description": "Deep dive into advanced JavaScript concepts",
            "thumbnail_url": "https://img.youtube.com/vi/abc123def456/mqdefault.jpg",
            "channel_title": "JavaScript Mastery",
            "duration": "25:15",
            "category": "programming"
        },
        {
            "youtube_id": "xyz789uvw012",
            "title": "Machine Learning Fundamentals",
            "description": "Introduction to machine learning algorithms and concepts",
            "thumbnail_url": "https://img.youtube.com/vi/xyz789uvw012/mqdefault.jpg",
            "channel_title": "ML Academy",
            "duration": "45:20",
            "category": "machine-learning"
        }
    ]
    
    for video_data in sample_videos:
        existing_video = db.query(SavedVideo).filter(
            SavedVideo.user_id == user.id,
            SavedVideo.youtube_id == video_data["youtube_id"]
        ).first()
        
        if not existing_video:
            video = SavedVideo(
                user_id=user.id,
                **video_data,
                watch_progress=0.3,  # 30% watched
                total_watch_time=180,  # 3 minutes
                last_watched=datetime.utcnow() - timedelta(days=1)
            )
            db.add(video)
    
    db.commit()
    print("✅ Sample videos created")

def create_sample_notes(db: Session, user: User):
    """Create sample study notes"""
    videos = db.query(SavedVideo).filter(SavedVideo.user_id == user.id).all()
    
    if not videos:
        return
    
    sample_notes = [
        {
            "content": "Important: Remember to use proper variable naming conventions",
            "timestamp": 120.5,
            "tags": ["variables", "best-practices"]
        },
        {
            "content": "Key concept: List comprehensions are more Pythonic than traditional loops",
            "timestamp": 300.0,
            "tags": ["lists", "comprehensions"]
        },
        {
            "content": "Review this section about closures - very important for interviews",
            "timestamp": 890.3,
            "tags": ["closures", "functions", "interview"]
        }
    ]
    
    for i, note_data in enumerate(sample_notes):
        if i < len(videos):
            existing_note = db.query(StudyNote).filter(
                StudyNote.user_id == user.id,
                StudyNote.video_id == videos[i].id,
                StudyNote.content == note_data["content"]
            ).first()
            
            if not existing_note:
                note = StudyNote(
                    user_id=user.id,
                    video_id=videos[i].id,
                    content=note_data["content"],
                    timestamp=note_data["timestamp"],
                    tags=json.dumps(note_data["tags"])
                )
                db.add(note)
    
    db.commit()
    print("✅ Sample notes created")

def create_sample_playlists(db: Session, user: User):
    """Create sample playlists"""
    videos = db.query(SavedVideo).filter(SavedVideo.user_id == user.id).all()
    
    if not videos:
        return
    
    # Create programming playlist
    programming_playlist = db.query(Playlist).filter(
        Playlist.user_id == user.id,
        Playlist.name == "Programming Fundamentals"
    ).first()
    
    if not programming_playlist:
        programming_playlist = Playlist(
            user_id=user.id,
            name="Programming Fundamentals",
            description="Essential programming concepts and tutorials"
        )
        db.add(programming_playlist)
        db.commit()
        db.refresh(programming_playlist)
        
        # Add programming videos to playlist
        programming_videos = [v for v in videos if v.category == "programming"]
        for video in programming_videos:
            programming_playlist.videos.append(video)
        
        db.commit()
        print("✅ Sample playlists created")

def main():
    print("🌱 Seeding database with sample data...")
    
    db = SessionLocal()
    try:
        # Create sample data
        user = create_sample_user(db)
        create_sample_videos(db, user)
        create_sample_notes(db, user)
        create_sample_playlists(db, user)
        
        print("🎉 Database seeded successfully!")
        print("\n📋 Sample data created:")
        print("   👤 Demo user: demo@studyapp.com / demopassword")
        print("   🎥 3 sample videos")
        print("   📝 3 study notes")
        print("   📚 1 playlist")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()