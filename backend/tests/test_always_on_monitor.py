"""Tests for src/kortana/services/always_on_monitor.py - Always-on monitoring service"""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.models import GitHubTask
from src.kortana.services.always_on_monitor import AlwaysOnMonitor


@pytest.fixture
def mock_db_manager():
    """Create mock database manager"""
    mock = MagicMock()
    mock.get_session = MagicMock()
    return mock


@pytest.fixture
def monitor(mock_db_manager):
    """Create AlwaysOnMonitor instance with mocked db"""
    with patch("src.kortana.services.always_on_monitor.get_db_manager") as mock_get_db:
        mock_get_db.return_value = mock_db_manager
        monitor = AlwaysOnMonitor()
        monitor.monitoring_enabled = True
        return monitor


class TestAlwaysOnMonitorInit:
    def test_init_defaults(self, mock_db_manager):
        """Test AlwaysOnMonitor initialization with defaults"""
        with patch(
            "src.kortana.services.always_on_monitor.get_db_manager"
        ) as mock_get_db:
            mock_get_db.return_value = mock_db_manager

            monitor = AlwaysOnMonitor()

            assert monitor.is_running is False
            assert monitor.db_manager is mock_db_manager
            assert monitor.check_interval > 0
            assert monitor.max_concurrent_tasks > 0
            assert "issues_fetched" in monitor.stats

    def test_init_with_env_variables(self, mock_db_manager, monkeypatch):
        """Test initialization respects environment variables"""
        monkeypatch.setenv("MONITOR_CHECK_INTERVAL", "120")
        monkeypatch.setenv("MAX_CONCURRENT_TASKS", "10")
        monkeypatch.setenv("ALWAYS_ON_MONITORING", "true")

        with patch(
            "src.kortana.services.always_on_monitor.get_db_manager"
        ) as mock_get_db:
            mock_get_db.return_value = mock_db_manager

            monitor = AlwaysOnMonitor()

            assert monitor.check_interval == 120
            assert monitor.max_concurrent_tasks == 10
            assert monitor.monitoring_enabled is True

    def test_init_monitoring_disabled(self, mock_db_manager, monkeypatch):
        """Test initialization when monitoring is disabled"""
        monkeypatch.setenv("ALWAYS_ON_MONITORING", "false")

        with patch(
            "src.kortana.services.always_on_monitor.get_db_manager"
        ) as mock_get_db:
            mock_get_db.return_value = mock_db_manager

            monitor = AlwaysOnMonitor()

            assert monitor.monitoring_enabled is False


class TestMonitoringCycle:
    @pytest.mark.asyncio
    async def test_monitoring_cycle_success(self, monitor):
        """Test successful monitoring cycle"""
        monitor._fetch_new_issues = AsyncMock(return_value=[])
        monitor._process_task_pipeline = AsyncMock()
        monitor._run_hop_cycle = AsyncMock()

        await monitor._monitoring_cycle()

        assert monitor._fetch_new_issues.called
        assert monitor._process_task_pipeline.called
        assert monitor._run_hop_cycle.called
        assert monitor.stats["last_run"] is not None

    @pytest.mark.asyncio
    async def test_monitoring_cycle_with_new_issues(self, monitor):
        """Test monitoring cycle with new issues"""
        # Create mock task
        mock_task = MagicMock(spec=GitHubTask)
        mock_task.github_issue_number = 123
        mock_task.title = "Test issue"

        monitor._fetch_new_issues = AsyncMock(return_value=[mock_task])
        monitor._process_task_pipeline = AsyncMock()
        monitor._run_hop_cycle = AsyncMock()

        await monitor._monitoring_cycle()

        assert monitor.stats["issues_fetched"] == 1
        assert monitor.stats["tasks_created"] == 1

    @pytest.mark.asyncio
    async def test_monitoring_cycle_handles_exceptions(self, monitor):
        """Test monitoring cycle handles exceptions gracefully (error recovery)"""
        monitor._fetch_new_issues = AsyncMock(side_effect=Exception("Fetch error"))
        monitor._process_task_pipeline = AsyncMock()
        monitor._run_hop_cycle = AsyncMock()

        with patch("src.kortana.services.always_on_monitor.logger"):
            # _monitoring_cycle has error recovery - it catches individual step
            # exceptions and continues, so it should NOT raise
            await monitor._monitoring_cycle()
            # Verify the fetch was attempted
            monitor._fetch_new_issues.assert_called_once()


class TestFetchNewIssues:
    @pytest.mark.asyncio
    async def test_fetch_new_issues_success(self, monitor):
        """Test successful issue fetching"""
        mock_task = MagicMock(spec=GitHubTask)
        mock_task.github_issue_number = 456
        mock_task.title = "New issue"

        mock_db = AsyncMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        with patch(
            "src.kortana.services.always_on_monitor.GitHubAutonomyService"
        ) as mock_service:
            mock_github = AsyncMock()
            mock_github.fetch_and_queue_issues = AsyncMock(return_value=[mock_task])
            mock_service.return_value = mock_github

            result = await monitor._fetch_new_issues()

            assert len(result) == 1
            assert result[0].github_issue_number == 456

    @pytest.mark.asyncio
    async def test_fetch_new_issues_no_issues(self, monitor):
        """Test fetching when no new issues exist"""
        mock_db = AsyncMock()
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        with patch(
            "src.kortana.services.always_on_monitor.GitHubAutonomyService"
        ) as mock_service:
            mock_github = AsyncMock()
            mock_github.fetch_and_queue_issues = AsyncMock(return_value=[])
            mock_service.return_value = mock_github

            result = await monitor._fetch_new_issues()

            assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_new_issues_handles_error(self, monitor):
        """Test fetch handles exceptions"""
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(side_effect=Exception("DB error"))
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        with patch("src.kortana.services.always_on_monitor.logger"):
            result = await monitor._fetch_new_issues()

            assert result == []


class TestProcessTaskPipeline:
    @pytest.mark.asyncio
    async def test_process_task_pipeline_success(self, monitor):
        """Test successful task pipeline processing"""
        mock_task = MagicMock(spec=GitHubTask)
        mock_task.id = 1
        mock_task.status = "pending"
        mock_task.github_issue_number = 789
        mock_task.title = "Task"

        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[mock_task]))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        # Mock the task filter to return the task with a mock context
        mock_context = MagicMock()
        mock_context.impact_level = MagicMock()
        mock_context.impact_level.value = "high"
        monitor.task_filter = MagicMock()
        monitor.task_filter.filter_and_rank_tasks = AsyncMock(
            return_value=[(mock_task, mock_context)]
        )

        monitor._process_single_task = AsyncMock()

        with patch("src.kortana.services.always_on_monitor.HOPAutonomyService"):
            await monitor._process_task_pipeline()

            assert monitor._process_single_task.called

    @pytest.mark.asyncio
    async def test_process_task_pipeline_no_pending(self, monitor):
        """Test pipeline with no pending tasks"""
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(
            return_value=MagicMock(all=MagicMock(return_value=[]))
        )
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        with patch("src.kortana.services.always_on_monitor.HOPAutonomyService"):
            await monitor._process_task_pipeline()

            # Should complete without errors


class TestProcessSingleTask:
    @pytest.mark.asyncio
    async def test_process_pending_task(self, monitor):
        """Test processing a pending task"""
        mock_task = MagicMock(spec=GitHubTask)
        mock_task.id = 1
        mock_task.status = "pending"
        mock_task.github_issue_number = 100

        mock_db = AsyncMock()

        with patch(
            "src.kortana.services.always_on_monitor.GitHubAutonomyService"
        ) as mock_service:
            mock_github = AsyncMock()
            mock_github.analyze_task = AsyncMock()
            mock_service.return_value = mock_github

            await monitor._process_single_task(mock_task, mock_db)

            assert mock_github.analyze_task.called

    @pytest.mark.asyncio
    async def test_process_analyzed_task(self, monitor):
        """Test processing an analyzed task"""
        mock_task = MagicMock(spec=GitHubTask)
        mock_task.id = 2
        mock_task.status = "analyzed"

        mock_db = AsyncMock()

        with patch(
            "src.kortana.services.always_on_monitor.GitHubAutonomyService"
        ) as mock_service:
            mock_github = AsyncMock()
            mock_github.plan_task = AsyncMock()
            mock_service.return_value = mock_github

            await monitor._process_single_task(mock_task, mock_db)

            assert mock_github.plan_task.called


class TestRunHOPCycle:
    @pytest.mark.asyncio
    async def test_run_hop_cycle_success(self, monitor):
        """Test successful HOP cycle"""
        with patch(
            "src.kortana.services.always_on_monitor.HOPAutonomyService"
        ) as mock_service:
            mock_hop = AsyncMock()
            mock_hop.run_hop_cycle = AsyncMock(return_value={"status": "success"})
            mock_service.return_value = mock_hop

            await monitor._run_hop_cycle()

            assert mock_hop.run_hop_cycle.called

    @pytest.mark.asyncio
    async def test_run_hop_cycle_handles_error(self, monitor):
        """Test HOP cycle error handling"""
        with patch(
            "src.kortana.services.always_on_monitor.HOPAutonomyService"
        ) as mock_service:
            mock_hop = AsyncMock()
            mock_hop.run_hop_cycle = AsyncMock(side_effect=Exception("HOP error"))
            mock_service.return_value = mock_hop

            with patch("src.kortana.services.always_on_monitor.logger"):
                # Should not raise - HOP cycle failure shouldn't stop monitoring
                await monitor._run_hop_cycle()


class TestMonitorControl:
    def test_stop_monitoring(self, monitor):
        """Test stopping the monitor"""
        monitor.is_running = True
        mock_github = MagicMock()
        mock_hop = MagicMock()
        monitor.github_service = mock_github
        monitor.hop_service = mock_hop

        monitor.stop_monitoring()

        assert monitor.is_running is False
        assert mock_github.close.called
        assert mock_hop.close.called

    def test_get_status(self, monitor):
        """Test getting monitor status"""
        monitor.is_running = True
        monitor.stats["issues_fetched"] = 5

        status = monitor.get_status()

        assert status["is_running"] is True
        assert status["monitoring_enabled"] is True
        assert status["check_interval"] > 0
        assert "statistics" in status
        assert status["statistics"]["issues_fetched"] == 5

    @pytest.mark.asyncio
    async def test_get_task_status(self, monitor):
        """Test getting task status"""
        mock_db = AsyncMock()
        mock_result = AsyncMock()
        mock_result.scalar_one = AsyncMock(return_value=10)
        mock_db.execute = AsyncMock(return_value=mock_result)

        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_db)
        mock_session.__aexit__ = AsyncMock(return_value=None)
        monitor.db_manager.get_session = MagicMock(return_value=mock_session)

        status = await monitor.get_task_status()

        assert isinstance(status, dict)


class TestStartMonitoring:
    @pytest.mark.asyncio
    async def test_start_monitoring_when_disabled(self, monitor):
        """Test starting monitor when disabled"""
        monitor.monitoring_enabled = False

        with patch("src.kortana.services.always_on_monitor.logger"):
            await monitor.start_monitoring()

            assert monitor.is_running is False

    @pytest.mark.asyncio
    async def test_start_monitoring_already_running(self, monitor):
        """Test starting when already running"""
        monitor.is_running = True

        with patch("src.kortana.services.always_on_monitor.logger"):
            await monitor.start_monitoring()

            assert monitor.is_running is True

    @pytest.mark.asyncio
    async def test_start_monitoring_handles_interrupt(self, monitor):
        """Test start_monitoring handles KeyboardInterrupt"""
        monitor._monitoring_cycle = AsyncMock(side_effect=KeyboardInterrupt())

        with patch("src.kortana.services.always_on_monitor.logger"):
            await monitor.start_monitoring()

            assert monitor.is_running is False
