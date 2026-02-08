"""
Async utilities for Kor'tana

Provides async helpers, batch processing, and connection pooling utilities.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")
R = TypeVar("R")


class AsyncBatchProcessor(Generic[T, R]):
    """
    Process items in batches with concurrency limits.

    Useful for:
    - Rate-limited API calls
    - Database batch operations
    - Memory operations with parallel processing
    """

    def __init__(
        self,
        batch_size: int = 10,
        max_concurrent: int = 5,
        timeout: float | None = None,
    ):
        """
        Initialize batch processor.

        Args:
            batch_size: Items per batch
            max_concurrent: Max concurrent operations
            timeout: Operation timeout in seconds
        """
        self.batch_size = batch_size
        self.max_concurrent = max_concurrent
        self.timeout = timeout

    async def process(
        self,
        items: list[T],
        processor: Callable[[T], Coroutine[Any, Any, R]],
    ) -> list[R]:
        """
        Process items with concurrency limits.

        Args:
            items: Items to process
            processor: Async function that processes each item

        Returns:
            List of results in original order
        """
        results = [None] * len(items)
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def bounded_processor(index: int, item: T) -> None:
            async with semaphore:
                try:
                    result = await asyncio.wait_for(
                        processor(item), timeout=self.timeout
                    )
                    results[index] = result
                except TimeoutError:
                    logger.error(f"Timeout processing item {index}")
                    results[index] = None
                except Exception as e:
                    logger.error(f"Error processing item {index}: {e}")
                    results[index] = None

        # Process in batches
        tasks = [
            bounded_processor(i, item)
            for i, item in enumerate(items)
        ]
        tasks = [bounded_processor(i, item) for i, item in enumerate(items)]

        await asyncio.gather(*tasks, return_exceptions=False)
        return [r for r in results if r is not None]


class ConnectionPool:
    """
    Simple connection pool for managing service connections.

    Prevents resource exhaustion by limiting concurrent connections.
    """

    def __init__(self, factory: Callable, pool_size: int = 10):
        """
        Initialize connection pool.

        Args:
            factory: Callable that creates new connections
            pool_size: Maximum pool size
        """
        self.factory = factory
        self.pool_size = pool_size
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=pool_size)
        self._created = 0
        self._lock = asyncio.Lock()

    async def acquire(self):
        """Get a connection from the pool."""
        try:
            conn = self._pool.get_nowait()
            logger.debug(
                f"Reused connection from pool. Available: {self._pool.qsize()}"
            )
            return conn
        except asyncio.QueueEmpty:
            async with self._lock:
                if self._created < self.pool_size:
                    conn = self.factory()
                    self._created += 1
                    logger.debug(f"Created new connection. Total: {self._created}")
                    return conn

            # Wait for available connection
            logger.debug("No available connections, waiting...")
            return await self._pool.get()

    async def release(self, conn):
        """Return a connection to the pool."""
        try:
            self._pool.put_nowait(conn)
            logger.debug(f"Released connection. Available: {self._pool.qsize()}")
        except asyncio.QueueFull:
            logger.warning("Connection pool full, closing connection")
            if hasattr(conn, "close"):
                conn.close()

    async def close_all(self):
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                if hasattr(conn, "close"):
                    conn.close()
            except asyncio.QueueEmpty:
                break
        logger.info(f"Closed all {self._created} connections")


class AsyncRetry:
    """Configurable async retry decorator."""

    def __init__(
        self,
        max_attempts: int = 3,
        backoff_factor: float = 2.0,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exceptions: tuple = (Exception,),
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum retry attempts
            backoff_factor: Exponential backoff multiplier
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay between retries
            exceptions: Tuple of exceptions to retry on
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exceptions = exceptions

    def __call__(self, func: Callable):
        """Apply retry decorator to function."""

        async def async_wrapper(*args, **kwargs):
            attempt = 0
            delay = self.initial_delay

            while attempt < self.max_attempts:
                try:
                    return await func(*args, **kwargs)
                except self.exceptions as e:
                    attempt += 1

                    if attempt >= self.max_attempts:
                        logger.error(
                            f"Final attempt {attempt} failed for {func.__name__}: {e}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt} failed for {func.__name__}, "
                        f"retrying in {delay}s: {e}"
                    )

                    await asyncio.sleep(delay)
                    delay = min(delay * self.backoff_factor, self.max_delay)

        return async_wrapper


async def gather_with_limit(
    *coros: Coroutine,
    limit: int = 10,
) -> list[Any]:
    """
    Gather coroutines with concurrency limit.

    Args:
        *coros: Coroutines to gather
        limit: Max concurrent operations

    Returns:
        List of results
    """
    semaphore = asyncio.Semaphore(limit)

    async def bounded_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(
        *(bounded_coro(coro) for coro in coros), return_exceptions=False
    )


class AsyncCache:
    """Simple async-safe cache."""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Any | None:
        """Get value from cache."""
        async with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        async with self._lock:
            if len(self._cache) >= self.max_size:
                # Remove first (FIFO)
                first_key = next(iter(self._cache))
                del self._cache[first_key]
            self._cache[key] = value

    async def clear(self) -> None:
        """Clear cache."""
        async with self._lock:
            self._cache.clear()
