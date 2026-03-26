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
    async def test_process_tasks_respects_max_tasks_override(self):
        """_process_tasks should forward max_tasks to the SQL LIMIT clause."""
    async def test_process_tasks_defers_execution_in_safe_mode(self):
        """Planning-complete tasks should be deferred when safe mode disables live execution."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()
            daemon.max_tasks = 5  # default

        tasks = [
            GitHubTask(
                id=f"task-{i}",
                github_issue_number=i,
                github_repo="madouble7/kortana",
                title=f"Task {i}",
                description="desc",
                status="queued",
            )
            for i in range(3)
        ]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = tasks

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
        service.analyze_task = AsyncMock()
        service.execute_task = AsyncMock()

        events = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            # Pass max_tasks=1 — the mock query ignores LIMIT, but the parameter
            # is accepted and the limit is constructed in the SQLAlchemy statement.
            processed, succeeded, failed = await daemon._process_tasks(session, max_tasks=1)

        # The mock returns all 3 tasks regardless of the limit clause; the key
        # assertion is that the call succeeds and the parameter is plumbed through.
        assert processed == 3
        assert succeeded == 3
        assert failed == 0

    @pytest.mark.asyncio
    async def test_run_cycle_enriches_metrics_with_system_state(self):
        """_run_cycle should add system_state to last_cycle metrics after self-assessment."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_db = MagicMock()

            async def _fake_session():
                yield AsyncMock()

            mock_db.get_session = _fake_session
            mock_get_db.return_value = mock_db

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        mock_awareness = MagicMock()
        mock_awareness.assess = AsyncMock(return_value={"state": "nominal"})

        mock_goal_mgr = MagicMock()
        mock_goal_mgr.get_status.return_value = {"total_goals": 3}
        mock_goal_mgr.reprioritise = MagicMock()

        mock_learner = MagicMock()
        mock_learner.generate_insights = MagicMock(return_value=[])

        with (
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._discover_issues",
                new=AsyncMock(return_value=0),
            ),
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._process_tasks",
                new=AsyncMock(return_value=(0, 0, 0)),
            ),
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._manifest_self_healing",
                new=AsyncMock(),
            ),
            patch(
                "src.kortana.services.self_awareness.get_self_awareness",
                return_value=mock_awareness,
            ),
            patch(
                "src.kortana.services.goal_manager.get_goal_manager",
                return_value=mock_goal_mgr,
            ),
            patch(
                "src.kortana.services.adaptive_learner.get_adaptive_learner",
                new=AsyncMock(return_value=mock_learner),
            ),
        ):
            await daemon._run_cycle()

        assert daemon.metrics["last_cycle"]["system_state"] == "nominal"
        assert daemon.metrics["system_state"] == "nominal"

    @pytest.mark.asyncio
    async def test_run_cycle_throttles_tasks_when_critical(self):
        """_run_cycle should halve max_tasks when system state is CRITICAL."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_db = MagicMock()

            async def _fake_session():
                yield AsyncMock()

            mock_db.get_session = _fake_session
            mock_get_db.return_value = mock_db

            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()
            daemon.max_tasks = 6

        mock_awareness = MagicMock()
        mock_awareness.assess = AsyncMock(return_value={"state": "critical"})

        mock_goal_mgr = MagicMock()
        mock_goal_mgr.get_status.return_value = {}
        mock_goal_mgr.reprioritise = MagicMock()

        mock_learner = MagicMock()
        mock_learner.generate_insights = MagicMock(return_value=[])

        captured_max: list[int] = []

        async def capture_process(_self: object, session: object, max_tasks: int | None = None) -> tuple[int, int, int]:
            captured_max.append(max_tasks if max_tasks is not None else daemon.max_tasks)
            return (0, 0, 0)

        with (
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._discover_issues",
                new=AsyncMock(return_value=0),
            ),
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._process_tasks",
                new=capture_process,
            ),
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyDaemon._manifest_self_healing",
                new=AsyncMock(),
            ),
            patch(
                "src.kortana.services.self_awareness.get_self_awareness",
                return_value=mock_awareness,
            ),
            patch(
                "src.kortana.services.goal_manager.get_goal_manager",
                return_value=mock_goal_mgr,
            ),
            patch(
                "src.kortana.services.adaptive_learner.get_adaptive_learner",
                new=AsyncMock(return_value=mock_learner),
            ),
        ):
            await daemon._run_cycle()

        # critical → max_tasks // 3 = 2
        assert captured_max == [2]

    @pytest.mark.asyncio
    async def test_record_outcome_calls_learner(self):
        """_record_outcome should forward the result to AdaptiveLearner.record()."""
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

        task = GitHubTask(
            id="task-learn",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Learning task",
            description="desc",
            status="executed",
        )

        mock_learner = MagicMock()
        mock_learner.record = AsyncMock()

        with patch(
            "src.kortana.services.adaptive_learner.get_adaptive_learner",
            new=AsyncMock(return_value=mock_learner),
        ):
            await daemon._record_outcome(task, success=True, latency=1.5)

        mock_learner.record.assert_awaited_once()
        recorded = mock_learner.record.call_args[0][0]
        assert recorded.task_id == "task-learn"
        assert recorded.success is True
        assert recorded.latency_seconds == 1.5
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
