"""
Redis-based caching layer for Kor'tana Backend
Provides high-performance caching with TTL management and metrics
"""

import hashlib
import json
import time
from typing import Any

try:
    import redis
    from redis.asyncio import Redis as AsyncRedis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️  Redis not available. Install: pip install redis aioredis")

from src.kortana.logger import get_logger

logger = get_logger(__name__)


class CacheConfig:
    """Cache configuration"""

    def __init__(self):
        self.host = "localhost"
        self.port = 6379
        self.db = 0
        self.password = None
        self.ttl = 300  # 5 minutes default
        self.enabled = True

    @classmethod
    def from_env(cls):
        """Load from environment"""
        import os

        config = cls()
        config.host = os.getenv("REDIS_HOST", "localhost")
        config.port = int(os.getenv("REDIS_PORT", 6379))
        config.db = int(os.getenv("REDIS_DB", 0))
        config.password = os.getenv("REDIS_PASSWORD")
        config.ttl = int(os.getenv("CACHE_TTL", 300))
        config.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        return config


class CacheMetrics:
    """Track cache performance"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.evictions = 0
        self.total_get_time = 0.0
        self.total_set_time = 0.0

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0

    def avg_get_time(self) -> float:
        return self.total_get_time / max(self.hits + self.misses, 1)

    def avg_set_time(self) -> float:
        return self.total_set_time / max(self.hits + self.misses, 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_rate": round(self.hit_rate(), 2),
            "avg_get_ms": round(self.avg_get_time() * 1000, 2),
            "avg_set_ms": round(self.avg_set_time() * 1000, 2),
        }


class CacheManager:
    """Main cache manager with sync and async support"""

    def __init__(self, config: CacheConfig | None = None):
        self.config = config or CacheConfig.from_env()
        self.metrics = CacheMetrics()
        self._client = None
        self._async_client = None

        if not REDIS_AVAILABLE:
            self.config.enabled = False
            logger.warning("Redis not available, caching disabled")

    def _get_client(self):
        """Get synchronous Redis client"""
        if not self._client and REDIS_AVAILABLE:
            try:
                self._client = redis.Redis(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    decode_responses=True,
                )
                # Test connection
                self._client.ping()
                logger.info(f"Redis connected: {self.config.host}:{self.config.port}")
            except Exception as e:
                logger.error(f"Redis connection failed: {e}")
                self.config.enabled = False
        return self._client

    async def _get_async_client(self):
        """Get asynchronous Redis client"""
        if not self._async_client and REDIS_AVAILABLE:
            try:
                self._async_client = AsyncRedis(
                    host=self.config.host,
                    port=self.config.port,
                    db=self.config.db,
                    password=self.config.password,
                    decode_responses=True,
                )
                await self._async_client.ping()
                logger.info(f"Async Redis connected: {self.config.host}:{self.config.port}")
            except Exception as e:
                logger.error(f"Async Redis connection failed: {e}")
                self.config.enabled = False
        return self._async_client

    def generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from arguments"""
        key_data = f"{prefix}:{str(args)}:{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Any | None:
        """Get value from src.kortana.cache (sync)"""
        if not self.config.enabled:
            return None

        start = time.time()
        try:
            client = self._get_client()
            if not client:
                return None

            value = client.get(key)
            self.metrics.total_get_time += time.time() - start

            if value:
                self.metrics.hits += 1
                logger.debug(f"Cache HIT: {key}")
                return json.loads(value)
            else:
                self.metrics.misses += 1
                logger.debug(f"Cache MISS: {key}")
                return None

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Cache GET error: {e}")
            return None

    async def async_get(self, key: str) -> Any | None:
        """Get value from src.kortana.cache (async)"""
        if not self.config.enabled:
            return None

        start = time.time()
        try:
            client = await self._get_async_client()
            if not client:
                return None

            value = await client.get(key)
            self.metrics.total_get_time += time.time() - start

            if value:
                self.metrics.hits += 1
                logger.debug(f"Async Cache HIT: {key}")
                return json.loads(value)
            else:
                self.metrics.misses += 1
                logger.debug(f"Async Cache MISS: {key}")
                return None

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Async Cache GET error: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache (sync)"""
        if not self.config.enabled:
            return False

        start = time.time()
        try:
            client = self._get_client()
            if not client:
                return False

            ttl = ttl or self.config.ttl
            client.setex(key, ttl, json.dumps(value))
            self.metrics.total_set_time += time.time() - start
            logger.debug(f"Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Cache SET error: {e}")
            return False

    async def async_set(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """Set value in cache (async)"""
        if not self.config.enabled:
            return False

        start = time.time()
        try:
            client = await self._get_async_client()
            if not client:
                return False

            ttl = ttl or self.config.ttl
            await client.setex(key, ttl, json.dumps(value))
            self.metrics.total_set_time += time.time() - start
            logger.debug(f"Async Cache SET: {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            self.metrics.errors += 1
            logger.error(f"Async Cache SET error: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete key from src.kortana.cache"""
        if not self.config.enabled:
            return False

        try:
            client = self._get_client()
            if not client:
                return False

            result = client.delete(key)
            if result:
                self.metrics.evictions += 1
                logger.debug(f"Cache DELETE: {key}")
            return bool(result)

        except Exception as e:
            logger.error(f"Cache DELETE error: {e}")
            return False

    async def async_delete(self, key: str) -> bool:
        """Delete key from src.kortana.cache (async)"""
        if not self.config.enabled:
            return False

        try:
            client = await self._get_async_client()
            if not client:
                return False

            result = await client.delete(key)
            if result:
                self.metrics.evictions += 1
                logger.debug(f"Async Cache DELETE: {key}")
            return bool(result)

        except Exception as e:
            logger.error(f"Async Cache DELETE error: {e}")
            return False

    def clear(self, pattern: str = "*") -> int:
        """Clear cache matching pattern"""
        if not self.config.enabled:
            return 0

        try:
            client = self._get_client()
            if not client:
                return 0

            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                self.metrics.evictions += len(keys)
                logger.info(f"Cache CLEAR: {len(keys)} keys deleted")
                return len(keys)
            return 0

        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
            return 0

    def get_metrics(self) -> dict[str, Any]:
        """Get cache performance metrics"""
        return self.metrics.to_dict()

    def is_available(self) -> bool:
        """Check if cache is available"""
        if not self.config.enabled:
            return False

        try:
            client = self._get_client()
            if client:
                client.ping()
                return True
            return False
        except:
            return False


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate cache key helper"""
    return get_cache_manager().generate_key(prefix, *args, **kwargs)


# Decorator for caching function results
def cache_result(ttl: int | None = None, key_prefix: str = "func"):
    """Decorator to cache function results"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            if not cache.config.enabled:
                return func(*args, **kwargs)

            key = cache.generate_key(key_prefix, *args, **kwargs)
            cached = cache.get(key)

            if cached is not None:
                return cached

            result = func(*args, **kwargs)
            cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


# Async decorator
def cache_result_async(ttl: int | None = None, key_prefix: str = "func"):
    """Decorator to cache async function results"""

    def decorator(func):
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()
            if not cache.config.enabled:
                return await func(*args, **kwargs)

            key = cache.generate_key(key_prefix, *args, **kwargs)
            cached = await cache.async_get(key)

            if cached is not None:
                return cached

            result = await func(*args, **kwargs)
            await cache.async_set(key, result, ttl)
            return result

        return wrapper

    return decorator
