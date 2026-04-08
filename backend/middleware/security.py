"""
Security middleware for Kor'tana Backend
Includes rate limiting, security headers, and request tracking
"""

import time
import uuid
from collections import defaultdict

from fastapi import HTTPException, Request, status
from logger import log_error, log_request
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware - limits requests per IP"""

    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        redis_url: str | None = None,
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Kept for compatibility with backend.main, which now passes a Redis URL
        # after probing availability at startup. The legacy middleware still uses
        # in-memory counters only.
        self.redis_url = redis_url
        self.requests: dict[str, list] = defaultdict()

    async def dispatch(self, request: Request, call_next):
        """Process request and apply rate limiting"""
        client_ip = request.client.host if request.client else "unknown"

        now = time.time()
        minute_ago = now - 60

        # Initialize request list for IP if needed
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Remove old requests outside the time window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip] if req_time > minute_ago
        ]

        # Check if rate limit exceeded
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            log_error(
                "RATE_LIMIT_EXCEEDED",
                f"IP {client_ip} exceeded {self.requests_per_minute} requests/minute",
                details={"client_ip": client_ip},
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Maximum requests exceeded.",
            )

        # Record this request
        self.requests[client_ip].append(now)

        # Continue processing
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(
            self.requests_per_minute - len(self.requests[client_ip])
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Remove server info
        response.headers["Server"] = "Kor'tana"

        return response


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add unique request ID for tracking"""

    async def dispatch(self, request: Request, call_next):
        """Add request ID to all requests"""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id

        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Enhanced request logging with detailed information"""

    async def dispatch(self, request: Request, call_next):
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

    def __init__(self, app, allowed_origins: list):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(self, request: Request, call_next):
        """Handle CORS with security checks"""
        origin = request.headers.get("origin")

        # Check if origin is allowed
        if origin and origin in self.allowed_origins:
            response = await call_next(request)
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
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
