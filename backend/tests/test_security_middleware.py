"""
Tests for security middleware: SecurityHeadersMiddleware, RequestIDMiddleware,
RequestLoggingMiddleware, and RateLimitMiddleware fallback behavior.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestSecurityHeadersMiddleware:
    """Tests for SecurityHeadersMiddleware via real app client."""

    def test_x_content_type_options_header(self, client):
        response = client.get("/api/health")
        assert response.headers.get("x-content-type-options") == "nosniff"

    def test_x_frame_options_header(self, client):
        response = client.get("/api/health")
        assert response.headers.get("x-frame-options") == "DENY"

    def test_x_xss_protection_header(self, client):
        response = client.get("/api/health")
        assert "x-xss-protection" in response.headers

    def test_server_header_is_kortana(self, client):
        response = client.get("/api/health")
        assert response.headers.get("server") == "Kor'tana"

    def test_referrer_policy_header(self, client):
        response = client.get("/api/health")
        assert "referrer-policy" in response.headers


class TestRequestIDMiddleware:
    """Tests for RequestIDMiddleware via real app client."""

    def test_request_id_present(self, client):
        response = client.get("/api/health")
        assert "x-request-id" in response.headers

    def test_request_id_is_uuid_format(self, client):
        import uuid

        response = client.get("/api/health")
        request_id = response.headers.get("x-request-id")
        assert request_id is not None
        # Should parse as valid UUID
        uuid.UUID(request_id)

    def test_different_requests_get_different_ids(self, client):
        r1 = client.get("/api/health")
        r2 = client.get("/api/health")
        assert r1.headers.get("x-request-id") != r2.headers.get("x-request-id")


class TestRateLimitMiddlewareUnit:
    """Unit tests for RateLimitMiddleware logic."""

    def test_middleware_instantiation(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=100)
        assert middleware.requests_per_minute == 100

    def test_middleware_default_requests_per_minute(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app)
        assert middleware.requests_per_minute == 60

    @pytest.mark.asyncio
    async def test_dispatch_redis_error_allows_request(self):
        """When Redis fails, request should still be processed (fail-open)."""
        from redis.exceptions import RedisError

        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=60)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        expected_response = MagicMock()
        call_next = AsyncMock(return_value=expected_response)

        with patch.object(
            middleware.redis, "incr", side_effect=RedisError("redis down")
        ):
            response = await middleware.dispatch(mock_request, call_next)

        # Even with Redis failure, request is processed (fail-open behavior)
        assert response == expected_response
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_dispatch_runtime_error_allows_request(self):
        """When RuntimeError occurs in rate limiting, request should still be processed."""
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=60)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"

        expected_response = MagicMock()
        call_next = AsyncMock(return_value=expected_response)

        with patch.object(
            middleware.redis, "incr", side_effect=RuntimeError("loop closed")
        ):
            response = await middleware.dispatch(mock_request, call_next)

        assert response == expected_response


class TestSecurityHeadersMiddlewareUnit:
    """Unit tests for SecurityHeadersMiddleware dispatch."""

    @pytest.mark.asyncio
    async def test_all_security_headers_added(self):
        from src.kortana.middleware.security import SecurityHeadersMiddleware

        mock_app = MagicMock()
        middleware = SecurityHeadersMiddleware(mock_app)

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        response = await middleware.dispatch(mock_request, call_next)
        assert response.headers["X-Content-Type-Options"] == "nosniff"
        assert response.headers["X-Frame-Options"] == "DENY"
        assert response.headers["Server"] == "Kor'tana"


class TestRequestIDMiddlewareUnit:
    """Unit tests for RequestIDMiddleware."""

    @pytest.mark.asyncio
    async def test_request_id_set_on_state(self):
        from src.kortana.middleware.security import RequestIDMiddleware

        mock_app = MagicMock()
        middleware = RequestIDMiddleware(mock_app)

        mock_request = MagicMock()
        mock_response = MagicMock()
        mock_response.headers = {}
        call_next = AsyncMock(return_value=mock_response)

        await middleware.dispatch(mock_request, call_next)
        assert hasattr(mock_request.state, "request_id")
        assert mock_response.headers["X-Request-ID"] == mock_request.state.request_id
