"""
Tests for security middleware: SecurityHeadersMiddleware, RequestIDMiddleware,
RequestLoggingMiddleware, and RateLimitMiddleware fallback behavior.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi import FastAPI
from starlette.responses import Response


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

    def test_legacy_middleware_accepts_redis_url(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(
            mock_app,
            requests_per_minute=100,
            redis_url="redis://localhost:6379/0",
        )

        assert middleware.requests_per_minute == 100
        assert middleware.redis_url == "redis://localhost:6379/0"

    @pytest.mark.asyncio
    async def test_dispatch_redis_error_allows_request(self):
        """When Redis fails, request should still be processed (fail-open)."""
        from redis.exceptions import RedisError

        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=60)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url.path = "/api/gemini/chat"

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
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url.path = "/api/gemini/chat"

        expected_response = MagicMock()
        call_next = AsyncMock(return_value=expected_response)

        with patch.object(
            middleware.redis, "incr", side_effect=RuntimeError("loop closed")
        ):
            response = await middleware.dispatch(mock_request, call_next)

        assert response == expected_response

    @pytest.mark.asyncio
    async def test_dispatch_rate_limit_returns_429_json_response(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=2)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url.path = "/api/gemini/chat"

        call_next = AsyncMock()

        with patch.object(middleware.redis, "incr", AsyncMock(return_value=3)), patch.object(
            middleware.redis, "expire", AsyncMock()
        ), patch.object(middleware.redis, "ttl", AsyncMock(return_value=60)):
            response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 429
        assert response.headers["Retry-After"] == "60"
        assert response.headers["X-RateLimit-Limit"] == "2"
        assert call_next.await_count == 0

    @pytest.mark.asyncio
    async def test_dispatch_excluded_path_skips_rate_limit(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        mock_app = MagicMock()
        middleware = RateLimitMiddleware(mock_app, requests_per_minute=2)

        mock_request = MagicMock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        mock_request.method = "GET"
        mock_request.url.path = "/assets/index.js"

        expected_response = Response(status_code=200)
        call_next = AsyncMock(return_value=expected_response)

        response = await middleware.dispatch(mock_request, call_next)

        assert response.status_code == 200
        call_next.assert_awaited_once()

    def test_trusted_proxy_supports_cidr_entries(self):
        from src.kortana.middleware.security import RateLimitMiddleware

        middleware = RateLimitMiddleware(
            MagicMock(), trusted_proxies=("127.0.0.0/24", "10.0.0.5")
        )

        assert middleware._is_trusted_proxy("127.0.0.1") is True
        assert middleware._is_trusted_proxy("10.0.0.5") is True
        assert middleware._is_trusted_proxy("192.168.1.10") is False


class FakeAsyncRedis:
    def __init__(self):
        self.counts: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counts[key] = self.counts.get(key, 0) + 1
        return self.counts[key]

    async def expire(self, key: str, seconds: int) -> bool:
        self.ttls[key] = seconds
        return True

    async def ttl(self, key: str) -> int:
        return self.ttls.get(key, 60)


def build_rate_limit_test_app(
    monkeypatch: pytest.MonkeyPatch,
    *,
    requests_per_minute: int = 2,
    period_seconds: int = 60,
    proxy_mode: bool = False,
    trusted_proxies: tuple[str, ...] = (),
    event_recorder: list[tuple[str, str, str | None, str]] | None = None,
):
    from src.kortana.middleware import security as security_module

    fake_redis = FakeAsyncRedis()
    fake_redis_factory = MagicMock()
    fake_redis_factory.from_url = MagicMock(return_value=fake_redis)
    monkeypatch.setattr(security_module, "Redis", fake_redis_factory)

    if event_recorder is not None:
        monkeypatch.setattr(
            security_module,
            "track_rate_limit_event",
            lambda route, client_ip, forwarded_ip, status: event_recorder.append(
                (route, client_ip, forwarded_ip, status)
            ),
        )
        monkeypatch.setattr(security_module, "track_rate_limit_hit", lambda *args: None)

    app = FastAPI()
    app.add_middleware(
        security_module.RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        period_seconds=period_seconds,
        proxy_mode=proxy_mode,
        trusted_proxies=trusted_proxies,
    )

    @app.get("/limited")
    async def limited():
        return {"ok": True}

    @app.get("/api/health")
    async def health():
        return {"status": "alive"}

    return app, fake_redis


class TestRateLimitMiddlewareIntegration:
    @pytest.mark.asyncio
    async def test_trusted_proxy_uses_forwarded_ip_and_returns_429(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        events: list[tuple[str, str, str | None, str]] = []
        app, fake_redis = build_rate_limit_test_app(
            monkeypatch,
            trusted_proxies=("127.0.0.1",),
            event_recorder=events,
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            headers = {"X-Forwarded-For": "1.2.3.4"}
            await client.get("/limited", headers=headers)
            await client.get("/limited", headers=headers)
            response = await client.get("/limited", headers=headers)

        assert fake_redis.counts["ratelimit:1.2.3.4"] == 3
        assert response.status_code == 429
        assert response.json()["error"] == "rate_limited"
        assert response.json()["retry_after"] == 60
        assert response.headers["Retry-After"] == "60"
        assert response.headers["X-RateLimit-Limit"] == "2"
        assert response.headers["X-RateLimit-Remaining"] == "0"
        assert int(response.headers["X-RateLimit-Reset"]) > 0
        assert any(status == "limited" for _, _, _, status in events)

    @pytest.mark.asyncio
    async def test_spoofed_forwarded_for_is_ignored_when_proxy_not_trusted(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        events: list[tuple[str, str, str | None, str]] = []
        app, fake_redis = build_rate_limit_test_app(
            monkeypatch,
            trusted_proxies=(),
            proxy_mode=False,
            event_recorder=events,
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            headers = {"X-Forwarded-For": "9.9.9.9"}
            await client.get("/limited", headers=headers)
            await client.get("/limited", headers=headers)
            response = await client.get("/limited", headers=headers)

        assert "ratelimit:9.9.9.9" not in fake_redis.counts
        assert len(fake_redis.counts) == 1
        assert response.status_code == 429
        assert any(status == "spoof-ignored" for _, _, _, status in events)

    @pytest.mark.asyncio
    async def test_health_endpoint_bypasses_rate_limit(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        app, fake_redis = build_rate_limit_test_app(monkeypatch)

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            headers = {"X-Forwarded-For": "7.7.7.7"}
            await client.get("/limited", headers=headers)
            await client.get("/limited", headers=headers)
            over_limit = await client.get("/limited", headers=headers)
            counts_before = dict(fake_redis.counts)
            health = await client.get("/api/health", headers=headers)

        assert over_limit.status_code == 429
        assert health.status_code == 200
        assert fake_redis.counts == counts_before

    @pytest.mark.asyncio
    async def test_proxy_mode_trusts_forwarded_ip_without_trusted_proxy_list(
        self, monkeypatch: pytest.MonkeyPatch
    ):
        app, fake_redis = build_rate_limit_test_app(
            monkeypatch,
            proxy_mode=True,
            trusted_proxies=(),
        )

        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            headers = {"X-Forwarded-For": "8.8.8.8"}
            await client.get("/limited", headers=headers)
            await client.get("/limited", headers=headers)
            response = await client.get("/limited", headers=headers)

        assert fake_redis.counts["ratelimit:8.8.8.8"] == 3
        assert response.status_code == 429


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
