"""Hermetic integration tests for rate-limit proxy trust behavior."""

import httpx
import pytest

from tests.test_security_middleware import build_rate_limit_test_app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_trusted_proxy_forwarded_ip_is_used(monkeypatch: pytest.MonkeyPatch):
    events: list[tuple[str, str, str | None, str]] = []
    app, fake_redis = build_rate_limit_test_app(
        monkeypatch,
        requests_per_minute=2,
        trusted_proxies=("127.0.0.1",),
        event_recorder=events,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        headers = {"X-Forwarded-For": "1.2.3.4"}
        response_one = await client.get("/api/info", headers=headers)
        response_two = await client.get("/api/info", headers=headers)
        response_three = await client.get("/api/info", headers=headers)

    assert response_one.status_code == 200
    assert response_two.status_code == 200
    assert response_three.status_code == 429
    assert response_three.json() == {
        "error": "rate_limited",
        "detail": "Too many requests",
        "message": "Too many requests",
        "status_code": 429,
        "retry_after": 60,
        "details": {
            "route": "/api/info",
            "client_ip": "1.2.3.4",
            "forwarded_ip": "1.2.3.4",
            "immediate_proxy": "127.0.0.1",
            "limit": 2,
            "current_count": 3,
        },
    }
    assert response_three.headers["Retry-After"] == "60"
    assert response_three.headers["X-RateLimit-Limit"] == "2"
    assert response_three.headers["X-RateLimit-Remaining"] == "0"
    assert int(response_three.headers["X-RateLimit-Reset"]) > 0
    assert fake_redis.counts["ratelimit:1.2.3.4"] == 3
    assert ("/api/info", "1.2.3.4", "1.2.3.4", "limited") in events


@pytest.mark.asyncio
@pytest.mark.integration
async def test_untrusted_proxy_spoof_is_ignored(monkeypatch: pytest.MonkeyPatch):
    events: list[tuple[str, str, str | None, str]] = []
    app, fake_redis = build_rate_limit_test_app(
        monkeypatch,
        requests_per_minute=2,
        trusted_proxies=(),
        proxy_mode=False,
        event_recorder=events,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        headers = {"X-Forwarded-For": "9.9.9.9"}
        response_one = await client.get("/api/info", headers=headers)
        response_two = await client.get("/api/info", headers=headers)
        response_three = await client.get("/api/info", headers=headers)

    assert response_one.status_code == 200
    assert response_two.status_code == 200
    assert response_three.status_code == 429
    assert response_three.json()["error"] == "rate_limited"
    assert "ratelimit:9.9.9.9" not in fake_redis.counts
    assert fake_redis.counts["ratelimit:127.0.0.1"] == 3
    assert ("/api/info", "127.0.0.1", "9.9.9.9", "spoof-ignored") in events
    assert ("/api/info", "127.0.0.1", "9.9.9.9", "limited") in events


@pytest.mark.asyncio
@pytest.mark.integration
async def test_proxy_mode_override_trusts_forwarded_ip(
    monkeypatch: pytest.MonkeyPatch,
):
    app, fake_redis = build_rate_limit_test_app(
        monkeypatch,
        requests_per_minute=1,
        proxy_mode=True,
        trusted_proxies=(),
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        headers = {"X-Forwarded-For": "203.0.113.77"}
        response_one = await client.get("/api/info", headers=headers)
        response_two = await client.get("/api/info", headers=headers)

    assert response_one.status_code == 200
    assert response_two.status_code == 429
    assert response_two.json()["details"]["client_ip"] == "203.0.113.77"
    assert fake_redis.counts["ratelimit:203.0.113.77"] == 2


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_bypass_when_other_route_is_over_limit(
    monkeypatch: pytest.MonkeyPatch,
):
    app, fake_redis = build_rate_limit_test_app(
        monkeypatch,
        requests_per_minute=1,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        await client.get("/api/info")
        limited = await client.get("/api/info")
        counts_before = dict(fake_redis.counts)
        health = await client.get("/api/health")

    assert limited.status_code == 429
    assert health.status_code == 200
    assert health.headers.get("X-RateLimit-Limit") is None
    assert fake_redis.counts == counts_before
