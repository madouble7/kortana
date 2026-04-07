"""
Tests for custom exception classes in src.kortana.exceptions
"""

import pytest

from src.kortana.exceptions import (
    ConflictError,
    ExternalServiceError,
    ForbiddenError,
    InternalServerError,
    KortanaException,
    NotFoundError,
    RateLimitError,
    TimeoutError,
    UnauthorizedError,
    ValidationError,
)


class TestKortanaException:
    """Base exception tests"""

    def test_default_status_code(self):
        exc = KortanaException("oops")
        assert exc.status_code == 500
        assert exc.message == "oops"
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.details == {}

    def test_custom_fields(self):
        exc = KortanaException(
            "custom", status_code=503, error_code="MY_ERROR", details={"k": "v"}
        )
        assert exc.status_code == 503
        assert exc.error_code == "MY_ERROR"
        assert exc.details == {"k": "v"}

    def test_to_dict(self):
        exc = KortanaException(
            "msg", status_code=400, error_code="CODE", details={"x": 1}
        )
        d = exc.to_dict()
        assert d["error"] == "CODE"
        assert d["message"] == "msg"
        assert d["status_code"] == 400
        assert d["details"] == {"x": 1}

    def test_is_exception(self):
        exc = KortanaException("msg")
        with pytest.raises(KortanaException):
            raise exc


class TestValidationError:
    def test_status_code(self):
        exc = ValidationError("invalid input")
        assert exc.status_code == 422
        assert exc.error_code == "VALIDATION_ERROR"

    def test_with_details(self):
        exc = ValidationError("bad field", details={"field": "email"})
        assert exc.details == {"field": "email"}

    def test_without_details(self):
        exc = ValidationError("bad")
        assert exc.details == {}


class TestNotFoundError:
    def test_basic(self):
        exc = NotFoundError("User")
        assert exc.status_code == 404
        assert exc.error_code == "NOT_FOUND"
        assert "User not found" in exc.message

    def test_with_id(self):
        exc = NotFoundError("Task", "abc-123")
        assert "abc-123" in exc.message
        assert exc.details["resource_id"] == "abc-123"

    def test_without_id(self):
        exc = NotFoundError("Agent")
        assert exc.details["resource"] == "Agent"
        assert exc.details["resource_id"] is None


class TestUnauthorizedError:
    def test_default_message(self):
        exc = UnauthorizedError()
        assert exc.status_code == 401
        assert exc.error_code == "UNAUTHORIZED"
        assert "Authentication" in exc.message

    def test_custom_message(self):
        exc = UnauthorizedError("Token expired")
        assert "Token expired" in exc.message


class TestForbiddenError:
    def test_default(self):
        exc = ForbiddenError()
        assert exc.status_code == 403
        assert exc.error_code == "FORBIDDEN"

    def test_custom_message(self):
        exc = ForbiddenError("Admin only")
        assert "Admin only" in exc.message


class TestConflictError:
    def test_basic(self):
        exc = ConflictError("email already used")
        assert exc.status_code == 409
        assert exc.error_code == "CONFLICT"

    def test_with_details(self):
        exc = ConflictError("dup", details={"field": "email"})
        assert exc.details["field"] == "email"


class TestExternalServiceError:
    def test_basic(self):
        exc = ExternalServiceError("stripe", "timeout")
        assert exc.status_code == 502
        assert exc.error_code == "EXTERNAL_SERVICE_ERROR"
        assert "stripe" in exc.message

    def test_custom_status_code(self):
        exc = ExternalServiceError("gemini", "quota exceeded", status_code=429)
        assert exc.status_code == 429

    def test_details_merged(self):
        exc = ExternalServiceError("github", "not found", details={"repo": "kortana"})
        assert exc.details["service"] == "github"
        assert exc.details["repo"] == "kortana"


class TestRateLimitError:
    def test_basic(self):
        exc = RateLimitError(100, 60)
        assert exc.status_code == 429
        assert exc.error_code == "RATE_LIMIT_EXCEEDED"
        assert "100" in exc.message
        assert "60" in exc.message
        assert exc.details["limit"] == 100
        assert exc.details["window"] == 60


class TestTimeoutError:
    def test_basic(self):
        exc = TimeoutError("fetch_issues", 30)
        assert exc.status_code == 504
        assert exc.error_code == "TIMEOUT"
        assert "fetch_issues" in exc.message
        assert "30" in exc.message
        assert exc.details["operation"] == "fetch_issues"
        assert exc.details["timeout_seconds"] == 30


class TestInternalServerError:
    def test_default(self):
        exc = InternalServerError()
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_SERVER_ERROR"
        assert "Internal" in exc.message

    def test_custom_message(self):
        exc = InternalServerError("db crashed", details={"trace": "..."})
        assert "db crashed" in exc.message
        assert exc.details["trace"] == "..."
