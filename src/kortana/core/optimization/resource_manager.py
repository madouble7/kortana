"""
Resource Manager inspired by Chromium's resource management strategies.

This module provides:
- Resource pooling and lifecycle management
- Adaptive resource limits based on system state
- Efficient resource allocation and cleanup
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Callable, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ResourcePool(Generic[T]):
    """
    Thread-safe resource pool for managing reusable resources.
    
    Inspired by Chromium's process/tab management for efficient resource use.
    """

    def __init__(
        self,
        name: str,
        factory: Callable[[], T],
        cleanup: Callable[[T], None] | None = None,
        min_size: int = 5,
        max_size: int = 50,
        timeout: float = 60.0,
    ):
        """
        Initialize resource pool.

        Args:
            name: Pool name for identification
            factory: Function to create new resources
            cleanup: Optional cleanup function for resources
            min_size: Minimum pool size
            max_size: Maximum pool size
            timeout: Resource idle timeout in seconds
        """
        self.name = name
        self.factory = factory
        self.cleanup = cleanup
        self.min_size = min_size
        self.max_size = max_size
        self.timeout = timeout

        self._pool: list[tuple[T, float]] = []
        self._lock = threading.RLock()
        self._active_resources: set[int] = set()
        self._created_count = 0
        self._acquired_count = 0
        self._released_count = 0

        # Pre-populate pool with minimum resources
        for _ in range(min_size):
            self._pool.append((self.factory(), time.time()))
            self._created_count += 1

        logger.info(
            f"ResourcePool '{name}' initialized: min={min_size}, max={max_size}"
        )

    def acquire(self) -> T:
        """
        Acquire a resource from the pool.

        Returns:
            Resource instance
        """
        with self._lock:
            # Try to get from pool
            while self._pool:
                resource, timestamp = self._pool.pop(0)

                # Check if resource is still valid (not timed out)
                if time.time() - timestamp < self.timeout:
                    self._active_resources.add(id(resource))
                    self._acquired_count += 1
                    return resource

                # Resource timed out, clean up
                if self.cleanup:
                    try:
                        self.cleanup(resource)
                    except Exception as e:
                        logger.warning(
                            f"Error cleaning up timed-out resource in pool '{self.name}': {e}"
                        )

            # No available resources, create new one
            if self._created_count < self.max_size:
                resource = self.factory()
                self._created_count += 1
                self._active_resources.add(id(resource))
                self._acquired_count += 1
                logger.debug(
                    f"Created new resource for pool '{self.name}' (total: {self._created_count})"
                )
                return resource

            # Max size reached, create temporary resource
            logger.warning(
                f"ResourcePool '{self.name}' at max capacity, creating temporary resource"
            )
            return self.factory()

    def release(self, resource: T) -> None:
        """
        Release a resource back to the pool.

        Args:
            resource: Resource to release
        """
        with self._lock:
            resource_id = id(resource)

            if resource_id in self._active_resources:
                self._active_resources.remove(resource_id)

            # Return to pool if under max size
            if len(self._pool) < self.max_size:
                self._pool.append((resource, time.time()))
                self._released_count += 1
            else:
                # Pool full, cleanup resource
                if self.cleanup:
                    try:
                        self.cleanup(resource)
                    except Exception as e:
                        logger.warning(
                            f"Error cleaning up excess resource in pool '{self.name}': {e}"
                        )

    def cleanup_idle(self) -> int:
        """
        Clean up idle resources that have exceeded timeout.

        Returns:
            Number of resources cleaned up
        """
        with self._lock:
            current_time = time.time()
            cleaned = 0
            new_pool = []

            for resource, timestamp in self._pool:
                # Calculate total resources if we keep this one
                total_if_kept = len(new_pool) + 1 + len(self._active_resources)
                
                # Keep resource if it hasn't timed out OR if removing it would go below min_size
                should_keep = (
                    current_time - timestamp < self.timeout or 
                    total_if_kept <= self.min_size
                )
                
                if should_keep:
                    # Keep resource
                    new_pool.append((resource, timestamp))
                else:
                    # Clean up resource
                    if self.cleanup:
                        try:
                            self.cleanup(resource)
                            cleaned += 1
                        except Exception as e:
                            logger.warning(
                                f"Error cleaning up idle resource in pool '{self.name}': {e}"
                            )

            self._pool = new_pool
            return cleaned

    def get_stats(self) -> dict[str, Any]:
        """
        Get pool statistics.

        Returns:
            Dictionary with pool statistics
        """
        with self._lock:
            return {
                "name": self.name,
                "available": len(self._pool),
                "active": len(self._active_resources),
                "total_created": self._created_count,
                "acquired": self._acquired_count,
                "released": self._released_count,
                "min_size": self.min_size,
                "max_size": self.max_size,
            }


class ResourceManager:
    """
    Central resource manager coordinating multiple resource pools.
    
    Provides unified resource management across the system.
    """

    def __init__(self):
        """Initialize resource manager."""
        self.pools: dict[str, ResourcePool] = {}
        self._lock = threading.RLock()
        self._cleanup_thread: threading.Thread | None = None
        self._running = False
        logger.info("ResourceManager initialized")

    def create_pool(
        self,
        name: str,
        factory: Callable[[], T],
        cleanup: Callable[[T], None] | None = None,
        min_size: int = 5,
        max_size: int = 50,
        timeout: float = 60.0,
    ) -> ResourcePool[T]:
        """
        Create a new resource pool.

        Args:
            name: Pool name
            factory: Resource factory function
            cleanup: Optional cleanup function
            min_size: Minimum pool size
            max_size: Maximum pool size
            timeout: Resource timeout in seconds

        Returns:
            Resource pool instance
        """
        with self._lock:
            if name in self.pools:
                logger.warning(f"Pool '{name}' already exists, returning existing pool")
                return self.pools[name]

            pool = ResourcePool(
                name=name,
                factory=factory,
                cleanup=cleanup,
                min_size=min_size,
                max_size=max_size,
                timeout=timeout,
            )
            self.pools[name] = pool
            return pool

    def get_pool(self, name: str) -> ResourcePool | None:
        """
        Get a resource pool by name.

        Args:
            name: Pool name

        Returns:
            Resource pool or None if not found
        """
        return self.pools.get(name)

    def start_cleanup_thread(self, interval: float = 30.0) -> None:
        """
        Start background thread to clean up idle resources.

        Args:
            interval: Cleanup interval in seconds
        """
        if self._running:
            logger.warning("Cleanup thread already running")
            return

        self._running = True

        def cleanup_worker():
            while self._running:
                time.sleep(interval)
                self.cleanup_all_pools()

        self._cleanup_thread = threading.Thread(
            target=cleanup_worker, daemon=True, name="ResourceCleanup"
        )
        self._cleanup_thread.start()
        logger.info(f"Started resource cleanup thread (interval={interval}s)")

    def stop_cleanup_thread(self) -> None:
        """Stop background cleanup thread."""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5.0)
            self._cleanup_thread = None
        logger.info("Stopped resource cleanup thread")

    def cleanup_all_pools(self) -> dict[str, int]:
        """
        Clean up idle resources in all pools.

        Returns:
            Dictionary mapping pool names to number of cleaned resources
        """
        results = {}
        for name, pool in self.pools.items():
            try:
                cleaned = pool.cleanup_idle()
                if cleaned > 0:
                    results[name] = cleaned
                    logger.debug(f"Cleaned {cleaned} idle resources from pool '{name}'")
            except Exception as e:
                logger.error(f"Error cleaning pool '{name}': {e}")
        return results

    def get_stats(self) -> dict[str, Any]:
        """
        Get statistics for all resource pools.

        Returns:
            Dictionary with statistics for all pools
        """
        return {
            "pools": {name: pool.get_stats() for name, pool in self.pools.items()},
            "total_pools": len(self.pools),
        }

    def shutdown(self) -> None:
        """Shutdown resource manager and cleanup all resources."""
        logger.info("Shutting down ResourceManager")
        self.stop_cleanup_thread()
        # Additional cleanup can be added here
