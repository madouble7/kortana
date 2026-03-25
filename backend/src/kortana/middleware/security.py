"""
Security middleware for Kor'tana Backend
Includes rate limiting, security headers, and request tracking
"""

import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import HTTPException, Request, Response, status
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware

from src.kortana.logger import log_error, log_request

# Circuit-breaker cooldown: after a Redis failure, stop retrying for this
# many seconds to avoid spamming error logs on every single request.
_REDIS_CIRCUIT_BREAKER_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware - limits requests per IP using Redis.

    This implementation uses a distributed Redis counter per client IP to ensure
    consistent rate limiting across multiple application instances and workers.

    The time window is 60 seconds, and the maximum number of requests within
    that window is defined by ``requests_per_minute``.
    """

    def __init__(
        self,
        app: Any,
        requests_per_minute: int = 60,
        redis_url: str | None = None,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute: int = requests_per_minute
        effective_redis_url = redis_url or "redis://localhost:6379/0"
        self.redis: Redis = Redis.from_url(
            effective_redis_url,
            encoding="utf-8",
            decode_responses=True,
        )
        # Circuit breaker state — 0.0 means "healthy / never failed".
        self._redis_failed_at: float = 0.0

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Process request and apply Redis-backed rate limiting."""
        # If the circuit breaker is open, skip Redis entirely.
        if self._redis_failed_at:
            elapsed = time.monotonic() - self._redis_failed_at
            if elapsed < _REDIS_CIRCUIT_BREAKER_SECONDS:
                return await call_next(request)
            # Cooldown expired — attempt to re-close the circuit.
            self._redis_failed_at = 0.0

        client_ip = request.client.host if request.client else "unknown"
        key = f"ratelimit:{client_ip}"

        try:
            current_count = await self.redis.incr(key)
            if current_count == 1:
                await self.redis.expire(key, 60)

            if current_count > self.requests_per_minute:
                log_error(
                    "RATE_LIMIT_EXCEEDED",
                    f"IP {client_ip} exceeded {self.requests_per_minute} requests/minute",
                    details={"client_ip": client_ip, "current_count": current_count},
                )
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Maximum requests exceeded.",
                )
        except (RedisError, RuntimeError, OSError) as exc:
            # Open the circuit breaker — one log line, then silence.
            self._redis_failed_at = time.monotonic()
            log_error(
                "RATE_LIMIT_REDIS_ERROR",
                f"Redis unavailable, rate limiting disabled for {_REDIS_CIRCUIT_BREAKER_SECONDS}s: {exc}",
                details={"client_ip": client_ip},
            )

        response = await call_next(request)
        return response

    def _cleanup_all(self, now: float) -> None:
        """Remove all IPs that haven't made a request in the last minute"""
        minute_ago = now - 60
        keys_to_delete = []
        for ip, timestamps in self.requests.items():
            new_timestamps = [t for t in timestamps if t > minute_ago]
            if not new_timestamps:
                keys_to_delete.append(ip)
            else:
                self.requests[ip] = new_timestamps

        for ip in keys_to_delete:
            del self.requests[ip]
        self.last_cleanup = now


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers[
            "Strict-Transport-Security"
        ] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers[
            "Permissions-Policy"
        ] = "geolocation=(), microphone=(), camera=()"

        # Remove server info
        response.headers["Server"] = "Kor'tana"

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracking"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Add request ID to all requests"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging with detailed information"""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Log request details"""
        start_time = time.time()

        client_ip = request.client.host if request.client else "unknown"
        request_id = getattr(request.state, "request_id", "unknown")

        log_request(
            "http_request_start",
            f"{request.method} {request.url.path}",
            details={
                "request_id": request_id,
                "client_ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "query_string": str(request.url.query),
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            process_time = time.time() - start_time
            log_error(
                "http_request_error",
                f"Error processing {request.method} {request.url.path}",
                details={
                    "request_id": request_id,
                    "error": str(exc),
                    "process_time": process_time,
                },
            )
            raise

        process_time = time.time() - start_time

        log_request(
            "http_request_complete",
            f"{request.method} {request.url.path} - {response.status_code}",
            details={
                "request_id": request_id,
                "client_ip": client_ip,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_seconds": round(process_time, 3),
            },
        )

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)

        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS handling with security checks"""

    def __init__(self, app: Any, allowed_origins: list[str]):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Handle CORS with security checks"""
        origin = request.headers.get("origin")

        # Check if origin is allowed
        if origin and origin in self.allowed_origins:
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers[
                "Access-Control-Allow-Methods"
            ] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers[
                "Access-Control-Allow-Headers"
            ] = "Content-Type, Authorization"
        else:
            response = await call_next(request)

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """Whitelist specific IPs for sensitive endpoints"""

    def __init__(self, app, whitelist: list = None, sensitive_paths: list = None):
        super().__init__(app)
        self.whitelist = whitelist or []
        self.sensitive_paths = sensitive_paths or ["/api/admin", "/api/system"]

    async def dispatch(self, request: Request, call_next):
        """Check IP whitelist for sensitive endpoints"""
        client_ip = request.client.host if request.client else "unknown"

        # Check if path requires whitelist
        if any(request.url.path.startswith(path) for path in self.sensitive_paths):
            if self.whitelist and client_ip not in self.whitelist:
                log_error(
                    "IP_WHITELIST_VIOLATION",
                    f"Unauthorized IP {client_ip} attempted to access {request.url.path}",
                    details={"client_ip": client_ip, "path": request.url.path},
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - IP not whitelisted",
                )

        response = await call_next(request)
        return response
