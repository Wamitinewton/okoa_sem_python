from typing import Dict, Any, List
import json
from datetime import datetime
from fastapi import HTTPException, status
from app.schemas.video import SaveVideo

def serialize_tags(tags: List[str]) -> str:
    """Serialize tags list to JSON string"""
    return json.dumps(tags) if tags else "[]"

def deserialize_tags(tags_json: str) -> List[str]:
    """Deserialize tags from JSON string to list"""
    try:
        return json.loads(tags_json) if tags_json else []
    except json.JSONDecodeError:
        return []

def format_duration_seconds(seconds: int) -> str:
    """Convert seconds to HH:MM:SS or MM:SS format"""
    if seconds < 0:
        return "0:00"
    
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"

def calculate_watch_progress(current_time: int, total_duration: int) -> float:
    """Calculate watch progress as a percentage (0.0 to 1.0)"""
    if total_duration <= 0:
        return 0.0
    
    progress = current_time / total_duration
    return min(max(progress, 0.0), 1.0)

def extract_video_id_from_url(url: str) -> str:
    """Extract YouTube video ID from various YouTube URL formats"""
    import re
    
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
        r'youtube\.com/v/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already a video ID
    return url

def paginate_query(query, page: int = 1, per_page: int = 20):
    """Add pagination to SQLAlchemy query"""
    total = query.count()
    
    if page < 1:
        page = 1
    
    offset = (page - 1) * per_page
    items = query.offset(offset).limit(per_page).all()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page
    }

def validate_youtube_api_key(api_key: str) -> bool:
    """Basic validation for YouTube API key format"""
    if not api_key:
        return False
    
    # YouTube API keys are typically 39 characters long
    # and contain only alphanumeric characters and underscores/hyphens
    import re
    pattern = r'^[A-Za-z0-9_-]{35,45}$'
    return bool(re.match(pattern, api_key))