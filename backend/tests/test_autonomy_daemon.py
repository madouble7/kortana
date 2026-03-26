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
            github_repo="KOR-TANA/kortana",
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
            processed, succeeded, failed = await daemon._process_tasks(session)

        assert (processed, succeeded, failed) == (1, 1, 0)
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
            github_repo="KOR-TANA/kortana",
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
            processed, succeeded, failed = await daemon._process_tasks(session)

        assert (processed, succeeded, failed) == (1, 1, 0)
        service.analyze_task.assert_awaited_once_with(task)
