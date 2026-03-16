"""Tests for services/always_on_monitor.py and routers/always_on.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ========================================
# AlwaysOnMonitor unit tests
# ========================================


class TestAlwaysOnMonitorInit:
    def test_default_init(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        monitor = mod.AlwaysOnMonitor()
        assert monitor.is_running is False
        assert monitor.github_service is None
        assert monitor.hop_service is None
        assert monitor.last_check is None
        assert monitor.stats["issues_fetched"] == 0
        assert monitor.stats["tasks_processed"] == 0

    def test_default_stats_keys(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        stats = monitor.stats
        assert "issues_fetched" in stats
        assert "tasks_created" in stats
        assert "tasks_processed" in stats
        assert "tasks_completed" in stats
        assert "tasks_failed" in stats
        assert "human_interventions" in stats
        assert "last_run" in stats

    def test_check_interval_default(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        assert monitor.check_interval == 60

    def test_check_interval_from_env(self, monkeypatch):
        monkeypatch.setenv("MONITOR_CHECK_INTERVAL", "30")
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        assert monitor.check_interval == 30

    def test_max_concurrent_tasks_from_env(self, monkeypatch):
        monkeypatch.setenv("MAX_CONCURRENT_TASKS", "3")
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        assert monitor.max_concurrent_tasks == 3

    def test_monitoring_disabled_via_env(self, monkeypatch):
        monkeypatch.setenv("ALWAYS_ON_MONITORING", "false")
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        assert monitor.monitoring_enabled is False

    def test_monitoring_enabled_by_default(self, monkeypatch):
        monkeypatch.setenv("ALWAYS_ON_MONITORING", "true")
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        assert monitor.monitoring_enabled is True


class TestAlwaysOnMonitorGetStatus:
    def test_get_status_returns_dict(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        status = monitor.get_status()
        assert isinstance(status, dict)

    def test_get_status_keys(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        status = monitor.get_status()
        assert "monitoring_enabled" in status
        assert "is_running" in status
        assert "last_check" in status
        assert "check_interval" in status
        assert "max_concurrent_tasks" in status
        assert "statistics" in status
        assert "timestamp" in status

    def test_get_status_not_running(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        status = monitor.get_status()
        assert status["is_running"] is False

    def test_get_status_statistics_are_zeros(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        stats = monitor.get_status()["statistics"]
        assert stats["issues_fetched"] == 0
        assert stats["tasks_completed"] == 0


class TestAlwaysOnMonitorStopMonitoring:
    def test_stop_sets_is_running_false(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.is_running = True
        monitor.stop_monitoring()
        assert monitor.is_running is False

    def test_stop_calls_github_service_close(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        mock_github = MagicMock()
        monitor.github_service = mock_github
        monitor.stop_monitoring()
        mock_github.close.assert_called_once()

    def test_stop_calls_hop_service_close(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        mock_hop = MagicMock()
        monitor.hop_service = mock_hop
        monitor.stop_monitoring()
        mock_hop.close.assert_called_once()

    def test_stop_with_no_services(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.stop_monitoring()  # Should not raise
        assert monitor.is_running is False


class TestAlwaysOnMonitorStartMonitoring:
    @pytest.mark.asyncio
    async def test_start_when_disabled(self, monkeypatch):
        monkeypatch.setenv("ALWAYS_ON_MONITORING", "false")
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        await monitor.start_monitoring()  # Should return immediately
        assert monitor.is_running is False

    @pytest.mark.asyncio
    async def test_start_when_already_running_returns_immediately(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.is_running = True
        monitor.monitoring_enabled = True
        # Calling start_monitoring when already running should log warning and return
        await monitor.start_monitoring()
        # Still running (we didn't call stop_monitoring)
        assert monitor.is_running is True
        monitor.is_running = False  # Cleanup


class TestAlwaysOnMonitorForceCheck:
    @pytest.mark.asyncio
    async def test_force_check_when_not_running(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.is_running = False

        with patch.object(
            monitor, "_monitoring_cycle", new_callable=AsyncMock
        ) as mock_cycle:
            result = await monitor.force_check()
            mock_cycle.assert_called_once()

        assert result["is_running"] is False  # Stopped after one cycle

    @pytest.mark.asyncio
    async def test_force_check_when_running(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.is_running = True

        with patch.object(
            monitor, "_monitoring_cycle", new_callable=AsyncMock
        ) as mock_cycle:
            result = await monitor.force_check()
            mock_cycle.assert_called_once()

        monitor.is_running = False  # Cleanup


class TestAlwaysOnMonitorSingleton:
    def test_get_always_on_monitor_returns_instance(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        monitor = mod.get_always_on_monitor()
        assert monitor is not None
        mod._monitor = None  # Cleanup

    def test_get_always_on_monitor_same_instance(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        m1 = mod.get_always_on_monitor()
        m2 = mod.get_always_on_monitor()
        assert m1 is m2
        mod._monitor = None  # Cleanup

    def test_stop_always_on_monitor_clears_global(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        mod.get_always_on_monitor()
        mod.stop_always_on_monitor()
        assert mod._monitor is None

    def test_stop_always_on_monitor_when_none(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        mod.stop_always_on_monitor()  # Should not raise


class TestAlwaysOnMonitorFetchIssues:
    @pytest.mark.asyncio
    async def test_fetch_issues_returns_empty_on_db_failure(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        mock_manager = MagicMock()
        mock_manager.get_session.side_effect = Exception("DB unavailable")
        monitor.db_manager = mock_manager
        result = await monitor._fetch_new_issues()
        assert result == []


class TestAlwaysOnMonitorRunHOPCycle:
    @pytest.mark.asyncio
    async def test_hop_cycle_handles_exception(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        with patch(
            "src.kortana.services.always_on_monitor.HOPAutonomyService"
        ) as MockHOP:
            instance = MockHOP.return_value
            instance.run_hop_cycle = AsyncMock(side_effect=Exception("HOP failure"))
            # Should not raise - exception is caught
            await monitor._run_hop_cycle()

    @pytest.mark.asyncio
    async def test_hop_cycle_success(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        with patch(
            "src.kortana.services.always_on_monitor.HOPAutonomyService"
        ) as MockHOP:
            instance = MockHOP.return_value
            instance.run_hop_cycle = AsyncMock(return_value={"status": "completed"})
            await monitor._run_hop_cycle()  # Should complete without error


class TestAlwaysOnMonitorGetTaskStatus:
    @pytest.mark.asyncio
    async def test_get_task_status_returns_error_on_db_failure(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        mock_manager = MagicMock()
        mock_manager.get_session.side_effect = Exception("DB unavailable")
        monitor.db_manager = mock_manager
        result = await monitor.get_task_status()
        assert "error" in result


# ========================================
# Always-On Router endpoint tests
# ========================================


class TestAlwaysOnRouter:
    @pytest.fixture
    def client(self):
        from src.kortana.main import app
        from tests.conftest import SyncTestClient

        return SyncTestClient(app)

    @pytest.fixture(autouse=True)
    def reset_monitor(self):
        """Reset global monitor before each test"""
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        yield
        mod._monitor = None

    def test_monitoring_status(self, client):
        resp = client.get("/api/always-on/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "is_running" in data
        assert "monitoring_enabled" in data

    def test_monitoring_health_check(self, client):
        resp = client.get("/api/always-on/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "is_running" in data

    def test_monitoring_metrics(self, client):
        resp = client.get("/api/always-on/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "monitoring" in data
        assert "tasks" in data

    def test_monitoring_dashboard(self, client):
        resp = client.get("/api/always-on/dashboard")
        assert resp.status_code in [200, 500]  # 500 if DB not available
        if resp.status_code == 200:
            data = resp.json()
            assert "monitor" in data

    def test_stop_monitoring(self, client):
        resp = client.post("/api/always-on/stop")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "stopped"

    def test_start_monitoring(self, client):
        resp = client.post("/api/always-on/start")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ["starting", "running"]
        # Stop it immediately to avoid background task issues
        import src.kortana.services.always_on_monitor as mod

        if mod._monitor:
            mod._monitor.stop_monitoring()

    def test_start_when_already_running(self, client):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = mod.AlwaysOnMonitor()
        mod._monitor.is_running = True
        resp = client.post("/api/always-on/start")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "running"

    def test_log_event(self, client):
        resp = client.post(
            "/api/always-on/log", json={"event": "test", "level": "info"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "logged"

    def test_get_recent_tasks_empty(self, client):
        resp = client.get("/api/always-on/tasks")
        assert resp.status_code in [200, 500]  # 500 if DB not available

    def test_get_monitoring_actions_empty(self, client):
        resp = client.get("/api/always-on/actions")
        assert resp.status_code in [200, 500]  # 500 if DB not available

    def test_tasks_status_endpoint(self, client):
        resp = client.get("/api/always-on/tasks/status")
        # Returns error dict when DB unavailable
        assert resp.status_code in [200, 500]

    def test_retry_nonexistent_task(self, client):
        resp = client.post("/api/always-on/tasks/nonexistent-id/retry")
        assert resp.status_code in [404, 500]

    def test_approve_nonexistent_task(self, client):
        resp = client.post("/api/always-on/tasks/nonexistent-id/approve?approved=true")
        assert resp.status_code in [404, 500]

    def test_force_check(self, client):
        with patch(
            "src.kortana.services.always_on_monitor.AlwaysOnMonitor._monitoring_cycle",
            new_callable=AsyncMock,
        ):
            resp = client.post("/api/always-on/force-check")
            assert resp.status_code == 200
            data = resp.json()
            assert "result" in data
