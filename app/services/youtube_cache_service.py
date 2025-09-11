import json
import hashlib
from typing import Optional, Dict, Any
from app.core.config import settings
from app.schemas.video import YouTubeSearchResponse
import redis.asyncio as redis  # use async client
from datetime import timedelta

from sentence_transformers import SentenceTransformer, util
import numpy as np

class YouTubeCacheService:
    def __init__(self):
        self.redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=False  # embeddings will be binary
        )
        self.default_ttl = 3600  # 1 hour
        self.educational_ttl = 7200  # 2 hours
        self.prefix = "youtube_search"

        # NEW: embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_dim = 384  # embedding size for this model
        self.similarity_threshold = 0.8  # adjust as needed

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

    async def _store_embedding(self, query: str, cache_key: str, ttl: int):
        """Store query embedding for later similarity search"""
        embedding = self.model.encode(query, normalize_embeddings=True).astype(np.float32).tobytes()
        meta_key = f"{cache_key}:meta"
        await self.redis_client.hset(meta_key, mapping={
            "query": query.lower().strip(),
            "embedding": embedding
        })
        await self.redis_client.expire(meta_key, ttl)

    async def _find_similar_query(self, query: str) -> Optional[str]:
        """Find similar cached query by comparing embeddings"""
        # fetch all meta keys
        meta_keys = await self.redis_client.keys(f"{self.prefix}:*:meta")
        if not meta_keys:
            return None

        query_emb = self.model.encode(query, normalize_embeddings=True)

        best_key = None
        best_score = -1.0

        for meta_key in meta_keys:
            data = await self.redis_client.hgetall(meta_key)
            if not data or b"embedding" not in data:
                continue

            emb_bytes = data[b"embedding"]
            emb = np.frombuffer(emb_bytes, dtype=np.float32)

            sim = util.cos_sim(query_emb, emb).item()
            if sim > best_score:
                best_score = sim
                best_key = meta_key

        if best_key and best_score >= self.similarity_threshold:
            return best_key.decode().replace(":meta", "")
        return None

    async def get_cached_search(
        self,
        query: str,
        max_results: int,
        page_token: Optional[str],
        order: str,
        is_educational: bool = False,
    ) -> Optional[YouTubeSearchResponse]:
        """Get cached search results if available (with semantic similarity)"""
        try:
            # exact match first
            cache_key = self._generate_cache_key(query, max_results, page_token, order, is_educational)
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                return YouTubeSearchResponse(**data)

            # try semantic similarity
            similar_key = await self._find_similar_query(query)
            if similar_key:
                cached_data = await self.redis_client.get(similar_key)
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
        """Cache search results (with embeddings)"""
        try:
            cache_key = self._generate_cache_key(query, max_results, page_token, order, is_educational)
            cache_data = results.model_dump_json()
            ttl = self.educational_ttl if is_educational else self.default_ttl

            await self.redis_client.setex(cache_key, ttl, cache_data)
            await self._store_embedding(query, cache_key, ttl)

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