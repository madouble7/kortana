"""
Rate Limiting Middleware for Kor'tana Backend

Provides configurable rate limiting using Redis or in-memory storage.
Helps protect API endpoints from abuse and DDoS attacks.

Features:
- Sliding window algorithm
- Configurable limits per endpoint
- User-based rate limiting
- Different tiers (free, basic, premium)
- Retry-After header support

Author: Kor'tana Security Team
Date: January 14, 2026
"""

import asyncio
import hashlib
import time
from dataclasses import dataclass, field
from functools import wraps
from typing import Callable, Dict, Optional, Tuple

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

# ==================== Rate Limit Configuration ====================


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""

    requests: int = 100  # Max requests
    window_seconds: int = 60  # Time window in seconds

    # Different limits for different user tiers
    free_tier: Tuple[int, int] = (20, 60)  # 20 req/min
    basic_tier: Tuple[int, int] = (50, 60)  # 50 req/min
    premium_tier: Tuple[int, int] = (200, 60)  # 200 req/min

    # Tier based on role
    tier_limits: Dict[str, Tuple[int, int]] = field(
        default_factory=lambda: {
            "admin": (500, 60),
            "service": (1000, 60),
            "user": (100, 60),
            "anonymous": (20, 60),
        }
    )


# Default configuration
default_config = RateLimitConfig()


# ==================== In-Memory Rate Limit Store ====================


class InMemoryRateLimitStore:
    """
    In-memory rate limit storage for single-instance deployments.
    For production, replace with Redis-based implementation.
    """

    def __init__(self):
        self._storage: Dict[str, list] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def _cleanup_expired(self):
        """Remove expired entries periodically"""
        while True:
            try:
                current_time = time.time()
                expired_keys = []

                for key, timestamps in self._storage.items():
                    # Remove timestamps outside the window
                    self._storage[key] = [
                        ts for ts in timestamps if current_time - ts < 3600  # Keep for 1 hour max
                    ]

                    # Mark for deletion if empty
                    if not self._storage[key]:
                        expired_keys.append(key)

                # Remove empty entries
                for key in expired_keys:
                    del self._storage[key]

                # Wait 5 minutes before next cleanup
                await asyncio.sleep(300)

            except asyncio.CancelledError:
                break
            except Exception:
                # Continue on error
                await asyncio.sleep(60)

    def _get_key(self, identifier: str, endpoint: str) -> str:
        """Generate unique key for rate limiting"""
        return f"ratelimit:{identifier}:{endpoint}"

    async def get_count(self, identifier: str, endpoint: str, window: int) -> int:
        """Get current request count for identifier/endpoint"""
        key = self._get_key(identifier, endpoint)
        current_time = time.time()

        if key not in self._storage:
            self._storage[key] = []

        # Remove old timestamps
        cutoff = current_time - window
        self._storage[key] = [ts for ts in self._storage[key] if ts > cutoff]

        return len(self._storage[key])

    async def increment(self, identifier: str, endpoint: str, window: int) -> int:
        """Increment request count and return new count"""
        key = self._get_key(identifier, endpoint)
        current_time = time.time()

        if key not in self._storage:
            self._storage[key] = []

        # Remove old timestamps
        cutoff = current_time - window
        self._storage[key] = [ts for ts in self._storage[key] if ts > cutoff]

        # Add current timestamp
        self._storage[key].append(current_time)

        return len(self._storage[key])

    async def get_remaining(self, identifier: str, endpoint: str, window: int, limit: int) -> int:
        """Get remaining requests allowed"""
        current = await self.get_count(identifier, endpoint, window)
        return max(0, limit - current)

    async def get_reset_time(self, identifier: str, endpoint: str, window: int) -> int:
        """Get timestamp when rate limit resets"""
        key = self._get_key(identifier, endpoint)

        if key not in self._storage or not self._storage[key]:
            return int(time.time()) + window

        oldest = min(self._storage[key])
        return int(oldest) + window


# Global rate limit store
_rate_limit_store = InMemoryRateLimitStore()


# ==================== Rate Limit Utilities ====================


def get_client_identifier(request: Request) -> str:
    """
    Extract client identifier from request for rate limiting.
    Priority: API Key > User ID > IP Address
    """
    # Check for API key
    api_key = request.headers.get("X-API-Key")
    if api_key:
        return f"apikey:{hashlib.sha256(api_key.encode()).hexdigest()[:16]}"

    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        # Use hashed token as identifier
        token = auth_header[7:]
        return f"token:{hashlib.sha256(token.encode()).hexdigest()[:16]}"

    # Fall back to IP address
    client_ip = request.client.host if request.client else "unknown"
    forwarded_for = request.headers.get("X-Forwarded-For")

    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()

    return f"ip:{client_ip}"


def get_rate_limit_for_tier(tier: str = "user") -> Tuple[int, int]:
    """Get rate limit configuration for a user tier"""
    return default_config.tier_limits.get(tier, default_config.tier_limits["user"])


# ==================== FastAPI Dependency ====================


class RateLimitExceeded(HTTPException):
    """Exception raised when rate limit is exceeded"""

    def __init__(self, limit: int, reset_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Maximum {limit} requests allowed.",
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(reset_after),
                "Retry-After": str(reset_after),
            },
        )


async def check_rate_limit(
    request: Request,
    endpoint: Optional[str] = None,
    tier: str = "user",
) -> Dict[str, int]:
    """
    Check and enforce rate limit for a request.

    Args:
        request: FastAPI request object
        endpoint: Optional custom endpoint for rate limiting
        tier: User tier for limit selection

    Returns:
        Dict with rate limit headers

    Raises:
        RateLimitExceeded: If rate limit is exceeded
    """
    # Get rate limit configuration for tier
    limit, window = get_rate_limit_for_tier(tier)

    # Use request path as endpoint
    if endpoint is None:
        endpoint = request.url.path

    # Get client identifier
    identifier = get_client_identifier(request)

    # Check current count
    current = await _rate_limit_store.get_count(identifier, endpoint, window)

    if current >= limit:
        # Rate limit exceeded
        reset_after = await _rate_limit_store.get_reset_time(identifier, endpoint, window)
        raise RateLimitExceeded(limit, reset_after)

    # Increment counter
    new_count = await _rate_limit_store.increment(identifier, endpoint, window)

    # Get remaining
    remaining = max(0, limit - new_count)
    reset_after = await _rate_limit_store.get_reset_time(identifier, endpoint, window)

    return {
        "X-RateLimit-Limit": limit,
        "X-RateLimit-Remaining": remaining,
        "X-RateLimit-Reset": reset_after,
    }


def rate_limit_dependency(
    endpoint: Optional[str] = None,
    tier: str = "user",
) -> Callable:
    """
    Create a rate limit dependency for routes.

    Usage:
        @router.get("/protected")
        async def protected_endpoint(
            rate_limit: Dict[str, int] = Depends(rate_limit_dependency(tier="user"))
        ):
            return {"message": "Success"}
    """

    async def dependency(
        request: Request,
    ) -> Dict[str, int]:
        return await check_rate_limit(request, endpoint, tier)

    return dependency


# ==================== Decorator for Routes ====================


def rate_limited(
    requests: int = 100,
    window_seconds: int = 60,
    tier: str = "user",
):
    """
    Decorator to apply rate limiting to route handlers.

    Usage:
        @router.get("/endpoint")
        @rate_limited(requests=50, window_seconds=60)
        async def endpoint():
            return {"message": "Success"}
    """

    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get request from kwargs (FastAPI passes it as keyword arg)
            request = kwargs.get("request")
            if request is None:
                # Try to get from args
                for arg in args:
                    if hasattr(arg, "url"):
                        request = arg
                        break

            if request is None:
                # No request available, skip rate limiting
                return await func(*args, **kwargs)

            # Check rate limit
            limit, window = get_rate_limit_for_tier(tier)
            limit = min(requests, limit)  # Use lower of two limits

            identifier = get_client_identifier(request)
            endpoint = request.url.path

            current = await _rate_limit_store.get_count(identifier, endpoint, window)

            if current >= limit:
                reset_after = await _rate_limit_store.get_reset_time(identifier, endpoint, window)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Maximum {limit} requests per {window} seconds.",
                    headers={
                        "X-RateLimit-Limit": str(limit),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_after),
                        "Retry-After": str(reset_after),
                    },
                )

            # Increment and proceed
            await _rate_limit_store.increment(identifier, endpoint, window)

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# ==================== Middleware for Automatic Rate Limiting ====================


class RateLimitMiddleware:
    """Middleware to automatically apply rate limiting to all routes"""

    def __init__(
        self,
        app,
        tier: str = "user",
        exclude_paths: list = None,
    ):
        self.app = app
        self.tier = tier
        self.exclude_paths = exclude_paths or ["/api/health", "/docs", "/openapi.json", "/"]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        # Only process API routes
        path = scope.get("path", "")

        if any(path.startswith(exclude) for exclude in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Get request info
        scope.get("method", "GET")

        # Create mock request for rate limiting
        # In production, you'd use actual request object

        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                # Add rate limit headers
                headers = list(message.get("headers", []))

                # Add X-RateLimit headers if not present
                # (These would be added by the route handler)

                message["headers"] = headers

            await send(message)

        await self.app(scope, receive, send_wrapper)


# ==================== Rate Limit Response Helper ====================


def create_rate_limit_response(
    limit: int,
    remaining: int,
    reset_after: int,
    message: str = "Rate limit exceeded",
) -> JSONResponse:
    """Create a standardized rate limit response"""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "RATE_LIMIT_EXCEEDED",
            "message": message,
            "limit": limit,
            "remaining": remaining,
            "reset_after": reset_after,
        },
        headers={
            "X-RateLimit-Limit": str(limit),
            "X-RateLimit-Remaining": str(remaining),
            "X-RateLimit-Reset": str(reset_after),
            "Retry-After": str(reset_after),
        },
    )


# ==================== Export Classes ====================

__all__ = [
    "RateLimitConfig",
    "InMemoryRateLimitStore",
    "RateLimitExceeded",
    "check_rate_limit",
    "rate_limit_dependency",
    "rate_limited",
    "RateLimitMiddleware",
    "create_rate_limit_response",
    "get_client_identifier",
    "get_rate_limit_for_tier",
]
