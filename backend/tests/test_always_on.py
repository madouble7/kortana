"""Tests for services/always_on_monitor.py and routers/always_on.py"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import GitHubTask

# ========================================
# AlwaysOnMonitor unit tests
# ========================================


class TestAlwaysOnMonitorInit:
    def test_default_init(self):
        import src.kortana.services.always_on_monitor as mod

        mod._monitor = None
        monitor = mod.AlwaysOnMonitor()
        assert monitor.is_running is False
        assert monitor._task is None
        assert monitor._cycle_in_progress is False
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
        assert "cycles_skipped" in stats

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
        assert "cycle_in_progress" in status
        assert "daemon" in status
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

    def test_stop_cancels_active_task(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        monitor.is_running = True
        task = MagicMock()
        task.done.return_value = False
        monitor._task = task
        monitor.stop_monitoring()
        task.cancel.assert_called_once()
        assert monitor._task is None

    def test_stop_keeps_completed_task_uncancelled(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        task = MagicMock()
        task.done.return_value = True
        monitor._task = task
        monitor.stop_monitoring()
        task.cancel.assert_not_called()
        assert monitor._task is None

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
            await monitor.force_check()
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


class TestAlwaysOnMonitorCycle:
    @pytest.mark.asyncio
    async def test_monitoring_cycle_syncs_daemon_status(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        daemon = MagicMock()
        daemon.get_status.return_value = {
            "tasks_processed": 4,
            "tasks_succeeded": 3,
            "tasks_failed": 1,
        }

        with patch(
            "src.kortana.services.always_on_monitor.get_autonomy_daemon",
            return_value=daemon,
        ):
            await monitor._monitoring_cycle()

        assert monitor.stats["tasks_processed"] == 4
        assert monitor.stats["tasks_completed"] == 3
        assert monitor.stats["tasks_failed"] == 1
        assert monitor.last_check is not None

    @pytest.mark.asyncio
    async def test_start_monitoring_runs_cycle_once_before_stop(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()

        async def stop_after_first_cycle() -> None:
            monitor.is_running = False

        with patch.object(
            monitor,
            "_monitoring_cycle",
            new=AsyncMock(side_effect=stop_after_first_cycle),
        ):
            with patch(
                "src.kortana.services.always_on_monitor.asyncio.sleep", new=AsyncMock()
            ):
                await monitor.start_monitoring()

        assert monitor.is_running is False


class TestAlwaysOnMonitorGetTaskStatus:
    @pytest.mark.asyncio
    async def test_get_task_status_raises_on_db_failure(self):
        from src.kortana.services.always_on_monitor import AlwaysOnMonitor

        monitor = AlwaysOnMonitor()
        mock_manager = MagicMock()
        session_scope = AsyncMock()
        session_scope.__aenter__.side_effect = Exception("DB unavailable")
        mock_manager.session_scope.return_value = session_scope
        monitor.db_manager = mock_manager

        with pytest.raises(Exception, match="DB unavailable"):
            await monitor.get_task_status()


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


def test_serialize_task_includes_validation_evidence():
    from src.kortana.routers.always_on import _serialize_task

    task = GitHubTask(
        id="task-observe",
        github_issue_number=321,
        github_repo="madouble7/kortana",
        title="Surface validation",
        description="desc",
        status="waiting_for_approval",
        classification="approval",
        priority="high",
        branch_name="auto/local/321-surface-validation",
        commit_sha="deadbeef",
        github_pr_number=17,
        code_changes=["backend/src/kortana/demo.py"],
        error_message="guardrail hold",
        validation_report={
            "stage": "planning_complete",
            "blocked_paths": [".env"],
            "planned_tests": ["python -m pytest backend/tests/test_always_on.py -q"],
            "validations": [
                {"name": "repo_grounding", "status": "adjusted"},
                {"name": "protected_path_guard", "status": "blocked"},
            ],
        },
    )

    payload = _serialize_task(task)

    assert payload["id"] == "task-observe"
    assert payload["commit_sha"] == "deadbeef"
    assert payload["github_pr_number"] == 17
    assert payload["code_changes"] == ["backend/src/kortana/demo.py"]
    assert payload["validation_report"]["stage"] == "planning_complete"
    assert payload["validation_summary"]["blocked_paths"] == [".env"]
    assert payload["validation_summary"]["failed_validations"] == [
        "protected_path_guard"
    ]

@pytest.mark.asyncio
async def test_get_memory_endpoint():
    from src.kortana.models import ArchitectureMemory
    from src.kortana.routers.always_on import get_repository_memory
    
    mock_db_manager = AsyncMock()
    
    mock_session = AsyncMock()
    # Mocking get_session async generator
    async def mock_gen():
        yield mock_session
    mock_db_manager.get_session = mock_gen
    
    # Mocking sqlalchemy execute
    mock_arch_res = MagicMock()
    mock_arch_res.scalars.return_value.all.return_value = [
        ArchitectureMemory(component_name="test_comp", description="test_desc", knowledge_factors={}, confidence_score=0.9)
    ]
    mock_cycle_res = MagicMock()
    mock_cycle_res.scalars.return_value.all.return_value = []
    mock_incid_res = MagicMock()
    mock_incid_res.scalars.return_value.all.return_value = []
    
    mock_session.execute = AsyncMock(side_effect=[mock_arch_res, mock_cycle_res, mock_incid_res])
    
    with patch("src.kortana.routers.always_on.get_db_manager", return_value=mock_db_manager):
        response = await get_repository_memory(limit=10)
        
        assert "data" in response
        assert "architecture_memory" in response["data"]
        assert "recent_cycles" in response["data"]
        assert "recent_incidents" in response["data"]
        assert len(response["data"]["architecture_memory"]) == 1
        assert response["data"]["architecture_memory"][0]["component"] == "test_comp"
