import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.user import User
from app.models.video import SavedVideo
from app.schemas.video import (
    VideoCreate, SavedVideo as SavedVideoSchema, VideoUpdate,
    YouTubeSearchResponse, YouTubeSearchRequest, SaveVideo, SavedVideoRequest
)
from app.services.youtube_service import youtube_service
from app.services.youtube_cache_service import youtube_cache_service
from datetime import datetime
import asyncio

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/search", response_model=YouTubeSearchResponse)
async def search_youtube_videos(
    q: str = Query(..., description="Search query", min_length=1, max_length=500),
    max_results: int = Query(20, le=50, ge=1),
    page_token: Optional[str] = Query(None, max_length=100),
    order: str = Query("relevance", regex="^(relevance|date|rating|viewCount|title)$"),
    # current_user: User = Depends(get_current_user)
):
    """Search YouTube videos with caching and error handling"""
    try:
        if not q or q.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )

        q = q.strip()[:500]
        logger.info(f"Searching YouTube videos: query='{q}', max_results={max_results}, order={order}")

        # Try cache first
        cached_result = await youtube_cache_service.get_cached_search(
            query=q,
            max_results=max_results,
            page_token=page_token,
            order=order,
            is_educational=False
        )

        if cached_result:
            print(f"used cache in search for query: '{q}'")
            logger.info(f"Cache hit for query: '{q}'")
            return cached_result

        # Fetch from YouTube API
        try:
            result = await asyncio.wait_for(
                youtube_service.search_videos(q, max_results, page_token, order),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"YouTube API timeout for query: '{q}'")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="YouTube search request timed out. Please try again."
            )
        except Exception as youtube_error:
            logger.error(f"YouTube API error for query '{q}': {str(youtube_error)}")
            if "quota" in str(youtube_error).lower():
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="YouTube API quota exceeded. Please try again later."
                )
            elif "invalid" in str(youtube_error).lower():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid search parameters provided"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="YouTube service is temporarily unavailable"
                )

        if not result or not hasattr(result, 'videos'):
            logger.warning(f"Invalid YouTube API response for query: '{q}'")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Invalid response from YouTube service"
            )

        try:
            await youtube_cache_service.cache_search_results(
                query=q,
                max_results=max_results,
                page_token=page_token,
                order=order,
                results=result,
                is_educational=False
            )
            logger.info(f"Cached search result for query: '{q}'")
        except Exception as cache_error:
            logger.warning(f"Failed to cache search result: {str(cache_error)}")

        print(f"didn't use cache in search for query: '{q}'")
        return result

    except ValidationError as e:
        logger.error(f"Validation error in search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid request parameters: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during search"
        )


@router.get("/search/educational", response_model=YouTubeSearchResponse)
async def search_educational_videos(
    q: str = Query(..., description="Search query", min_length=1, max_length=500),
    max_results: int = Query(20, le=50, ge=1),
    # current_user: User = Depends(get_current_user)
):
    """Search specifically for educational content with caching and error handling"""
    try:
        if not q or q.strip() == "":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query cannot be empty"
            )

        q = q.strip()[:500]
        logger.info(f"Searching educational videos: query='{q}', max_results={max_results}")

        cached_result = await youtube_cache_service.get_cached_search(
            query=q,
            max_results=max_results,
            page_token=None,
            order="relevance",
            is_educational=True
        )

        if cached_result:
            logger.info(f"Cache hit for educational query: '{q}'")
            return cached_result

        try:
            result = await asyncio.wait_for(
                youtube_service.search_educational_videos(q, max_results),
                timeout=30.0
            )
        except asyncio.TimeoutError:
            logger.error(f"Educational YouTube API timeout for query: '{q}'")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail="Educational video search timed out. Please try again."
            )
        except Exception as youtube_error:
            logger.error(f"Educational YouTube API error: {str(youtube_error)}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Educational video search service temporarily unavailable"
            )

        try:
            await youtube_cache_service.cache_search_results(
                query=q,
                max_results=max_results,
                page_token=None,
                order="relevance",
                results=result,
                is_educational=True
            )
        except Exception as cache_error:
            logger.warning(f"Failed to cache educational search result: {str(cache_error)}")

        return result

    except Exception as e:
        logger.error(f"Unexpected error in educational search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during educational video search"
        )


@router.post("/save", response_model=SavedVideoSchema)
async def save_video(
    request: SaveVideo,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Save a video to user's library with error handling"""
    try:
        if not request.youtube_id or not request.youtube_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="YouTube video ID is required"
            )

        if not request.title or not request.title.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Video title is required"
            )

        if request.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        logger.info(f"Saving video {request.youtube_id} for user {request.user_id}")

        try:
            existing_video = db.query(SavedVideo).filter(
                SavedVideo.user_id == request.user_id,
                SavedVideo.youtube_id == request.youtube_id
            ).first()

            if existing_video:
                logger.warning(f"Video {request.youtube_id} already saved by user {request.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Video is already saved in your library"
                )

        except SQLAlchemyError as db_error:
            logger.error(f"Database error checking existing video: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database error occurred while checking existing videos"
            )

        video_info = None
        try:
            video_info = await asyncio.wait_for(
                youtube_service.get_video_info(request.youtube_id),
                timeout=15.0
            )
        except asyncio.TimeoutError:
            logger.warning(f"YouTube API timeout getting info for video {request.youtube_id}")
        except Exception as youtube_error:
            logger.warning(f"Failed to get YouTube video info: {str(youtube_error)}")

        try:
            db_video = SavedVideo(
                user_id=request.user_id,
                youtube_id=request.youtube_id.strip(),
                title=request.title.strip()[:255],
                description=request.description[:1000] if request.description else None,
                thumbnail_url=request.thumbnail_url,
                channel_title=request.channel_title[:100] if request.channel_title else None,
                duration=video_info.get("duration") if video_info else request.duration,
                category=request.category or "general",
                published_at=None
            )

            if video_info and video_info.get("published_at"):
                try:
                    db_video.published_at = datetime.fromisoformat(
                        video_info["published_at"].replace("Z", "+00:00")
                    )
                except ValueError as date_error:
                    logger.warning(f"Invalid published_at format: {str(date_error)}")

            db.add(db_video)
            db.commit()
            db.refresh(db_video)

            logger.info(f"Successfully saved video {request.youtube_id} for user {request.user_id}")
            return db_video

        except SQLAlchemyError as db_error:
            db.rollback()
            logger.error(f"Database error saving video: {str(db_error)}")
            if "duplicate" in str(db_error).lower():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Video is already saved"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save video to database"
                )

    except ValidationError as e:
        logger.error(f"Validation error saving video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid video data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error saving video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while saving the video"
        )


@router.get("/saved/{user_id}", response_model=List[SavedVideoSchema])
def get_saved_videos(
    user_id: int,
    category: Optional[str] = Query(None, max_length=50),
    skip: int = Query(0, ge=0, le=10000),
    limit: int = Query(100, le=100, ge=1),
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get user's saved videos with error handling"""
    try:
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        logger.info(f"Getting saved videos for user {user_id}, category={category}")

        # Build query
        query = db.query(SavedVideo).filter(SavedVideo.user_id == user_id)
        
        if category and category.strip():
            query = query.filter(SavedVideo.category == category.strip())
        
        # Execute query with error handling
        try:
            videos = query.order_by(SavedVideo.saved_at.desc()).offset(skip).limit(limit).all()
            logger.info(f"Retrieved {len(videos)} saved videos for user {user_id}")
            return videos

        except SQLAlchemyError as db_error:
            logger.error(f"Database error getting saved videos: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve saved videos"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting saved videos: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving videos"
        )

@router.get("/saved/{video_id}/user/{user_id}", response_model=SavedVideoSchema)
def get_saved_video(
    video_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get a specific saved video with error handling"""
    try:
        # Validate IDs
        if video_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID"
            )
        
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        logger.info(f"Getting saved video {video_id} for user {user_id}")

        try:
            video = db.query(SavedVideo).filter(
                SavedVideo.id == video_id,
                SavedVideo.user_id == user_id
            ).first()

            if not video:
                logger.warning(f"Video {video_id} not found for user {user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found in your library"
                )

            return video

        except SQLAlchemyError as db_error:
            logger.error(f"Database error getting saved video: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve video"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting saved video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving the video"
        )

@router.put("/saved/{video_id}", response_model=SavedVideoSchema)
def update_saved_video(
    video_id: int,
    video_update: VideoUpdate,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Update video progress and metadata with error handling"""
    try:
        # Validate IDs
        if video_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID"
            )
        
        if video_update.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        # Validate progress values
        if video_update.watch_progress is not None:
            if not (0.0 <= video_update.watch_progress <= 1.0):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Watch progress must be between 0.0 and 1.0"
                )

        if video_update.total_watch_time is not None:
            if video_update.total_watch_time < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Total watch time cannot be negative"
                )

        logger.info(f"Updating video {video_id} for user {video_update.user_id}")

        try:
            video = db.query(SavedVideo).filter(
                SavedVideo.id == video_id,
                SavedVideo.user_id == video_update.user_id
            ).first()

            if not video:
                logger.warning(f"Video {video_id} not found for user {video_update.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found in your library"
                )

            # Update fields
            update_data = video_update.dict(exclude_unset=True, exclude={'user_id'})
            
            # Update last_watched if watch_progress is updated
            if "watch_progress" in update_data:
                update_data["last_watched"] = datetime.utcnow()

            for field, value in update_data.items():
                if hasattr(video, field):
                    setattr(video, field, value)

            db.commit()
            db.refresh(video)

            logger.info(f"Successfully updated video {video_id}")
            return video

        except SQLAlchemyError as db_error:
            db.rollback()
            logger.error(f"Database error updating video: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update video"
            )

    except HTTPException:
        raise
    except ValidationError as e:
        logger.error(f"Validation error updating video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid update data: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error updating video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while updating the video"
        )

@router.delete("/saved/{video_id}")
def delete_saved_video(
    request: SavedVideoRequest,
    video_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Delete a saved video with error handling"""
    try:
        # Validate IDs
        if video_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid video ID"
            )
        
        if request.user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        logger.info(f"Deleting video {video_id} for user {request.user_id}")

        try:
            video = db.query(SavedVideo).filter(
                SavedVideo.id == video_id,
                SavedVideo.user_id == request.user_id
            ).first()

            if not video:
                logger.warning(f"Video {video_id} not found for user {request.user_id}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Video not found in your library"
                )

            db.delete(video)
            db.commit()

            logger.info(f"Successfully deleted video {video_id}")
            return {"message": "Video deleted successfully"}

        except SQLAlchemyError as db_error:
            db.rollback()
            logger.error(f"Database error deleting video: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete video"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error deleting video: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while deleting the video"
        )

@router.get("/categories/{user_id}")
def get_video_categories(
    user_id: int,
    db: Session = Depends(get_db),
    # current_user: User = Depends(get_current_user)
):
    """Get all categories used by the user with error handling"""
    try:
        # Validate user_id
        if user_id <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid user ID"
            )

        logger.info(f"Getting video categories for user {user_id}")

        try:
            categories = db.query(SavedVideo.category).filter(
                SavedVideo.user_id == user_id
            ).distinct().all()

            category_list = [cat[0] for cat in categories if cat[0] and cat[0].strip()]
            
            logger.info(f"Retrieved {len(category_list)} categories for user {user_id}")
            return {"categories": sorted(category_list)}

        except SQLAlchemyError as db_error:
            logger.error(f"Database error getting categories: {str(db_error)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve video categories"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting categories: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while retrieving categories"
        )

# Cache management endpoints with error handling
@router.get("/cache/stats")
async def get_cache_stats():
    """Get cache statistics with error handling"""
    try:
        stats = await youtube_cache_service.get_cache_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )

@router.post("/cache/clear")
async def clear_cache(pattern: Optional[str] = Query(None, max_length=100)):
    """Clear cache with error handling"""
    try:
        cleared_count = await youtube_cache_service.invalidate_search_cache(pattern)
        logger.info(f"Cleared {cleared_count} cache entries with pattern: {pattern}")
        return {"message": f"Cleared {cleared_count} cache entries"}
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )