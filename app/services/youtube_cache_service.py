import json
import hashlib
from typing import Optional, Dict, Any
from app.core.config import settings
from app.schemas.video import YouTubeSearchResponse
import redis.asyncio as redis  # use async client
from datetime import timedelta


class YouTubeCacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True  # returns str instead of bytes
        )
        self.default_ttl = 3600  # 1 hour
        self.educational_ttl = 7200  # 2 hours
        self.prefix = "youtube_search"

    def _generate_cache_key(
        self,
        query: str,
        max_results: int,
        page_token: Optional[str],
        order: str,
        is_educational: bool = True
    ) -> str:
        """Generate a consistent cache key for search parameters"""
        params = {
            "q": query.lower().strip(),
            "max_results": max_results,
            "page_token": page_token or "",
            "order": order,
            "educational": is_educational,
        }
        param_string = json.dumps(params, sort_keys=True)
        hash_key = hashlib.md5(param_string.encode()).hexdigest()
        cache_type = "edu" if is_educational else "search"
        return f"{self.prefix}:{cache_type}:{hash_key}"

    async def get_cached_search(
        self,
        query: str,
        max_results: int,
        page_token: Optional[str],
        order: str,
        is_educational: bool = False,
    ) -> Optional[YouTubeSearchResponse]:
        """Get cached search results if available"""
        try:
            cache_key = self._generate_cache_key(query, max_results, page_token, order, is_educational)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                return YouTubeSearchResponse(**data)

            return None

        except Exception as e:
            print(f"Cache retrieval error: {e}")
            return None

    async def cache_search_results(
        self,
        query: str,
        max_results: int,
        page_token: Optional[str],
        order: str,
        results: YouTubeSearchResponse,
        is_educational: bool = False,
    ) -> None:
        """Cache search results"""
        try:
            cache_key = self._generate_cache_key(query, max_results, page_token, order, is_educational)
            cache_data = results.model_dump_json()
            ttl = self.educational_ttl if is_educational else self.default_ttl
            await self.redis_client.setex(cache_key, ttl, cache_data)

        except Exception as e:
            print(f"Cache storage error: {e}")

    async def invalidate_search_cache(self, pattern: Optional[str] = None) -> int:
        """Invalidate cached search results"""
        try:
            if pattern:
                search_pattern = f"{self.prefix}:{pattern}:*"
            else:
                search_pattern = f"{self.prefix}:*"

            keys = await self.redis_client.keys(search_pattern)
            if keys:
                return await self.redis_client.delete(*keys)
            return 0

        except Exception as e:
            print(f"Cache invalidation error: {e}")
            return 0

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        try:
            search_keys = await self.redis_client.keys(f"{self.prefix}:search:*")
            edu_keys = await self.redis_client.keys(f"{self.prefix}:edu:*")

            return {
                "total_cached_searches": len(search_keys) + len(edu_keys),
                "regular_searches": len(search_keys),
                "educational_searches": len(edu_keys),
                "cache_prefix": self.prefix,
            }

        except Exception as e:
            print(f"Cache stats error: {e}")
            return {"error": str(e)}


# Create service instance
youtube_cache_service = YouTubeCacheService()
