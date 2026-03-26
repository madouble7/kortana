"""
Response Caching Middleware for Kor'tana
Provides intelligent HTTP caching to reduce GitHub API calls and improve performance
Supports cache busting, conditional requests (ETag/Last-Modified), and cache analytics
"""

import hashlib
import json
import time
from typing import Callable

from fastapi import Request, Response
from redis import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

from src.kortana.logger import get_logger

logger = get_logger(__name__)

# Circuit-breaker cooldown for Redis connection failures.
_CACHE_CIRCUIT_BREAKER_SECONDS = 60
DEFAULT_CACHE_EXCLUDE_PATHS = [
    "/health",
    "/docs",
    "/openapi.json",
    "/protocol/auto/execute",
    "/api/tasks/execute",
    "/api/health",
    "/api/system/health",
    "/api/autonomy",
    "/api/autonomous",
    "/api/always-on",
    "/api/daemon",
    "/api/intelligence",
    "/api/task-queue",
]


class CacheStrategy:
    """Cache strategy configuration"""

    def __init__(
        self,
        ttl: int = 300,  # 5 minutes default
        key_prefix: str = "cache:",
        include_status_codes: list[int] = None,
        exclude_paths: list[str] = None,
    ):
        self.ttl = ttl
        self.key_prefix = key_prefix
        self.include_status_codes = include_status_codes or [200, 404]
        self.exclude_paths = exclude_paths or list(DEFAULT_CACHE_EXCLUDE_PATHS)


class ResponseCacheMiddleware(BaseHTTPMiddleware):
    """
    Intelligent response caching middleware
    - Caches GET responses in Redis
    - Supports cache invalidation via POST/PUT/DELETE
    - Adds cache-control headers
    - Provides cache statistics
    """

    def __init__(self, app, redis_client: Redis, strategy: CacheStrategy = None):
        super().__init__(app)
        self.redis = redis_client
        self.strategy = strategy or CacheStrategy()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "bypassed": 0,
            "errors": 0,
        }
        self._redis_failed_at: float = 0.0

    def _should_cache(self, request: Request) -> bool:
        """Determine if request should be cached"""
        # Only cache GET requests
        if request.method != "GET":
            return False

        # Skip excluded paths
        for excluded in self.strategy.exclude_paths:
            if request.url.path.startswith(excluded):
                return False

        return True

    def _get_cache_key(self, request: Request) -> str:
        """Generate cache key from request"""
        # Include path, query params, and authorization in key
        path = request.url.path
        query = request.url.query or ""
        auth = request.headers.get("authorization", "")

        key_data = f"{path}?{query}::{auth}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{self.strategy.key_prefix}{path}:{key_hash}"

    def _invalidate_related_cache(self, request: Request) -> None:
        """Invalidate related cache entries on mutations"""
        if request.method in ["POST", "PUT", "DELETE"]:
            # Invalidate cache entries with similar paths
            base_path = request.url.path.rsplit("/", 1)[0]  # Parent path
            patterns = [
                f"{self.strategy.key_prefix}{base_path}:*",
                f"{self.strategy.key_prefix}{base_path}/*",
            ]

            try:
                for pattern in patterns:
                    for key in self.redis.scan_iter(match=pattern):
                        self.redis.delete(key)
                    logger.debug(f"Invalidated cache for path pattern: {pattern}")
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with caching"""
        # If the circuit breaker is open, skip cache entirely.
        if self._redis_failed_at:
            elapsed = time.monotonic() - self._redis_failed_at
            if elapsed < _CACHE_CIRCUIT_BREAKER_SECONDS:
                return await call_next(request)
            self._redis_failed_at = 0.0

        try:
            cache_key = self._get_cache_key(request)

            if self._should_cache(request):
                # Try to get from cache
                try:
                    cached_data = self.redis.get(cache_key)
                    if cached_data:
                        # Parse cached response
                        cache_entry = json.loads(cached_data)
                        body = cache_entry["body"].encode()
                        headers = cache_entry["headers"]

                        # Add cache headers
                        headers[
                            "cache-control"
                        ] = f"max-age={self.strategy.ttl}, stale-while-revalidate=60"
                        headers["x-cache"] = "HIT"
                        headers["age"] = str(int(time.time() - cache_entry["time"]))

                        self.stats["hits"] += 1

                        return StarletteResponse(
                            content=body,
                            status_code=cache_entry["status"],
                            headers=headers,
                            media_type=headers.get("content-type"),
                        )
                except (json.JSONDecodeError, KeyError, ValueError) as e:
                    logger.debug(f"Cache read error for {cache_key}: {e}")
                    self.stats["errors"] += 1

                self.stats["misses"] += 1
            else:
                self.stats["bypassed"] += 1

            # Process request
            response = await call_next(request)

            # Cache successful responses
            if (
                self._should_cache(request)
                and response.status_code in self.strategy.include_status_codes
            ):
                try:
                    body = b""
                    async for chunk in response.body_iterator:
                        body += chunk

                    cache_entry = {
                        "status": response.status_code,
                        "headers": dict(response.headers),
                        "body": body.decode(),
                        "time": time.time(),
                    }

                    try:
                        self.redis.setex(
                            cache_key, self.strategy.ttl, json.dumps(cache_entry)
                        )
                    except Exception as e:
                        logger.warning(f"Cache write error: {e}")
                        self.stats["errors"] += 1

                    # Add cache headers to response
                    response.headers[
                        "cache-control"
                    ] = f"max-age={self.strategy.ttl}, public"
                    response.headers["x-cache"] = "MISS"

                    # Return response with body
                    return StarletteResponse(
                        content=body,
                        status_code=response.status_code,
                        headers=dict(response.headers),
                        media_type=response.media_type,
                    )
                except Exception as e:
                    logger.warning(f"Cache response processing error: {e}")
                    self.stats["errors"] += 1
            else:
                # Invalidate related caches on mutations
                self._invalidate_related_cache(request)
                response.headers["cache-control"] = "no-store"

            return response

        except Exception as e:
            # Open the circuit breaker — one log line, then silence.
            self._redis_failed_at = time.monotonic()
            logger.error(
                f"Cache middleware error (circuit breaker open for "
                f"{_CACHE_CIRCUIT_BREAKER_SECONDS}s): {e}"
            )
            self.stats["errors"] += 1
            return await call_next(request)

    def get_stats(self) -> dict:
        """Get cache statistics"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0

        return {
            "cache_hits": self.stats["hits"],
            "cache_misses": self.stats["misses"],
            "cache_bypassed": self.stats["bypassed"],
            "cache_errors": self.stats["errors"],
            "hit_rate": f"{hit_rate:.1f}%",
            "total_requests": total,
        }

    def reset_stats(self) -> None:
        """Reset statistics counter"""
        self.stats = {"hits": 0, "misses": 0, "bypassed": 0, "errors": 0}
