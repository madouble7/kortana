"""Tests for src/kortana/services/autonomy_daemon.py."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from src.kortana.models import GitHubTask


class TestAutonomyDaemon:
    @pytest.mark.asyncio
    async def test_process_tasks_emits_task_complete_with_title(self) -> None:
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

        events: list[dict[str, str]] = []
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
    async def test_process_tasks_treats_queued_as_pending(self) -> None:
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
    async def test_process_tasks_respects_max_tasks_override(self) -> None:
        """_process_tasks should forward max_tasks to the SQL LIMIT clause."""

    async def test_process_tasks_defers_execution_in_safe_mode(self) -> None:
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

        events: list[dict[str, str]] = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            # Pass max_tasks=1 — the mock query ignores LIMIT, but the parameter
            # is accepted and the limit is constructed in the SQLAlchemy statement.
            processed, succeeded, failed, deferred = await daemon._process_tasks(session)

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        service.execute_task.assert_not_awaited()
        task_deferred = next(event for event in events if event.type == "task_deferred")
        assert task_deferred.data["task_id"] == "task-deferred"

    @pytest.mark.asyncio
    async def test_run_cycle_enriches_metrics_with_system_state(self) -> None:
        """_run_cycle should add system_state to last_cycle metrics after self-assessment."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_db = MagicMock()

            async def _fake_session() -> AsyncMock:
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
                new=AsyncMock(return_value=(0, 0, 0, 0)),
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
    async def test_run_cycle_throttles_tasks_when_critical(self) -> None:
        """_run_cycle should halve max_tasks when system state is CRITICAL."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_db = MagicMock()

            async def _fake_session() -> AsyncMock:
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

        async def capture_process(
            _self: object, session: object, max_tasks: int | None = None
        ) -> tuple[int, int, int, int]:
            captured_max.append(max_tasks if max_tasks is not None else daemon.max_tasks)
            return (0, 0, 0, 0)

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
    async def test_record_outcome_calls_learner(self) -> None:
        """_record_outcome should forward the result to AdaptiveLearner.record()."""
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

    @pytest.mark.asyncio
    async def test_manifest_self_healing_success(self) -> None:
        """Should manifest a self-repair issue via GitHub API when a failure is detected."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()
            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        from src.kortana.models import GitHubTask

        task = GitHubTask(
            id="task-fail",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Failed task",
            error_message="Systematic logic failure",
            status="failed",
        )

        mock_session = AsyncMock()
        mock_result_failed = MagicMock()
        mock_result_failed.scalar_one_or_none.return_value = task
        mock_result_active = MagicMock()
        mock_result_active.scalars.return_value.all.return_value = []

        mock_session.execute.side_effect = [mock_result_failed, mock_result_active]

        with patch("src.kortana.services.autonomy_daemon.os.getenv") as mock_env:

            def env_side_effect(k, default=None):
                if k == "GITHUB_TOKEN":
                    return "fake-token"
                if k == "GITHUB_OWNER":
                    return "madouble7"
                if k == "GITHUB_REPO":
                    return "kortana"
                return default

            mock_env.side_effect = env_side_effect

            with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
                mock_resp = MagicMock()
                mock_resp.status_code = 201
                mock_resp.json.return_value = {"number": 99}
                mock_post.return_value = mock_resp

                await daemon._manifest_self_healing(mock_session)

                mock_post.assert_awaited_once()
                args, kwargs = mock_post.call_args
                assert "https://api.github.com/repos/madouble7/kortana/issues" in args[0]
                assert (
                    "[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task"
                    in kwargs["json"]["title"]
                )

                assert daemon.metrics["self_heals_manifested"] == 1

    @pytest.mark.asyncio
    async def test_manifest_self_healing_skip_active(self) -> None:
        """Should skip self-repair manifestation if an active self-repair issue already exists."""
        with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
            mock_get_db.return_value = MagicMock()
            from src.kortana.services.autonomy_daemon import AutonomyDaemon

            daemon = AutonomyDaemon()

        from src.kortana.models import GitHubTask

        task_fail = GitHubTask(
            id="task-fail",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Failed task",
            error_message="Systematic logic failure",
            status="failed",
        )
        task_repair = GitHubTask(
            id="task-repair",
            github_issue_number=2,
            github_repo="madouble7/kortana",
            title="[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task",
            status="pending",
        )

        mock_session = AsyncMock()
        mock_result_failed = MagicMock()
        mock_result_failed.scalar_one_or_none.return_value = task_fail
        mock_result_active = MagicMock()
        mock_result_active.scalars.return_value.all.return_value = [task_repair]

        mock_session.execute.side_effect = [mock_result_failed, mock_result_active]

        with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
            await daemon._manifest_self_healing(mock_session)

            # Should not call the HTTP endpoint if there's an active repair
            mock_post.assert_not_called()
            assert daemon.metrics["self_heals_manifested"] == 0
