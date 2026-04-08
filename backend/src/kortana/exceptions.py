"""
Custom exception classes for Kor'tana API
Provides structured error handling with appropriate HTTP status codes
"""

from typing import Any


class KortanaException(Exception):
    """Base exception for Kor'tana application"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for JSON response"""
        return {
            "error": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class ValidationError(KortanaException):
    """Raised when input validation fails"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class NotFoundError(KortanaException):
    """Raised when a requested resource is not found"""

    def __init__(self, resource: str, resource_id: Any = None):
        message = f"{resource} not found"
        if resource_id:
            message += f": {resource_id}"
        super().__init__(
            message=message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
        )


class UnauthorizedError(KortanaException):
    """Raised when authentication fails"""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(
            message=message,
            status_code=401,
            error_code="UNAUTHORIZED",
        )


class ForbiddenError(KortanaException):
    """Raised when user lacks required permissions"""

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(
            message=message,
            status_code=403,
            error_code="FORBIDDEN",
        )


class ConflictError(KortanaException):
    """Raised when operation conflicts with existing state"""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=409,
            error_code="CONFLICT",
            details=details,
        )


class ExternalServiceError(KortanaException):
    """Raised when external API call fails"""

    def __init__(
        self,
        service: str,
        message: str,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ):
        full_message = f"External service error ({service}): {message}"
        super().__init__(
            message=full_message,
            status_code=status_code,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service, **(details or {})},
        )


class RateLimitError(KortanaException):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: int):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window} seconds",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"limit": limit, "window": window},
        )


class TimeoutError(KortanaException):
    """Raised when operation times out"""

    def __init__(self, operation: str, timeout_seconds: int):
        super().__init__(
            message=f"Operation '{operation}' timed out after {timeout_seconds}s",
            status_code=504,
            error_code="TIMEOUT",
            details={"operation": operation, "timeout_seconds": timeout_seconds},
        )


class InternalServerError(KortanaException):
    """Raised for unexpected internal errors"""

    def __init__(
        self, message: str = "Internal server error", details: dict[str, Any] | None = None
    ):
        super().__init__(
            message=message,
            status_code=500,
            error_code="INTERNAL_SERVER_ERROR",
            details=details,
        )
