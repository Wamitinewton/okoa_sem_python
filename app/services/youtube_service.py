import httpx
import re
from datetime import datetime
from typing import List, Optional, Dict, Any
from app.core.config import settings
from app.schemas.video import YouTubeSearchResult, YouTubeSearchResponse

class YouTubeService:
    def __init__(self):
        self.api_key = settings.YOUTUBE_API_KEY
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    async def search_videos(
        self, 
        query: str, 
        max_results: int = 20,
        page_token: Optional[str] = None,
        order: str = "relevance"  # relevance, date, rating, viewCount, title
    ) -> YouTubeSearchResponse:
        """Search for YouTube videos"""
        
        params = {
            "part": "snippet",
            "type": "video",
            "q": query,
            "maxResults": max_results,
            "order": order,
            "key": self.api_key
        }
        
        if page_token:
            params["pageToken"] = page_token
            
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            # Get video IDs for additional details
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            video_details = await self._get_video_details(video_ids) if video_ids else {}
            
            videos = []
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                details = video_details.get(video_id, {})
                
                video = YouTubeSearchResult(
                    id=video_id,
                    title=snippet["title"],
                    description=snippet["description"],
                    thumbnail_url=snippet["thumbnails"]["medium"]["url"],
                    channel_title=snippet["channelTitle"],
                    published_at=snippet["publishedAt"],
                    duration=details.get("duration"),
                    view_count=details.get("viewCount")
                )
                videos.append(video)
            
            return YouTubeSearchResponse(
                videos=videos,
                total_results=data.get("pageInfo", {}).get("totalResults", 0),
                next_page_token=data.get("nextPageToken")
            )
    
    async def _get_video_details(self, video_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get detailed information for videos"""
        
        if not video_ids:
            return {}
            
        params = {
            "part": "contentDetails,statistics",
            "id": ",".join(video_ids),
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/videos", params=params)
            response.raise_for_status()
            data = response.json()
            
            result = {}
            for item in data.get("items", []):
                video_id = item["id"]
                content_details = item.get("contentDetails", {})
                statistics = item.get("statistics", {})
                
                result[video_id] = {
                    "duration": self._parse_duration(content_details.get("duration", "")),
                    "viewCount": statistics.get("viewCount")
                }
            
            return result
    
    async def get_video_info(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information for a single video"""
        
        params = {
            "part": "snippet,contentDetails,statistics",
            "id": video_id,
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/videos", params=params)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            if not items:
                return None
                
            item = items[0]
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {})
            statistics = item.get("statistics", {})
            
            return {
                "id": video_id,
                "title": snippet.get("title"),
                "description": snippet.get("description"),
                "thumbnail_url": snippet.get("thumbnails", {}).get("medium", {}).get("url"),
                "channel_title": snippet.get("channelTitle"),
                "published_at": snippet.get("publishedAt"),
                "duration": self._parse_duration(content_details.get("duration", "")),
                "view_count": statistics.get("viewCount"),
                "like_count": statistics.get("likeCount"),
                "comment_count": statistics.get("commentCount")
            }
    
    def _parse_duration(self, duration: str) -> str:
        """Convert ISO 8601 duration to readable format (PT4M13S -> 4:13)"""
        if not duration:
            return ""
            
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if not match:
            return ""
            
        hours = int(match.group(1)) if match.group(1) else 0
        minutes = int(match.group(2)) if match.group(2) else 0
        seconds = int(match.group(3)) if match.group(3) else 0
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    async def search_educational_videos(
        self, 
        query: str, 
        max_results: int = 20
    ) -> YouTubeSearchResponse:
        """Search specifically for educational content"""
        
        # Add educational keywords to improve results
        educational_query = f"{query} tutorial education learn"
        
        params = {
            "part": "snippet",
            "type": "video",
            "q": educational_query,
            "maxResults": max_results,
            "order": "relevance",
            "videoCategoryId": "27",  # Education category
            "key": self.api_key
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/search", params=params)
            response.raise_for_status()
            data = response.json()
            
            video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
            video_details = await self._get_video_details(video_ids) if video_ids else {}
            
            videos = []
            for item in data.get("items", []):
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]
                details = video_details.get(video_id, {})
                
                video = YouTubeSearchResult(
                    id=video_id,
                    title=snippet["title"],
                    description=snippet["description"],
                    thumbnail_url=snippet["thumbnails"]["medium"]["url"],
                    channel_title=snippet["channelTitle"],
                    published_at=snippet["publishedAt"],
                    duration=details.get("duration"),
                    view_count=details.get("viewCount")
                )
                videos.append(video)
            
            return YouTubeSearchResponse(
                videos=videos,
                total_results=data.get("pageInfo", {}).get("totalResults", 0),
                next_page_token=data.get("nextPageToken")
            )

# Create service instance
youtube_service = YouTubeService()