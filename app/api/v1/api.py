from fastapi import APIRouter
from app.api.v1.endpoints import auth, videos, notes, playlists

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
