"""
Security middleware for Kor'tana Backend
Includes rate limiting, security headers, and request tracking
"""

import time
import uuid
from collections.abc import Awaitable, Callable
from ipaddress import ip_address, ip_network
from typing import Any

from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware

from src.kortana.logger import log_error, log_request, set_request_id
from src.kortana.metrics import track_rate_limit_event, track_rate_limit_hit

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
        period_seconds: int = 60,
        redis_url: str | None = None,
        proxy_mode: bool = False,
        trusted_proxies: tuple[str, ...] | None = None,
        exclude_paths: tuple[str, ...] | None = None,
    ) -> None:
        super().__init__(app)
        self.requests_per_minute: int = requests_per_minute
        self.period_seconds = period_seconds
        self.proxy_mode = proxy_mode
        self.trusted_proxies = tuple(
            entry.strip() for entry in (trusted_proxies or ()) if entry.strip()
        )
        self.exclude_paths = exclude_paths or (
            "/",
            "/index.html",
            "/favicon.ico",
            "/manifest.json",
            "/sw.js",
            "/icon-192.png",
            "/icon-512.png",
            "/assets",
            "/api/health",
            "/api/autonomy/status",
            "/api/autonomy/health",
        )
        effective_redis_url = redis_url or "redis://localhost:6379/0"
        self.redis_url = effective_redis_url
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
        if request.method == "OPTIONS" or self._is_excluded_path(request.url.path):
            return await call_next(request)

        # If the circuit breaker is open, skip Redis entirely.
        if self._redis_failed_at:
            elapsed = time.monotonic() - self._redis_failed_at
            if elapsed < _REDIS_CIRCUIT_BREAKER_SECONDS:
                return await call_next(request)
            # Cooldown expired — attempt to re-close the circuit.
            self._redis_failed_at = 0.0

        client_ip, immediate_proxy, forwarded_ip, spoof_ignored = (
            self._resolve_client_identity(request)
        )
        route = request.url.path
        key = f"ratelimit:{client_ip}"

        try:
            current_count = await self.redis.incr(key)
            if current_count == 1:
                await self.redis.expire(key, self.period_seconds)

            ttl = await self.redis.ttl(key)
            retry_after = (
                int(ttl) if isinstance(ttl, int) and ttl and ttl > 0 else self.period_seconds
            )
            reset_at = int(time.time()) + retry_after
            remaining = max(self.requests_per_minute - current_count, 0)

            if current_count > self.requests_per_minute:
                track_rate_limit_hit(route, "global")
                track_rate_limit_event(route, client_ip, forwarded_ip, "limited")
                log_error(
                    "RATE_LIMIT_EXCEEDED",
                    f"IP {client_ip} exceeded {self.requests_per_minute} requests/minute",
                    details={
                        "client_ip": client_ip,
                        "forwarded_ip": forwarded_ip,
                        "immediate_proxy": immediate_proxy,
                        "current_count": current_count,
                        "route": route,
                        "retry_after": retry_after,
                    },
                )
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": "rate_limited",
                        "detail": "Too many requests",
                        "message": "Too many requests",
                        "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                        "retry_after": retry_after,
                        "details": {
                            "route": route,
                            "client_ip": client_ip,
                            "forwarded_ip": forwarded_ip,
                            "immediate_proxy": immediate_proxy,
                            "limit": self.requests_per_minute,
                            "current_count": current_count,
                        },
                    },
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(self.requests_per_minute),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(reset_at),
                    },
                )

            if spoof_ignored:
                track_rate_limit_event(route, client_ip, forwarded_ip, "spoof-ignored")
                log_request(
                    "security",
                    "Ignored untrusted X-Forwarded-For header",
                    details={
                        "route": route,
                        "client_ip": client_ip,
                        "forwarded_ip": forwarded_ip,
                        "immediate_proxy": immediate_proxy,
                        "status": "spoof-ignored",
                    },
                )
            else:
                track_rate_limit_event(route, client_ip, forwarded_ip, "allowed")
        except (RedisError, RuntimeError, OSError) as exc:
            # Open the circuit breaker — one log line, then silence.
            self._redis_failed_at = time.monotonic()
            log_error(
                "RATE_LIMIT_REDIS_ERROR",
                f"Redis unavailable, rate limiting disabled for {_REDIS_CIRCUIT_BREAKER_SECONDS}s: {exc}",
                details={"client_ip": client_ip},
            )

        response = await call_next(request)
        if "remaining" in locals():
            response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset_at)
        return response

    def _resolve_client_identity(
        self, request: Request
    ) -> tuple[str, str | None, str | None, bool]:
        immediate_proxy = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        forwarded_ip = (
            forwarded_for.split(",")[0].strip() if forwarded_for else None
        )

        if forwarded_ip:
            if self.proxy_mode or self._is_trusted_proxy(immediate_proxy):
                return forwarded_ip, immediate_proxy, forwarded_ip, False
            return immediate_proxy, immediate_proxy, forwarded_ip, True

        return immediate_proxy, immediate_proxy, None, False

    def _is_trusted_proxy(self, client_ip: str | None) -> bool:
        if not client_ip:
            return False

        try:
            parsed_ip = ip_address(client_ip)
        except ValueError:
            return False

        for entry in self.trusted_proxies:
            try:
                if "/" in entry:
                    if parsed_ip in ip_network(entry, strict=False):
                        return True
                elif parsed_ip == ip_address(entry):
                    return True
            except ValueError:
                continue

        return False

    def _is_excluded_path(self, path: str) -> bool:
        return any(
            path == excluded or path.startswith(f"{excluded}/")
            for excluded in self.exclude_paths
        )


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
    """Add unique request ID for tracking and propagate it into the logging context."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Stamp every request with a UUID and inject it into the async log context."""
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = request_id
        # Bind to the ContextVar so all log statements for this request include it.
        set_request_id(request_id)

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
