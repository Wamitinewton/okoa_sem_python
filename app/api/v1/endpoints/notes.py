from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.note import StudyNote
from app.models.video import SavedVideo
from app.schemas.note import NoteCreate, StudyNote as StudyNoteSchema, NoteUpdate
import json

router = APIRouter()

@router.post("/", response_model=StudyNoteSchema)
def create_note(
    note: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new study note"""
    # Verify that the video belongs to the user
    video = db.query(SavedVideo).filter(
        SavedVideo.id == note.video_id,
        SavedVideo.user_id == current_user.id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    db_note = StudyNote(
        user_id=current_user.id,
        video_id=note.video_id,
        content=note.content,
        timestamp=note.timestamp,
        tags=json.dumps(note.tags) if note.tags else "[]"
    )
    
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    db_note.tags = json.loads(db_note.tags)
    return db_note

@router.get("/", response_model=List[StudyNoteSchema])
def get_notes(
    video_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get user's study notes"""
    query = db.query(StudyNote).filter(StudyNote.user_id == current_user.id)
    
    if video_id:
        query = query.filter(StudyNote.video_id == video_id)
    
    notes = query.offset(skip).limit(limit).all()
    for note in notes:
        note.tags = json.loads(note.tags) if note.tags else []
    return notes

@router.get("/{note_id}", response_model=StudyNoteSchema)
def get_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific note"""
    note = db.query(StudyNote).filter(
        StudyNote.id == note_id,
        StudyNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    note.tags = json.loads(note.tags)
    
    return note

@router.put("/{note_id}", response_model=StudyNoteSchema)
def update_note(
    note_id: int,
    note_update: NoteUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a study note"""
    note = db.query(StudyNote).filter(
        StudyNote.id == note_id,
        StudyNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    update_data = note_update.dict(exclude_unset=True)
    
    # Handle tags serialization
    if "tags" in update_data:
        update_data["tags"] = json.dumps(update_data["tags"])
    
    for field, value in update_data.items():
        setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    note.tags = json.loads(note.tags)
    return note

@router.delete("/{note_id}")
def delete_note(
    note_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a study note"""
    note = db.query(StudyNote).filter(
        StudyNote.id == note_id,
        StudyNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    return {"message": "Note deleted successfully"}
