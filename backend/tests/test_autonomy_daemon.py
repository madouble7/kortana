"""Tests for src/kortana/services/autonomy_daemon.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.models import GitHubTask


class TestAutonomyDaemon:
    @pytest.mark.asyncio
    async def test_process_tasks_emits_task_complete_with_title(self):
        """Completed task events should use the GitHubTask title field."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        task = GitHubTask(
            id="task-123",
            github_issue_number=53,
            github_repo="madouble7/kortana",
            title="Consolidate dual backend stacks",
            description="desc",
            status="planning_complete",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [task]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        service = MagicMock()
        service.execute_task = AsyncMock()

        events = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(session)

        assert (processed, succeeded, failed, deferred) == (1, 1, 0, 0)
        task_complete = next(event for event in events if event.type == "task_complete")
        assert task_complete.data["task_id"] == "task-123"
        assert task_complete.data["title"] == "Consolidate dual backend stacks"

    @pytest.mark.asyncio
    async def test_process_tasks_treats_queued_as_pending(self):
        """Queued tasks should enter the analyze stage like pending tasks."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        task = GitHubTask(
            id="task-queued",
            github_issue_number=11000,
            github_repo="madouble7/kortana",
            title="Queued autonomy task",
            description="desc",
            status="queued",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [task]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        service = MagicMock()
        service.analyze_task = AsyncMock()

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(session)

        assert (processed, succeeded, failed, deferred) == (1, 1, 0, 0)
        service.analyze_task.assert_awaited_once_with(task)

    @pytest.mark.asyncio
    async def test_process_tasks_defers_execution_in_safe_mode(self):
        """Planning-complete tasks should be deferred when safe mode disables live execution."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        daemon.safe_mode = True
        daemon.live_execution_enabled = False

        task = GitHubTask(
            id="task-deferred",
            github_issue_number=88,
            github_repo="madouble7/kortana",
            title="Defer autonomous execution",
            description="desc",
            status="planning_complete",
        )

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [task]

        session = AsyncMock()
        session.execute = AsyncMock(return_value=mock_result)

        service = MagicMock()
        service.execute_task = AsyncMock()

        events = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(session)

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        service.execute_task.assert_not_awaited()
        task_deferred = next(event for event in events if event.type == "task_deferred")
        assert task_deferred.data["task_id"] == "task-deferred"

    @pytest.mark.asyncio
    async def test_self_regulate_applies_runtime_profile(self):
        """Daemon should adopt the runtime profile returned by self-awareness."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        fake_engine = MagicMock()
        fake_engine.regulate = AsyncMock(
            return_value={
                "assessment": {"state": "degraded", "snapshot": {}, "drift": [], "corrections": []},
                "runtime_profile": {
                    "generated_at": "2026-03-26T00:00:00",
                    "state": "degraded",
                    "safe_mode": True,
                    "allow_live_execution": False,
                    "max_tasks_per_cycle": 1,
                    "cycle_interval_seconds": 450,
                    "execution_confidence": 0.44,
                    "reasons": ["low_execution_confidence"],
                    "corrections": [],
                },
            }
        )

        with patch(
            "src.kortana.services.autonomy_daemon.get_self_awareness",
            return_value=fake_engine,
        ):
            await daemon._self_regulate()

        assert daemon.safe_mode is True
        assert daemon.live_execution_enabled is False
        assert daemon.max_tasks == 1
        assert daemon.cycle_interval == 450
        assert daemon.metrics["adaptive_adjustments"] == 1
