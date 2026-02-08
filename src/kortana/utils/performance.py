"""
Performance Optimization Utilities for Kor'tana

Implements:
- Request deduplication for identical queries
- Response caching with TTL
- Circuit breaker pattern for external services
- Performance metrics collection
- Connection pooling helpers
"""

import asyncio
import hashlib
import logging
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from typing import Any, Generic, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """State of a circuit breaker."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"      # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CacheEntry:
    """A cached response with TTL."""
    value: Any
    timestamp: datetime
    ttl_seconds: int | None = None

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        if self.ttl_seconds is None:
            return False
        elapsed = (datetime.now() - self.timestamp).total_seconds()
        return elapsed > self.ttl_seconds


class TTLCache(Generic[T]):
    """Thread-safe cache with TTL (Time-To-Live) support."""

    def __init__(self, max_size: int = 100, default_ttl: int | None = 300):
        """
        Initialize TTL cache.

        Args:
            max_size: Maximum number of items
            default_ttl: Default TTL in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()

    def _make_key(self, *args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_str = f"{str(args)}{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_str.encode()).hexdigest()

    async def get(self, key: str) -> T | None:
        """Get value from cache."""
        async with self._lock:
            if key not in self.cache:
                return None

            entry = self.cache[key]
            if entry.is_expired():
                del self.cache[key]
                logger.debug(f"Cache entry expired: {key}")
                return None

            # Move to end (LRU)
            self.cache.move_to_end(key)
            logger.debug(f"Cache hit: {key}")
            return entry.value

    async def set(self, key: str, value: T, ttl: int | None = None) -> None:
        """Set value in cache."""
        async with self._lock:
            if len(self.cache) >= self.max_size:
                # Remove oldest item
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
                logger.debug(f"Evicted cache entry: {oldest_key}")

            ttl = ttl or self.default_ttl
            self.cache[key] = CacheEntry(value, datetime.now(), ttl)
            logger.debug(f"Cached value: {key}")

    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self.cache.clear()


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5  # Failures before opening
    recovery_timeout: int = 60  # Seconds before attempting recovery
    expected_exception: type = Exception


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for protecting external service calls.

    Prevents cascading failures by failing fast when a service is down.
    """

    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time: datetime | None = None
        self.success_count = 0

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery."""
        if self.last_failure_time is None:
            return False

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.config.recovery_timeout

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker is OPEN. Service unavailable. "
                    f"Retry after {self.config.recovery_timeout}s"
                )

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except self.config.expected_exception:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= 2:
                self.state = CircuitState.CLOSED
                self.success_count = 0
                logger.info("Circuit breaker reset to CLOSED")

    def _on_failure(self) -> None:
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.config.failure_threshold:
            self.state = CircuitState.OPEN
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning("Circuit breaker returned to OPEN after failed recovery")


def cached_async(ttl: int | None = 300):
    """
    Async decorator for caching function results.

    Args:
        ttl: Time-to-live in seconds

    Example:
        @cached_async(ttl=300)
        async def fetch_data():
            return await some_service.fetch()
    """
    cache = TTLCache(default_ttl=ttl)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            key = cache._make_key(*args, **kwargs)

            # Try cache
            cached_value = await cache.get(key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set(key, result, ttl)
            return result

        return wrapper

    return decorator


def timed_execution(name: str = ""):
    """
    Decorator to measure function execution time.

    Args:
        name: Name for the operation (auto-generated if not provided)

    Example:
        @timed_execution(name="database_query")
        async def query_db():
            pass
    """
    def decorator(func: Callable) -> Callable:
        operation_name = name or func.__name__

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > 100:  # Log only if > 100ms
                    logger.info(f"{operation_name} took {elapsed:.1f}ms")

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = (time.perf_counter() - start) * 1000
                if elapsed > 100:
                    logger.info(f"{operation_name} took {elapsed:.1f}ms")

        # Return appropriate wrapper
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


@dataclass
class PerfMetrics:
    """Performance metrics for a service."""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_time_ms: float = 0.0
    min_time_ms: float = float('inf')
    max_time_ms: float = 0.0

    @property
    def avg_time_ms(self) -> float:
        """Calculate average response time."""
        if self.total_requests == 0:
            return 0.0
        return self.total_time_ms / self.total_requests

    @property
    def success_rate(self) -> float:
        """Calculate success rate."""
        if self.total_requests == 0:
            return 0.0
        return (self.successful_requests / self.total_requests) * 100

    def record_request(self, duration_ms: float, success: bool = True) -> None:
        """Record a request."""
        self.total_requests += 1
        self.total_time_ms += duration_ms
        self.min_time_ms = min(self.min_time_ms, duration_ms)
        self.max_time_ms = max(self.max_time_ms, duration_ms)

        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1


class MetricsCollector:
    """Collect performance metrics."""

    def __init__(self):
        self.metrics: dict[str, PerfMetrics] = {}
        self._lock = asyncio.Lock()

    async def record(self, operation: str, duration_ms: float, success: bool = True) -> None:
        """Record an operation's performance."""
        async with self._lock:
            if operation not in self.metrics:
                self.metrics[operation] = PerfMetrics()

            self.metrics[operation].record_request(duration_ms, success)

    def get_summary(self) -> dict[str, dict[str, float]]:
        """Get metrics summary."""
        return {
            op: {
                'avg_time_ms': m.avg_time_ms,
                'min_time_ms': m.min_time_ms,
                'max_time_ms': m.max_time_ms,
                'success_rate': m.success_rate,
                'total_requests': m.total_requests,
            }
            for op, m in self.metrics.items()
        }
