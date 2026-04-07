"""Tests for middleware/rate_limit.py"""
import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import Request

from src.kortana.middleware.rate_limit import (
    InMemoryRateLimitStore,
    RateLimitConfig,
    RateLimitExceeded,
    RateLimitMiddleware,
    check_rate_limit,
    create_rate_limit_response,
    default_config,
    get_client_identifier,
    get_rate_limit_for_tier,
    rate_limit_dependency,
    rate_limited,
)


def make_request(path="/api/test", method="GET", client_ip="127.0.0.1", headers=None):
    """Helper to create a mock FastAPI Request"""
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
        "client": (client_ip, 12345),  # Starlette reads client from scope
    }
    if headers:
        scope["headers"] = [
            (k.lower().encode(), v.encode()) for k, v in headers.items()
        ]
    return Request(scope)


class TestRateLimitConfig:
    def test_defaults(self):
        cfg = RateLimitConfig()
        assert cfg.requests == 100
        assert cfg.window_seconds == 60
        assert cfg.free_tier == (20, 60)
        assert cfg.basic_tier == (50, 60)
        assert cfg.premium_tier == (200, 60)

    def test_tier_limits(self):
        cfg = RateLimitConfig()
        assert "admin" in cfg.tier_limits
        assert "user" in cfg.tier_limits
        assert "anonymous" in cfg.tier_limits
        assert cfg.tier_limits["admin"][0] == 500

    def test_default_config_exists(self):
        assert default_config is not None
        assert isinstance(default_config, RateLimitConfig)


class TestInMemoryRateLimitStore:
    @pytest.mark.asyncio
    async def test_initial_count_zero(self):
        store = InMemoryRateLimitStore()
        count = await store.get_count("user1", "/api/test", 60)
        assert count == 0

    @pytest.mark.asyncio
    async def test_increment_increases_count(self):
        store = InMemoryRateLimitStore()
        count = await store.increment("user1", "/api/test", 60)
        assert count == 1
        count = await store.increment("user1", "/api/test", 60)
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_count_after_increment(self):
        store = InMemoryRateLimitStore()
        await store.increment("user2", "/api/path", 60)
        await store.increment("user2", "/api/path", 60)
        count = await store.get_count("user2", "/api/path", 60)
        assert count == 2

    @pytest.mark.asyncio
    async def test_get_remaining(self):
        store = InMemoryRateLimitStore()
        await store.increment("user3", "/api/x", 60)
        remaining = await store.get_remaining("user3", "/api/x", 60, 10)
        assert remaining == 9

    @pytest.mark.asyncio
    async def test_get_remaining_at_zero(self):
        store = InMemoryRateLimitStore()
        for _ in range(5):
            await store.increment("user4", "/api/y", 60)
        remaining = await store.get_remaining("user4", "/api/y", 60, 3)
        assert remaining == 0

    @pytest.mark.asyncio
    async def test_get_reset_time_no_history(self):
        store = InMemoryRateLimitStore()
        reset = await store.get_reset_time("newuser", "/api/z", 60)
        assert reset > int(time.time())

    @pytest.mark.asyncio
    async def test_get_reset_time_with_history(self):
        store = InMemoryRateLimitStore()
        await store.increment("user5", "/api/w", 60)
        reset = await store.get_reset_time("user5", "/api/w", 60)
        assert reset > 0

    @pytest.mark.asyncio
    async def test_different_endpoints_tracked_separately(self):
        store = InMemoryRateLimitStore()
        await store.increment("user6", "/api/a", 60)
        await store.increment("user6", "/api/b", 60)
        count_a = await store.get_count("user6", "/api/a", 60)
        count_b = await store.get_count("user6", "/api/b", 60)
        assert count_a == 1
        assert count_b == 1

    @pytest.mark.asyncio
    async def test_different_users_tracked_separately(self):
        store = InMemoryRateLimitStore()
        await store.increment("userA", "/api/test", 60)
        await store.increment("userA", "/api/test", 60)
        await store.increment("userB", "/api/test", 60)
        count_a = await store.get_count("userA", "/api/test", 60)
        count_b = await store.get_count("userB", "/api/test", 60)
        assert count_a == 2
        assert count_b == 1

    @pytest.mark.asyncio
    async def test_internal_key_format(self):
        store = InMemoryRateLimitStore()
        key = store._get_key("user", "endpoint")
        assert "ratelimit" in key
        assert "user" in key
        assert "endpoint" in key


class TestGetClientIdentifier:
    def test_falls_back_to_ip(self):
        req = make_request(client_ip="192.168.1.1")
        ident = get_client_identifier(req)
        assert "ip:" in ident
        assert "192.168.1.1" in ident

    def test_api_key_header(self):
        req = make_request(headers={"X-API-Key": "myapikey123"})
        ident = get_client_identifier(req)
        assert ident.startswith("apikey:")

    def test_bearer_token(self):
        req = make_request(headers={"Authorization": "Bearer mytoken123"})
        ident = get_client_identifier(req)
        assert ident.startswith("token:")

    def test_x_forwarded_for(self):
        req = make_request(headers={"X-Forwarded-For": "10.0.0.1, 10.0.0.2"})
        ident = get_client_identifier(req)
        # X-Forwarded-For takes priority over client IP
        assert "10.0.0.1" in ident

    def test_no_client_host(self):
        scope = {
            "type": "http",
            "method": "GET",
            "path": "/api/test",
            "query_string": b"",
            "headers": [],
        }
        req = Request(scope)
        # _client is None by default
        ident = get_client_identifier(req)
        assert "ip:" in ident or "unknown" in ident


class TestGetRateLimitForTier:
    def test_user_tier(self):
        limit, window = get_rate_limit_for_tier("user")
        assert limit == 100
        assert window == 60

    def test_admin_tier(self):
        limit, window = get_rate_limit_for_tier("admin")
        assert limit == 500

    def test_service_tier(self):
        limit, window = get_rate_limit_for_tier("service")
        assert limit == 1000

    def test_anonymous_tier(self):
        limit, window = get_rate_limit_for_tier("anonymous")
        assert limit == 20

    def test_unknown_tier_defaults_to_user(self):
        limit, window = get_rate_limit_for_tier("unknown_tier")
        assert limit == 100


class TestRateLimitExceeded:
    def test_exception_has_429_status(self):
        exc = RateLimitExceeded(limit=100, reset_after=60)
        assert exc.status_code == 429

    def test_exception_has_headers(self):
        exc = RateLimitExceeded(limit=50, reset_after=30)
        assert "X-RateLimit-Limit" in exc.headers
        assert exc.headers["X-RateLimit-Limit"] == "50"
        assert exc.headers["Retry-After"] == "30"


class TestCheckRateLimit:
    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self):
        req = make_request()
        result = await check_rate_limit(req, tier="user")
        assert "X-RateLimit-Limit" in result
        assert "X-RateLimit-Remaining" in result

    @pytest.mark.asyncio
    async def test_raises_when_limit_exceeded(self):
        import src.kortana.middleware.rate_limit as rl_module
        from src.kortana.middleware.rate_limit import InMemoryRateLimitStore

        # Use a fresh store with very low limit
        fresh_store = InMemoryRateLimitStore()
        original_store = rl_module._rate_limit_store
        rl_module._rate_limit_store = fresh_store

        try:
            # Use anonymous tier (20 req/min) and pre-fill the store
            req = make_request(client_ip="10.99.99.99")
            ident = get_client_identifier(req)
            for _ in range(20):
                await fresh_store.increment(ident, req.url.path, 60)

            with pytest.raises(RateLimitExceeded):
                await check_rate_limit(req, tier="anonymous")
        finally:
            rl_module._rate_limit_store = original_store

    @pytest.mark.asyncio
    async def test_custom_endpoint_parameter(self):
        req = make_request()
        result = await check_rate_limit(req, endpoint="/custom/endpoint", tier="user")
        assert result is not None


class TestRateLimitDependency:
    @pytest.mark.asyncio
    async def test_returns_callable(self):
        dep = rate_limit_dependency(tier="user")
        assert callable(dep)

    @pytest.mark.asyncio
    async def test_dependency_callable_returns_headers(self):
        dep = rate_limit_dependency(tier="user")
        req = make_request()
        result = await dep(req)
        assert isinstance(result, dict)


class TestCreateRateLimitResponse:
    def test_returns_json_response(self):
        resp = create_rate_limit_response(100, 50, 60)
        assert resp.status_code == 429

    def test_response_has_expected_fields(self):
        resp = create_rate_limit_response(100, 50, 60, "Too many requests")
        content = resp.body
        import json

        data = json.loads(content)
        assert "error" in data
        assert "limit" in data
        assert "remaining" in data
        assert data["limit"] == 100
        assert data["remaining"] == 50

    def test_response_headers(self):
        resp = create_rate_limit_response(100, 50, 60)
        headers = dict(resp.headers)
        assert "x-ratelimit-limit" in headers


class TestRateLimitMiddleware:
    def test_instantiation(self):
        app = MagicMock()
        middleware = RateLimitMiddleware(app)
        assert middleware.tier == "user"
        assert "/api/health" in middleware.exclude_paths

    def test_custom_exclude_paths(self):
        app = MagicMock()
        middleware = RateLimitMiddleware(app, exclude_paths=["/custom"])
        assert "/custom" in middleware.exclude_paths

    @pytest.mark.asyncio
    async def test_passes_non_http_scope_through(self):
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        scope = {"type": "websocket"}
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_called_once_with(scope, receive, send)

    @pytest.mark.asyncio
    async def test_excluded_path_passes_through(self):
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        scope = {"type": "http", "path": "/api/health", "method": "GET"}
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_called_once()

    @pytest.mark.asyncio
    async def test_non_excluded_path_passes_through(self):
        app = AsyncMock()
        middleware = RateLimitMiddleware(app)
        scope = {"type": "http", "path": "/api/agents/list", "method": "GET"}
        receive = AsyncMock()
        send = AsyncMock()
        await middleware(scope, receive, send)
        app.assert_called_once()


class TestRateLimitedDecorator:
    @pytest.mark.asyncio
    async def test_allows_request_under_limit(self):
        @rate_limited(requests=100, window_seconds=60)
        async def endpoint(request):
            return {"status": "ok"}

        req = make_request()
        result = await endpoint(request=req)
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_without_request_still_runs(self):
        @rate_limited(requests=100, window_seconds=60)
        async def endpoint():
            return {"status": "ok"}

        result = await endpoint()
        assert result == {"status": "ok"}
