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

        async def execute_task(
            task_to_execute: GitHubTask, dry_run: bool = False
        ) -> None:
            task_to_execute.status = "executed"

        service = AsyncMock()
        service.execute_task = AsyncMock(side_effect=execute_task)

        events: list[Any] = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

        assert (processed, succeeded, failed, deferred) == (1, 1, 0, 0)
        task_complete = next(event for event in events if event.type == "task_complete")
        assert task_complete.data["task_id"] == "task-123"
        assert task_complete.data["title"] == "Consolidate dual backend stacks"

    @pytest.mark.asyncio
    async def test_process_tasks_ignores_shadow_loop_failures(self) -> None:
        """
        Verify that shadow loop (sandbox dry-run) failures are caught and logged,
        never blocking the live autonomy cycle from proceeding with task analysis.
        """
        daemon = build_daemon()
        task = GitHubTask(
            id="task-124",
            github_issue_number=54,
            github_repo="madouble7/kortana",
            title="Shadow test task",
            description="desc",
            status="pending",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        async def analyze_task(task_to_analyze: GitHubTask) -> None:
            task_to_analyze.status = "analyzed"

        async def plan_task(task_to_plan: GitHubTask) -> None:
            task_to_plan.status = "planning_complete"

        async def execute_task(
            task_to_execute: GitHubTask, dry_run: bool = False
        ) -> None:
            task_to_execute.status = "executed"

        service = AsyncMock()
        service.analyze_task = AsyncMock(side_effect=analyze_task)
        service.plan_task = AsyncMock(side_effect=plan_task)
        service.execute_task = AsyncMock(side_effect=execute_task)

        # Mock settings to enable shadow loop
        mock_settings = MagicMock()
        mock_settings.AUTONOMY_LOOP_SHADOW_ENABLED = True

        with (
            patch(
                "src.kortana.services.autonomy_daemon.get_settings",
                return_value=mock_settings,
            ),
            patch(
                "src.kortana.services.autonomy_daemon.AutonomyLoopBridgeService.run_dry_run",
                side_effect=Exception("Simulated catastrophic sandbox failure"),
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=service,
            ),
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

        # Ensure the live processing loop still successfully analyzed the task despite sandbox crash
        assert (processed, succeeded, failed, deferred) == (1, 1, 0, 0)
        assert task.status == "executed"

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

        async def analyze_task(task_to_analyze: GitHubTask) -> None:
            task_to_analyze.status = "analyzed"

        async def plan_task(task_to_plan: GitHubTask) -> None:
            task_to_plan.status = "planning_complete"

        async def execute_task(
            task_to_execute: GitHubTask, dry_run: bool = False
        ) -> None:
            task_to_execute.status = "executed"

        service = AsyncMock()
        service.analyze_task = AsyncMock(side_effect=analyze_task)
        service.plan_task = AsyncMock(side_effect=plan_task)
        service.execute_task = AsyncMock(side_effect=execute_task)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

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

        service = AsyncMock()
        service.execute_task = AsyncMock()

        events: list[Any] = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        service.execute_task.assert_not_awaited()
        task_deferred = next(event for event in events if event.type == "task_deferred")
        assert task_deferred.data["task_id"] == "task-deferred"

    @pytest.mark.asyncio
    async def test_process_tasks_defers_execution_when_approval_is_required(
        self,
    ) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = False

        task = GitHubTask(
            id="task-review",
            github_issue_number=90,
            github_repo="madouble7/kortana",
            title="Stage for review",
            description="desc",
            status="planning_complete",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = AsyncMock()
        service.execute_task = AsyncMock()

        events: list[Any] = []
        daemon.on_event(events.append)
        guidance = DirectiveSummary(
            active_count=1,
            approval_mode="manual",
            approval_required=True,
        )

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session,
                guidance=guidance,
            )

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        task_deferred = next(event for event in events if event.type == "task_deferred")
        assert task_deferred.data["reason"] == "approval_required"
        service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_tasks_retries_approval_comment_when_github_fails(
        self,
    ) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = True

        task = GitHubTask(
            id="task-retry",
            title="Retry Test",
            status="planning_complete",
            github_issue_number=100,
            github_repo="madouble7/kortana",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = AsyncMock()
        # Mock github comment to fail explicitly
        service.post_issue_comment = AsyncMock(return_value=False)

        events: list[Any] = []
        daemon.on_event(events.append)
        guidance = DirectiveSummary(
            active_count=1,
            approval_mode="manual",
            approval_required=True,
        )

        with (
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=service,
            ),
            patch(
                "src.kortana.services.autonomy_daemon.TaskApprovalService",
                return_value=AsyncMock(
                    evaluate_task=AsyncMock(
                        return_value=MagicMock(
                            approved=False,
                            reason_code="approval_required",
                            rationale="test",
                            shadow_summary=None,
                        )
                    ),
                    record_decision=AsyncMock(return_value=None),
                ),
            ),
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session,
                guidance=guidance,
            )

        # Deferred should not be incremented because we continued early
        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 0)

        # State should be reverted to planning_complete
        assert task.status == "planning_complete"

        # Emits a failure event indicating retryability
        failed_event = next(
            event for event in events if event.type == "github_comment_failed"
        )
        assert failed_event.data["task_id"] == "task-retry"

        # Method was actually called
        service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_tasks_holds_self_aware_review_when_risk_is_high(
        self,
    ) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = True
        daemon.metrics["system_state"] = "degraded"
        daemon.metrics["workspace_bridge"] = {"changed_count": 200}
        daemon.metrics["last_self_regulation"] = {"execution_confidence": 0.58}

        task = GitHubTask(
            id="task-review",
            github_issue_number=91,
            github_repo="madouble7/kortana",
            title="Risky infra rewrite",
            description="desc",
            status="planning_complete",
            priority="high",
            classification="approval",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)
        session.flush = AsyncMock()
        session.add = MagicMock()

        service = AsyncMock()
        service.execute_task = AsyncMock()
        events: list[Any] = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session,
                guidance=DirectiveSummary(approval_mode="self-aware"),
            )

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        assert task.status == "waiting_for_approval"
        service.execute_task.assert_not_awaited()
        task_deferred = next(event for event in events if event.type == "task_deferred")
        assert task_deferred.data["reason"] == "self_approval_hold"

    @pytest.mark.asyncio
    async def test_process_tasks_marks_terminal_analysis_failures(self) -> None:
        daemon = build_daemon()
        task = GitHubTask(
            id="task-failed",
            github_issue_number=89,
            github_repo="madouble7/kortana",
            title="Broken autonomy task",
            description="desc",
            status="pending",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        async def fail_analysis(task_to_fail: GitHubTask) -> None:
            task_to_fail.status = "failed"
            task_to_fail.error_message = "analysis pipeline crashed"

        service = AsyncMock()
        service.analyze_task = AsyncMock(side_effect=fail_analysis)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

        assert (processed, succeeded, failed, deferred) == (1, 0, 1, 0)
        assert daemon._cycle_failed_task_ids == ["task-failed"]

    @pytest.mark.asyncio
    async def test_process_tasks_blocks_abstract_non_executable_tasks(self) -> None:
        daemon = build_daemon()
        task = GitHubTask(
            id="task-abstract",
            github_issue_number=188,
            github_repo="madouble7/kortana",
            title="Quantum Linkage Integration Framework",
            description="Establish a recursive synthesis layer for system resonance.",
            status="pending",
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [task]
        session = AsyncMock()
        session.execute = AsyncMock(return_value=result)

        service = AsyncMock()
        events: list[Any] = []
        daemon.on_event(events.append)

        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
        ):
            processed, succeeded, failed, deferred = await daemon._process_tasks(
                session
            )

        assert (processed, succeeded, failed, deferred) == (1, 0, 0, 1)
        assert task.status == "blocked"
        assert "executability filter" in (task.error_message or "")
        service.analyze_task.assert_not_awaited()
        blocked_event = next(event for event in events if event.type == "task_blocked")
        assert blocked_event.data["task_id"] == "task-abstract"

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

    def test_apply_operator_guidance_supports_protocol_controls(self) -> None:
        daemon = build_daemon()
        guidance = DirectiveSummary(
            active_count=1,
            execution_mode="plan",
            approval_mode="manual",
            approval_required=True,
            handoff_rules=["analyzer -> planner -> executor"],
            override_mode="halt",
            max_tasks_override=1,
        )

        daemon._apply_operator_guidance(guidance)

        # Governance stripped: halt directives are stored but execution is never blocked.
        assert daemon.max_tasks == 1  # throughput hint still honoured
        assert daemon.live_execution_enabled is True
        assert daemon.safe_mode is False
        assert daemon.control_mode == "execute"
        assert daemon.operator_guidance["execution_mode"] == "plan"
        assert daemon.operator_guidance["approval_required"] is True

    def test_apply_operator_guidance_sets_auto_approval_execute_mode(self) -> None:
        daemon = build_daemon()
        daemon.default_approval_mode = "auto"

        daemon._apply_operator_guidance(DirectiveSummary(active_count=0))

        assert daemon.live_execution_enabled is True
        assert daemon.control_mode == "execute"

    def test_apply_operator_guidance_restores_live_execution_when_cleared(self) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = False
        guidance = DirectiveSummary(active_count=0)

        daemon._apply_operator_guidance(guidance)

        # Governance stripped: always execute regardless of prior state.
        assert daemon.control_mode == "execute"
        assert daemon.live_execution_enabled is True

    @pytest.mark.asyncio
    async def test_discover_tasks_uses_local_backlog_when_github_demoted(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")
        daemon = build_daemon()
        session = AsyncMock()
        local_task = GitHubTask(
            id="local-1",
            github_issue_number=-1,
            github_repo="local/workspace",
            title="Local task",
            description="desc",
            status="pending",
        )
        local_service = AsyncMock()
        local_service.discover_workspace_tasks = AsyncMock(return_value=[local_task])

        with (
            patch(
                "src.kortana.services.autonomy_daemon.LocalBacklogService",
                return_value=local_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService"
            ) as mock_github,
        ):
            discovered = await daemon._discover_tasks(
                session,
                guidance=DirectiveSummary(focus_topics=["autonomy"]),
                workspace_status={"dirty": True, "changed_files": ["a.py"]},
            )

        assert discovered == 1
        local_service.discover_workspace_tasks.assert_awaited_once()
        mock_github.assert_not_called()

    @pytest.mark.asyncio
    async def test_self_regulate_applies_runtime_profile(self) -> None:
        daemon = build_daemon()
        fake_engine = MagicMock()
        fake_engine.regulate = AsyncMock(
            return_value={
                "assessment": {
                    "state": "degraded",
                    "snapshot": {},
                    "drift": [],
                    "corrections": [],
                },
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
        existing_result = MagicMock()
        existing_result.scalars.return_value.all.return_value = []
        session.execute.side_effect = [failed_result, active_result, existing_result]

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
            mock_env.side_effect = lambda key, default=None: {
                "GITHUB_TOKEN": "fake-token",
                "GITHUB_OWNER": "madouble7",
                "GITHUB_REPO": "kortana",
                "KORTANA_GITHUB_MODE": "full",
            }.get(key, default)

            await daemon._manifest_self_healing(
                session, candidate_task_ids=[failed_task.id]
            )

        client.post.assert_awaited_once()
        args, kwargs = client.post.call_args
        assert "https://api.github.com/repos/madouble7/kortana/issues" == args[0]
        assert (
            "[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task"
            == kwargs["json"]["title"]
        )
        assert "[SELF-REPAIR-ANCHOR] task:task-fail" in kwargs["json"]["body"]
        assert daemon.metrics["self_heals_manifested"] == 1

    @pytest.mark.asyncio
    async def test_manifest_self_healing_falls_back_to_local_task_when_github_demoted(
        self, monkeypatch
    ) -> None:
        monkeypatch.setenv("KORTANA_GITHUB_MODE", "deferred")
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
        existing_result = MagicMock()
        existing_result.scalars.return_value.all.return_value = []
        session.execute.side_effect = [failed_result, active_result, existing_result]

        local_repair = GitHubTask(
            id="repair-1",
            github_issue_number=-1,
            github_repo="local/self-heal",
            title="[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task",
            description="desc",
            status="pending",
        )
        local_service = AsyncMock()
        local_service.manifest_self_repair = AsyncMock(return_value=local_repair)

        with (
            patch(
                "src.kortana.services.autonomy_daemon.LocalBacklogService",
                return_value=local_service,
            ),
            patch(
                "src.kortana.services.autonomy_daemon.httpx.AsyncClient"
            ) as mock_client,
        ):
            await daemon._manifest_self_healing(
                session, candidate_task_ids=[failed_task.id]
            )

        local_service.manifest_self_repair.assert_awaited_once()
        mock_client.assert_not_called()
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
            await daemon._manifest_self_healing(
                session, candidate_task_ids=[failed_task.id]
            )

        mock_client.assert_not_called()
        assert daemon.metrics["self_heals_manifested"] == 0

    @pytest.mark.asyncio
    async def test_manifest_self_healing_skips_without_current_cycle_failures(
        self,
    ) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        with patch(
            "src.kortana.services.autonomy_daemon.httpx.AsyncClient"
        ) as mock_client:
            await daemon._manifest_self_healing(session, candidate_task_ids=[])

        session.execute.assert_not_called()
        mock_client.assert_not_called()
        assert daemon.metrics["self_heals_manifested"] == 0

    @pytest.mark.asyncio
    async def test_manifest_self_healing_skips_when_repair_anchor_already_exists(
        self,
    ) -> None:
        daemon = build_daemon()
        failed_task = GitHubTask(
            id="task-fail",
            github_issue_number=1,
            github_repo="madouble7/kortana",
            title="Failed task",
            description="desc",
            error_message="Systematic logic failure",
            status="failed",
        )
        existing_repair = GitHubTask(
            id="task-repair",
            github_issue_number=3,
            github_repo="madouble7/kortana",
            title="[AUTO] [SELF-REPAIR] Resolve systemic failure in Failed task",
            description="[SELF-REPAIR-ANCHOR] task:task-fail",
            status="completed",
        )

        session = AsyncMock()
        failed_result = MagicMock()
        failed_result.scalar_one_or_none.return_value = failed_task
        active_result = MagicMock()
        active_result.scalars.return_value.all.return_value = []
        existing_result = MagicMock()
        existing_result.scalars.return_value.all.return_value = [existing_repair]
        session.execute.side_effect = [failed_result, active_result, existing_result]

        with patch(
            "src.kortana.services.autonomy_daemon.httpx.AsyncClient"
        ) as mock_client:
            await daemon._manifest_self_healing(
                session, candidate_task_ids=[failed_task.id]
            )

        mock_client.assert_not_called()
        assert daemon.metrics["self_heals_manifested"] == 0

    @pytest.mark.asyncio
    async def test_process_pending_approvals_handles_approve_comment(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-1",
            last_processed_github_comment_id=None,
        )
        mock_task = GitHubTask(
            id="task-1",
            github_repo="repo/test",
            github_issue_number=42,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])

        async def mock_process(
            task_id, body, reviewer, github_comment_id, github_comment_url, **kwargs
        ):
            if github_comment_id == "1001":
                return "approved"
            return None

        mock_approval_service.process_command_from_comment = AsyncMock(
            side_effect=mock_process
        )
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1001,
                    "html_url": "https://github.com/repo/test/issues/42#issuecomment-1001",
                    "body": "great work /approve this",
                    "user": {"login": "human", "type": "User"},
                },
                {
                    "id": 1002,
                    "html_url": "https://github.com/repo/test/issues/42#issuecomment-1002",
                    "body": "logging my final thought after approval",
                    "user": {"login": "human", "type": "User"},
                },
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.process_command_from_comment.assert_any_await(
            task_id="task-1",
            body="great work /approve this",
            reviewer="human",
            github_comment_id="1001",
            github_comment_url="https://github.com/repo/test/issues/42#issuecomment-1001",
        )
        mock_approval_service.mark_comment_seen.assert_awaited_once()
        mock_github_service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_handles_reject_comment(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-2",
            last_processed_github_comment_id=None,
        )
        mock_task = GitHubTask(
            id="task-2",
            github_repo="repo/test",
            github_issue_number=43,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])

        async def mock_process(
            task_id, body, reviewer, github_comment_id, github_comment_url, **kwargs
        ):
            if github_comment_id == "1002":
                return "rejected"
            return None

        mock_approval_service.process_command_from_comment = AsyncMock(
            side_effect=mock_process
        )
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1002,
                    "html_url": "https://github.com/repo/test/issues/43#issuecomment-1002",
                    "body": "no thanks /reject",
                    "user": {"login": "human", "type": "User"},
                }
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.process_command_from_comment.assert_any_await(
            task_id="task-2",
            body="no thanks /reject",
            reviewer="human",
            github_comment_id="1002",
            github_comment_url="https://github.com/repo/test/issues/43#issuecomment-1002",
        )
        mock_approval_service.mark_comment_seen.assert_awaited_once()
        mock_github_service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_ignores_bot_comments(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-3",
            last_processed_github_comment_id=None,
        )
        mock_task = GitHubTask(
            id="task-3",
            github_repo="repo/test",
            github_issue_number=44,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.process_command_from_comment = AsyncMock(
            return_value=None
        )
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1003,
                    "html_url": "https://github.com/repo/test/issues/44#issuecomment-1003",
                    "body": "/approve",
                    "user": {"login": "github-actions[bot]", "type": "Bot"},
                },
                {
                    "id": 1004,
                    "html_url": "https://github.com/repo/test/issues/44#issuecomment-1004",
                    "body": "/reject",
                    "user": {"login": "kortana", "type": "Bot"},
                },
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.approve_task.assert_not_called()
        mock_approval_service.mark_comment_seen.assert_awaited_once_with(
            "task-3",
            github_comment_id="1004",
            github_comment_url="https://github.com/repo/test/issues/44#issuecomment-1004",
        )

    @pytest.mark.asyncio
    async def test_process_pending_approvals_marks_irrelevant_comments_as_seen(
        self,
    ) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-4",
            last_processed_github_comment_id=None,
        )
        mock_task = GitHubTask(
            id="task-4",
            github_repo="repo/test",
            github_issue_number=45,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.process_command_from_comment = AsyncMock(
            return_value=None
        )
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1005,
                    "html_url": "https://github.com/repo/test/issues/45#issuecomment-1005",
                    "body": "This looks okay but needs more work",
                    "user": {"login": "human", "type": "User"},
                }
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.approve_task.assert_not_called()
        mock_approval_service.mark_comment_seen.assert_awaited_once_with(
            "task-4",
            github_comment_id="1005",
            github_comment_url="https://github.com/repo/test/issues/45#issuecomment-1005",
        )

    @pytest.mark.asyncio
    async def test_process_pending_approvals_ignores_already_processed_comments(
        self,
    ) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-5",
            last_processed_github_comment_id="1007",
        )
        mock_task = GitHubTask(
            id="task-5",
            github_repo="repo/test",
            github_issue_number=46,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.approve_task = AsyncMock()
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1006,
                    "html_url": "https://github.com/repo/test/issues/46#issuecomment-1006",
                    "body": "/approve",
                    "user": {"login": "human", "type": "User"},
                },
                {
                    "id": 1007,
                    "html_url": "https://github.com/repo/test/issues/46#issuecomment-1007",
                    "body": "latest seen",
                    "user": {"login": "human", "type": "User"},
                },
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.approve_task.assert_not_called()
        mock_approval_service.mark_comment_seen.assert_not_awaited()
        mock_github_service.post_issue_comment.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_skips_when_already_resolved(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()

        mock_approval = MagicMock(
            github_task_id="task-already-resolved",
            last_processed_github_comment_id=None,
        )
        mock_task = GitHubTask(
            id="task-already-resolved",
            github_repo="repo/test",
            github_issue_number=47,
        )

        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.process_command_from_comment = AsyncMock(
            return_value=None  # simulated value
        )
        mock_approval_service.mark_comment_seen = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(
            return_value=[
                {
                    "id": 1008,
                    "html_url": "https://github.com/repo/test/issues/47#issuecomment-1008",
                    "body": "/approve",
                    "user": {"login": "human", "type": "User"},
                }
            ]
        )
        mock_github_service.post_issue_comment = AsyncMock()

        with (
            patch(
                "src.kortana.services.task_approval_service.TaskApprovalService",
                return_value=mock_approval_service,
            ),
            patch(
                "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
                return_value=mock_github_service,
            ),
        ):
            await daemon._process_pending_approvals(session)

        mock_approval_service.process_command_from_comment.assert_any_await(
            task_id="task-already-resolved",
            body="/approve",
            reviewer="human",
            github_comment_id="1008",
            github_comment_url="https://github.com/repo/test/issues/47#issuecomment-1008",
        )
        mock_approval_service.mark_comment_seen.assert_awaited_once()
        mock_github_service.post_issue_comment.assert_not_awaited()


@pytest.mark.asyncio
async def test_daemon_crash_writes_to_incident_memory():
    daemon = build_daemon()
    from src.kortana.models import IncidentMemory

    mock_session = AsyncMock()
    # Provide a real add method memory list
    calls = []

    def mock_add(obj):
        calls.append(obj)

    mock_session.add.side_effect = mock_add

    # Create an async generator for get_session
    async def mock_get_session():
        yield mock_session

    daemon._db_manager.get_session = mock_get_session

    sleep_call_count = 0

    async def mock_sleep(*args, **kwargs):
        nonlocal sleep_call_count
        sleep_call_count += 1
        if sleep_call_count >= 2:
            daemon._running = False

    with patch(
        "src.kortana.services.autonomy_daemon.asyncio.sleep", side_effect=mock_sleep
    ):
        # We need a patch on self_regulate that raises Exception
        async def mock_regulate(*args, **kwargs):
            raise Exception("Fatal crash in daemon memory")

        with patch.object(daemon, "_self_regulate", side_effect=mock_regulate):
            daemon._running = True
            await daemon._loop()

    # Check if an IncidentMemory was added
    mock_session.add.assert_called()
    incident = mock_session.add.call_args[0][0]
    assert isinstance(incident, IncidentMemory)
    assert incident.incident_type == "daemon_crash"
    assert "Fatal crash in daemon memory" in incident.description


@pytest.mark.asyncio
@patch("src.kortana.services.autonomy_daemon.get_settings")
async def test_task_failure_writes_to_incident_memory(mock_settings):
    mock_sett = MagicMock()
    mock_sett.AUTONOMY_LOOP_SHADOW_ENABLED = False
    mock_sett.AUTONOMY_CYCLE_INTERVAL = 1
    mock_sett.AUTONOMY_MAX_TASKS = 1
    mock_settings.return_value = mock_sett

    daemon = build_daemon()
    from src.kortana.models import GitHubTask, IncidentMemory

    mock_session = AsyncMock()

    mock_task = GitHubTask(id="task_fail_1", title="test", status="planning_complete")

    class MockResult:
        def scalars(self):
            class MockScalars:
                def all(self):
                    return [mock_task]

            return MockScalars()

    mock_session.execute.return_value = MockResult()

    with patch(
        "src.kortana.services.autonomy_daemon.time.monotonic", return_value=100.0
    ):

        async def mock_execute(*args, **kwargs):
            raise RuntimeError("Task execution crashed")

        async def mock_plan(t, *args, **kwargs):
            t.status = "planning_complete"

        mock_service = AsyncMock()
        mock_service.plan_task = mock_plan
        mock_service.execute_task = mock_execute

        # We patch github_autonomy_service.GitHubAutonomyService which is used inside _process_tasks
        with patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=mock_service,
        ):
            with patch(
                "src.kortana.services.autonomy_daemon.TaskApprovalService"
            ) as mock_app_class:
                mock_app_service = AsyncMock()

                class MockApp:
                    approved = True
                    risk_level = "low"
                    requires_human = False
                    reasoning = "ok"
                    confidence = 1.0

                mock_app_service.evaluate_task.return_value = MockApp()
                mock_app_class.return_value = mock_app_service

                processed, succeeded, failed, deferred = await daemon._process_tasks(
                    mock_session, max_tasks=1
                )

                assert failed == 1

                # Check incident was written
                mock_session.add.assert_called()
                added_incidents = [
                    call.args[0]
                    for call in mock_session.add.call_args_list
                    if isinstance(call.args[0], IncidentMemory)
                ]
                assert len(added_incidents) > 0
                incident = added_incidents[0]
                assert incident.incident_type == "task_failure"
                assert "Task execution crashed" in incident.description


@pytest.mark.asyncio
async def test_heal_vectors_invokes_vector_alpha():
    from unittest.mock import AsyncMock, MagicMock, patch

    from src.kortana.models import IncidentMemory
    from src.kortana.services.autonomy_daemon import AutonomyDaemon

    incident = IncidentMemory(
        incident_type="daemon_crash",
        description="test failure",
        resolved=False,
        fix_status=None,
    )

    daemon = AutonomyDaemon()

    mock_session = AsyncMock()
    mock_execute = MagicMock()
    mock_execute.scalars.return_value.all.return_value = [incident]
    mock_session.execute.return_value = mock_execute

    with (
        patch(
            "src.kortana.services.vector_alpha_branch_service.VectorAlphaBranchService"
        ) as mock_alpha,
        patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService"),
        patch("src.kortana.services.patch_planner.PatchPlanner") as mock_planner,
    ):
        mock_alpha_inst = mock_alpha.return_value
        mock_alpha_inst.evaluate_incident.return_value = True
        mock_planner.return_value.apply_healing_patch = AsyncMock(return_value=True)
        mock_alpha_inst.create_healing_branch = AsyncMock(return_value="auto-fix/test")
        mock_alpha_inst.commit_and_propose = AsyncMock(return_value=True)

        await daemon._heal_vectors(mock_session)

        mock_alpha_inst.evaluate_incident.assert_called_once_with(incident)
        mock_alpha_inst.create_healing_branch.assert_called_once_with(incident)
        mock_alpha_inst.commit_and_propose.assert_called_once()
