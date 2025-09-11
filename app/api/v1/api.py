from fastapi import APIRouter
from app.api.v1.endpoints import auth, videos, notes, playlists,pdf_analyzer

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(videos.router, prefix="/videos", tags=["videos"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(playlists.router, prefix="/playlists", tags=["playlists"])
api_router.include_router(pdf_analyzer.router,prefix="/pdfs", tags=["pdfs"])
