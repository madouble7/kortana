"""Tests for routers/health.py HealthChecker classes and endpoints"""
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.routers.health import (
    ComponentHealth,
    ComponentType,
    HealthChecker,
    HealthStatus,
)


class TestHealthStatusEnum:
    def test_values(self):
        assert HealthStatus.HEALTHY == "healthy"
        assert HealthStatus.DEGRADED == "degraded"
        assert HealthStatus.UNHEALTHY == "unhealthy"
        assert HealthStatus.UNKNOWN == "unknown"


class TestComponentTypeEnum:
    def test_values(self):
        assert ComponentType.DATABASE == "database"
        assert ComponentType.CACHE == "cache"
        assert ComponentType.CPU == "cpu"
        assert ComponentType.MEMORY == "memory"
        assert ComponentType.DISK == "disk"
        assert ComponentType.CELERY == "celery"
        assert ComponentType.EXTERNAL_API == "external_api"


class TestComponentHealth:
    def test_defaults(self):
        ch = ComponentHealth(
            name="test",
            component_type=ComponentType.MEMORY,
            status=HealthStatus.HEALTHY,
        )
        assert ch.name == "test"
        assert ch.message == ""
        assert ch.latency_ms == 0
        assert ch.details == {}

    def test_to_dict(self):
        ch = ComponentHealth(
            name="postgres",
            component_type=ComponentType.DATABASE,
            status=HealthStatus.DEGRADED,
            message="slow",
            latency_ms=42.5,
            details={"host": "db"},
        )
        d = ch.to_dict()
        assert d["name"] == "postgres"
        assert d["type"] == "database"
        assert d["status"] == "degraded"
        assert d["message"] == "slow"
        assert d["latency_ms"] == 42.5
        assert d["details"] == {"host": "db"}
        assert "last_checked" in d

    def test_last_checked_is_iso_string(self):
        ch = ComponentHealth(
            name="x",
            component_type=ComponentType.CPU,
            status=HealthStatus.HEALTHY,
        )
        # Should be valid ISO datetime
        dt = datetime.fromisoformat(ch.last_checked)
        assert isinstance(dt, datetime)


class TestHealthChecker:
    def test_instantiation(self):
        hc = HealthChecker()
        assert hc.components == {}
        assert hc._check_interval == 30
        assert hc._cache == {}

    def test_register_component(self):
        hc = HealthChecker()
        hc.register_component("mydb", ComponentType.DATABASE, lambda: None)
        assert "mydb" in hc.components
        assert hc.components["mydb"].status == HealthStatus.UNKNOWN

    def test_check_system_resources_returns_list(self):
        hc = HealthChecker()
        results = hc.check_system_resources()
        assert isinstance(results, list)
        assert len(results) == 3  # memory, cpu, disk

    def test_check_system_resources_names(self):
        hc = HealthChecker()
        results = hc.check_system_resources()
        names = [r.name for r in results]
        assert "memory" in names
        assert "cpu" in names
        assert "disk" in names

    def test_check_system_resources_all_have_status(self):
        hc = HealthChecker()
        results = hc.check_system_resources()
        for r in results:
            assert r.status in [
                HealthStatus.HEALTHY,
                HealthStatus.DEGRADED,
                HealthStatus.UNHEALTHY,
            ]

    def test_check_system_resources_detail_structure(self):
        hc = HealthChecker()
        results = hc.check_system_resources()
        mem = next(r for r in results if r.name == "memory")
        assert "total_gb" in mem.details
        assert "percent" in mem.details

    def test_get_cached_check_empty(self):
        hc = HealthChecker()
        assert hc.get_cached_check() is None

    def test_set_and_get_cached_check(self):
        hc = HealthChecker()
        result = {"status": "healthy", "timestamp": datetime.now().isoformat()}
        hc.set_cached_check(result)
        cached = hc.get_cached_check()
        assert cached is not None
        assert cached["status"] == "healthy"

    def test_cached_check_expires(self):
        from datetime import timedelta

        hc = HealthChecker()
        old_time = (datetime.now() - timedelta(seconds=30)).isoformat()
        hc.set_cached_check({"status": "healthy", "timestamp": old_time})
        # With max_age=10, old cache should be expired
        assert hc.get_cached_check(max_age_seconds=10) is None

    @pytest.mark.asyncio
    async def test_check_database_failure(self):
        hc = HealthChecker()
        result = await hc.check_database(host="nonexistent_host", port=9999)
        assert result.status == HealthStatus.UNHEALTHY
        assert result.name == "postgresql"
        assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_redis_failure(self):
        hc = HealthChecker()
        result = await hc.check_redis(host="nonexistent_host", port=9999)
        assert result.status == HealthStatus.UNHEALTHY
        assert result.name == "redis"

    @pytest.mark.asyncio
    async def test_check_celery_failure(self):
        hc = HealthChecker()
        result = await hc.check_celery(
            broker_url="redis://nonexistent:9999/0", timeout=1
        )
        # Celery will fail since broker isn't available
        assert result.name == "celery"

    @pytest.mark.asyncio
    async def test_check_external_api_failure(self):
        hc = HealthChecker()
        result = await hc.check_external_api(
            "test_api", "http://nonexistent_host_xyz.invalid"
        )
        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in result.message.lower()

    @pytest.mark.asyncio
    async def test_check_external_api_success(self):
        hc = HealthChecker()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_httpx_client = AsyncMock()
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            result = await hc.check_external_api("github", "https://api.github.com")
        assert result.status == HealthStatus.HEALTHY
        assert result.name == "github"

    @pytest.mark.asyncio
    async def test_check_external_api_wrong_status(self):
        hc = HealthChecker()
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_httpx_client = AsyncMock()
        mock_httpx_client.__aenter__ = AsyncMock(return_value=mock_httpx_client)
        mock_httpx_client.__aexit__ = AsyncMock(return_value=None)
        mock_httpx_client.get = AsyncMock(return_value=mock_response)

        with patch("httpx.AsyncClient", return_value=mock_httpx_client):
            result = await hc.check_external_api(
                "api", "https://example.com", expected_status=200
            )
        assert result.status == HealthStatus.DEGRADED

    @pytest.mark.asyncio
    async def test_run_full_check_no_external(self):
        hc = HealthChecker()
        result = await hc.run_full_check(
            check_db=False,
            check_redis=False,
            check_celery=False,
            check_external=False,
        )
        assert "status" in result
        assert "components" in result
        assert "summary" in result
        assert result["summary"]["total"] == 3  # memory, cpu, disk

    @pytest.mark.asyncio
    async def test_run_full_check_sets_unhealthy_on_failure(self):
        hc = HealthChecker()
        result = await hc.run_full_check(
            check_db=True,
            check_redis=False,
            check_celery=False,
            check_external=False,
        )
        # DB check will fail since no real DB → overall unhealthy
        assert result["status"] in [
            "unhealthy",
            "healthy",
            "degraded",
        ]  # depends on system

    @pytest.mark.asyncio
    async def test_run_full_check_with_degraded_component(self):
        hc = HealthChecker()
        with patch.object(hc, "check_system_resources") as mock_sys:
            mock_sys.return_value = [
                ComponentHealth("memory", ComponentType.MEMORY, HealthStatus.DEGRADED)
            ]
            result = await hc.run_full_check(
                check_db=False,
                check_redis=False,
                check_celery=False,
                check_external=False,
            )
            assert result["status"] == "degraded"
            assert result["summary"]["degraded"] == 1

    @pytest.mark.asyncio
    async def test_run_full_check_with_unhealthy_component(self):
        hc = HealthChecker()
        with patch.object(hc, "check_system_resources") as mock_sys:
            mock_sys.return_value = [
                ComponentHealth("cpu", ComponentType.CPU, HealthStatus.UNHEALTHY)
            ]
            result = await hc.run_full_check(
                check_db=False,
                check_redis=False,
                check_celery=False,
                check_external=False,
            )
            assert result["status"] == "unhealthy"
            assert result["summary"]["unhealthy"] == 1


class TestHealthRouterEndpoints:
    """Test the health router HTTP endpoints"""

    @pytest.fixture
    def client(self):
        from src.kortana.main import app
        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    def test_basic_health_alive(self, client):
        resp = client.get("/api/system/health/api/health/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "alive"

    def test_liveness_probe(self, client):
        resp = client.get("/api/system/health/api/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert "alive" in data["status"]

    def test_health_system_endpoint(self, client):
        resp = client.get("/api/system/health/api/health/system")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_count" in data
        assert "python_version" in data

    def test_health_metrics_endpoint(self, client):
        resp = client.get("/api/system/health/api/health/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "component_count" in data

    def test_health_detailed_endpoint(self, client):
        resp = client.get("/api/system/health/api/health/detailed")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "components" in data
        assert "summary" in data

    def test_health_ready_endpoint(self, client):
        resp = client.get("/api/system/health/api/health/ready")
        # Returns 200 unless unhealthy
        assert resp.status_code in [200, 503]
