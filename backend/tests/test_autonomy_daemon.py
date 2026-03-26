"""Tests for src.kortana.services.autonomy_daemon."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.kortana.models import GitHubTask
from src.kortana.services.autonomy_daemon import AutonomyDaemon
from src.kortana.services.operator_directive_service import DirectiveSummary


def build_daemon() -> AutonomyDaemon:
    with patch("src.kortana.services.autonomy_daemon.get_db_manager") as mock_get_db:
        mock_get_db.return_value = MagicMock()
        return AutonomyDaemon()


class TestAutonomyDaemon:
    @pytest.mark.asyncio
    async def test_process_tasks_emits_task_complete_with_title(self) -> None:
        daemon = build_daemon()
        task = GitHubTask(
            id="task-123",
            github_issue_number=53,
            github_repo="madouble7/kortana",
            title="Consolidate dual backend stacks",
            description="desc",
            status="planning_complete",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = MagicMock()
        service.execute_task = AsyncMock()

        events: list[Any] = []
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
        daemon = build_daemon()
        task = GitHubTask(
            id="task-queued",
            github_issue_number=11000,
            github_repo="madouble7/kortana",
            title="Queued autonomy task",
            description="desc",
            status="queued",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

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
    async def test_process_tasks_defers_execution_when_live_execution_disabled(
        self,
    ) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = False

        task = GitHubTask(
            id="task-deferred",
            github_issue_number=88,
            github_repo="madouble7/kortana",
            title="Defer autonomous execution",
            description="desc",
            status="planning_complete",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = MagicMock()
        service.execute_task = AsyncMock()

        events: list[Any] = []
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

    def test_prioritize_tasks_prefers_focus_topics_and_filters_avoid(self) -> None:
        daemon = build_daemon()
        tasks = [
            GitHubTask(
                id="1",
                github_issue_number=1,
                github_repo="madouble7/kortana",
                title="Fix flaky tests",
                description="pytest cleanup",
                status="pending",
            ),
            GitHubTask(
                id="2",
                github_issue_number=2,
                github_repo="madouble7/kortana",
                title="Billing polish",
                description="stripe ui",
                status="pending",
            ),
            GitHubTask(
                id="3",
                github_issue_number=3,
                github_repo="madouble7/kortana",
                title="Improve task queue",
                description="background worker",
                status="pending",
            ),
        ]
        guidance = DirectiveSummary(
            active_count=2,
            focus_topics=["tests"],
            avoid_topics=["billing"],
        )

        selected = daemon._prioritize_tasks(tasks, guidance, limit=3)

        assert [task.id for task in selected] == ["1", "3"]

    @pytest.mark.asyncio
    async def test_self_regulate_applies_runtime_profile(self) -> None:
        daemon = build_daemon()
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
        assert daemon.metrics["system_state"] == "degraded"

    @pytest.mark.asyncio
    async def test_record_outcome_calls_learner(self) -> None:
        daemon = build_daemon()
        task = GitHubTask(
            id="task-learn",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Learning task",
            description="desc",
            status="executed",
        )

        learner = MagicMock()
        learner.record = AsyncMock()

        with patch(
            "src.kortana.services.adaptive_learner.get_adaptive_learner",
            new=AsyncMock(return_value=learner),
        ):
            await daemon._record_outcome(
                task=task,
                success=True,
                latency_seconds=1.5,
            )

        learner.record.assert_awaited_once()
        outcome = learner.record.call_args.args[0]
        assert outcome.task_id == "task-learn"
        assert outcome.success is True
        assert outcome.latency_seconds == 1.5

    @pytest.mark.asyncio
    async def test_manifest_self_healing_success(self) -> None:
        daemon = build_daemon()
        failed_task = GitHubTask(
            id="task-fail",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Failed task",
            error_message="Systematic logic failure",
            status="failed",
        )

        session = AsyncMock()
        failed_result = MagicMock()
        failed_result.scalar_one_or_none.return_value = failed_task
        active_result = MagicMock()
        active_result.scalars.return_value.all.return_value = []
        session.execute.side_effect = [failed_result, active_result]

        client = AsyncMock()
        response = MagicMock()
        response.status_code = 201
        client.post.return_value = response
        client_cm = AsyncMock()
        client_cm.__aenter__.return_value = client
        client_cm.__aexit__.return_value = None

        with (
            patch(
                "src.kortana.services.autonomy_daemon.httpx.AsyncClient",
                return_value=client_cm,
            ),
            patch("src.kortana.services.autonomy_daemon.os.getenv") as mock_env,
        ):
            mock_env.side_effect = (
                lambda key, default=None: {
                    "GITHUB_TOKEN": "fake-token",
                    "GITHUB_OWNER": "madouble7",
                    "GITHUB_REPO": "kortana",
                }.get(key, default)
            )

            await daemon._manifest_self_healing(session)

        client.post.assert_awaited_once()
        args, kwargs = client.post.call_args
        assert "https://api.github.com/repos/madouble7/kortana/issues" == args[0]
        assert (
            "[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task"
            == kwargs["json"]["title"]
        )
        assert daemon.metrics["self_heals_manifested"] == 1

    @pytest.mark.asyncio
    async def test_manifest_self_healing_skips_when_active_issue_exists(self) -> None:
        daemon = build_daemon()
        failed_task = GitHubTask(
            id="task-fail",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Failed task",
            error_message="Systematic logic failure",
            status="failed",
        )
        active_repair = GitHubTask(
            id="task-repair",
            github_issue_number=2,
            github_repo="madouble7/kortana",
            title="[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task",
            status="pending",
        )

        session = AsyncMock()
        failed_result = MagicMock()
        failed_result.scalar_one_or_none.return_value = failed_task
        active_result = MagicMock()
        active_result.scalars.return_value.all.return_value = [active_repair]
        session.execute.side_effect = [failed_result, active_result]

        with patch(
            "src.kortana.services.autonomy_daemon.httpx.AsyncClient"
        ) as mock_client:
            await daemon._manifest_self_healing(session)

        mock_client.assert_not_called()
        assert daemon.metrics["self_heals_manifested"] == 0
