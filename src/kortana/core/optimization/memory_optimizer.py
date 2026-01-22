"""
Memory Optimizer inspired by Chromium's PartitionAlloc and caching strategies.

This module provides efficient memory management through:
- LRU caching for frequently accessed data
- Memory pooling to reduce allocation overhead
- Adaptive cache sizing based on usage patterns
"""

import logging
import time
from collections import OrderedDict
from enum import Enum
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CacheStrategy(str, Enum):
    """Cache eviction strategies."""

    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out


class LRUCache(Generic[T]):
    """
    LRU (Least Recently Used) cache implementation.
    
    Inspired by Chromium's caching mechanisms for efficient memory usage.
    """

    def __init__(self, capacity: int = 128):
        """
        Initialize LRU cache.

        Args:
            capacity: Maximum number of items to store
        """
        self.capacity = capacity
        self.cache: OrderedDict[str, tuple[T, float]] = OrderedDict()
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> T | None:
        """
        Get item from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if key in self.cache:
            # Move to end to mark as recently used
            value, _ = self.cache.pop(key)
            self.cache[key] = (value, time.time())
            self.hits += 1
            return value
        self.misses += 1
        return None

    def put(self, key: str, value: T) -> None:
        """
        Put item in cache.

        Args:
            key: Cache key
            value: Value to cache
        """
        if key in self.cache:
            # Update existing entry
            self.cache.pop(key)
        elif len(self.cache) >= self.capacity:
            # Remove oldest entry
            self.cache.popitem(last=False)

        self.cache[key] = (value, time.time())

    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = self.hits + self.misses
        hit_rate = (self.hits / total * 100) if total > 0 else 0

        return {
            "size": len(self.cache),
            "capacity": self.capacity,
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": f"{hit_rate:.2f}%",
        }


class MemoryPool(Generic[T]):
    """
    Memory pool for object reuse to reduce allocation overhead.
    
    Inspired by Chromium's memory pooling strategies.
    """

    def __init__(
        self, factory: Callable[[], T], initial_size: int = 10, max_size: int = 100
    ):
        """
        Initialize memory pool.

        Args:
            factory: Function to create new objects
            initial_size: Initial pool size
            max_size: Maximum pool size
        """
        self.factory = factory
        self.max_size = max_size
        self.pool: list[T] = [factory() for _ in range(initial_size)]
        self.allocated = 0
        self.reused = 0

    def acquire(self) -> T:
        """
        Acquire object from pool.

        Returns:
            Object from pool or newly created
        """
        if self.pool:
            self.reused += 1
            return self.pool.pop()
        self.allocated += 1
        return self.factory()

    def release(self, obj: T) -> None:
        """
        Release object back to pool.

        Args:
            obj: Object to return to pool
        """
        if len(self.pool) < self.max_size:
            self.pool.append(obj)

    def get_stats(self) -> dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Dictionary with pool stats
        """
        return {
            "pool_size": len(self.pool),
            "max_size": self.max_size,
            "allocated": self.allocated,
            "reused": self.reused,
            "reuse_rate": (
                f"{(self.reused / (self.allocated + self.reused) * 100):.2f}%"
                if (self.allocated + self.reused) > 0
                else "0.00%"
            ),
        }


class MemoryOptimizer:
    """
    Main memory optimizer coordinating caching and pooling strategies.
    
    Provides a unified interface for memory optimization features.
    """

    def __init__(self, cache_capacity: int = 128):
        """
        Initialize memory optimizer.

        Args:
            cache_capacity: Maximum cache size
        """
        self.cache_capacity = cache_capacity
        self.caches: dict[str, LRUCache] = {}
        self.pools: dict[str, MemoryPool] = {}
        logger.info(
            f"MemoryOptimizer initialized with cache_capacity={cache_capacity}"
        )

    def get_cache(self, name: str, capacity: int | None = None) -> LRUCache:
        """
        Get or create a named cache.

        Args:
            name: Cache name
            capacity: Cache capacity (uses default if None)

        Returns:
            LRU cache instance
        """
        if name not in self.caches:
            cap = capacity if capacity is not None else self.cache_capacity
            self.caches[name] = LRUCache(capacity=cap)
            logger.debug(f"Created cache '{name}' with capacity {cap}")
        return self.caches[name]

    def get_pool(
        self, name: str, factory: Callable[[], T], max_size: int = 100
    ) -> MemoryPool[T]:
        """
        Get or create a named memory pool.

        Args:
            name: Pool name
            factory: Object factory function
            max_size: Maximum pool size

        Returns:
            Memory pool instance
        """
        if name not in self.pools:
            self.pools[name] = MemoryPool(factory=factory, max_size=max_size)
            logger.debug(f"Created memory pool '{name}' with max_size {max_size}")
        return self.pools[name]

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics for all caches and pools.

        Returns:
            Dictionary with comprehensive statistics
        """
        stats = {
            "caches": {name: cache.get_stats() for name, cache in self.caches.items()},
            "pools": {name: pool.get_stats() for name, pool in self.pools.items()},
        }
        return stats

    def clear_all(self) -> None:
        """Clear all caches (pools are not cleared as they contain reusable objects)."""
        for cache in self.caches.values():
            cache.clear()
        logger.info("All caches cleared")
