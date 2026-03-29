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

        async def execute_task(task_to_execute: GitHubTask, dry_run: bool = False) -> None:
            task_to_execute.status = "executed"

        service = AsyncMock()
        service.analyze_task = AsyncMock(side_effect=analyze_task)
        service.plan_task = AsyncMock(side_effect=plan_task)
        service.execute_task = AsyncMock(side_effect=execute_task)

        # Mock settings to enable shadow loop
        mock_settings = MagicMock()
        mock_settings.AUTONOMY_LOOP_SHADOW_ENABLED = True

        with patch(
            "src.kortana.services.autonomy_daemon.get_settings",
            return_value=mock_settings,
        ), patch(
            "src.kortana.services.autonomy_daemon.AutonomyLoopBridgeService.run_dry_run",
            side_effect=Exception("Simulated catastrophic sandbox failure"),
        ), patch(
            "src.kortana.services.github_autonomy_service.GitHubAutonomyService",
            return_value=service,
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

        assert daemon.max_tasks == 1
        assert daemon.live_execution_enabled is False
        assert daemon.safe_mode is True
        assert daemon.control_mode == "operator_override_halt"
        assert daemon.operator_guidance["execution_mode"] == "plan"
        assert daemon.operator_guidance["approval_required"] is True

    def test_apply_operator_guidance_sets_auto_approval_execute_mode(self) -> None:
        daemon = build_daemon()
        daemon.default_approval_mode = "auto"

        daemon._apply_operator_guidance(DirectiveSummary(active_count=0))

        assert daemon.live_execution_enabled is True
        assert daemon.control_mode == "auto_approval_execute"

    def test_apply_operator_guidance_restores_live_execution_when_cleared(self) -> None:
        daemon = build_daemon()
        daemon.live_execution_enabled = False
        guidance = DirectiveSummary(active_count=0)

        daemon._apply_operator_guidance(guidance)

        expected_control = (
            "auto_approval_execute"
            if daemon.default_approval_mode == "auto"
            else "execute"
        )
        assert daemon.control_mode == expected_control
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
        
        mock_approval = MagicMock()
        mock_approval.github_task_id = "task-1"
        
        mock_task = GitHubTask(id="task-1", github_repo="repo/test", github_issue_number=42)
        
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.approve_task = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(return_value=[
            {"body": "great work /approve this", "user": {"login": "human", "type": "User"}}
        ])
        mock_github_service.post_issue_comment = AsyncMock()

        with patch("src.kortana.services.task_approval_service.TaskApprovalService", return_value=mock_approval_service),              patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService", return_value=mock_github_service):
            await daemon._process_pending_approvals(session)
            
        mock_approval_service.approve_task.assert_awaited_once_with(
            "task-1", approved=True, reviewer="human", notes="great work /approve this"
        )
        mock_github_service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_handles_reject_comment(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()
        
        mock_approval = MagicMock()
        mock_approval.github_task_id = "task-2"
        
        mock_task = GitHubTask(id="task-2", github_repo="repo/test", github_issue_number=43)
        
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.approve_task = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(return_value=[
            {"body": "no thanks /reject", "user": {"login": "human", "type": "User"}}
        ])
        mock_github_service.post_issue_comment = AsyncMock()

        with patch("src.kortana.services.task_approval_service.TaskApprovalService", return_value=mock_approval_service),              patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService", return_value=mock_github_service):
            await daemon._process_pending_approvals(session)
            
        mock_approval_service.approve_task.assert_awaited_once_with(
            "task-2", approved=False, reviewer="human", notes="no thanks /reject"
        )
        mock_github_service.post_issue_comment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_ignores_bot_comments(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()
        
        mock_approval = MagicMock()
        mock_approval.github_task_id = "task-3"
        
        mock_task = GitHubTask(id="task-3", github_repo="repo/test", github_issue_number=44)
        
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.approve_task = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(return_value=[
            {"body": "/approve", "user": {"login": "github-actions[bot]", "type": "Bot"}},
            {"body": "/reject", "user": {"login": "kortana", "type": "Bot"}}
        ])
        mock_github_service.post_issue_comment = AsyncMock()

        with patch("src.kortana.services.task_approval_service.TaskApprovalService", return_value=mock_approval_service),              patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService", return_value=mock_github_service):
            await daemon._process_pending_approvals(session)
            
        mock_approval_service.approve_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_ignores_irrelevant_comments(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()
        
        mock_approval = MagicMock()
        mock_approval.github_task_id = "task-4"
        
        mock_task = GitHubTask(id="task-4", github_repo="repo/test", github_issue_number=45)
        
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        mock_approval_service.approve_task = AsyncMock()

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(return_value=[
            {"body": "This looks okay but needs more work", "user": {"login": "human", "type": "User"}}
        ])
        mock_github_service.post_issue_comment = AsyncMock()

        with patch("src.kortana.services.task_approval_service.TaskApprovalService", return_value=mock_approval_service),              patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService", return_value=mock_github_service):
            await daemon._process_pending_approvals(session)
            
        mock_approval_service.approve_task.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_pending_approvals_skips_when_already_resolved(self) -> None:
        daemon = build_daemon()
        session = AsyncMock()
        
        mock_approval = MagicMock()
        mock_approval.github_task_id = "task-already-resolved"
        
        mock_task = GitHubTask(id="task-already-resolved", github_repo="repo/test", github_issue_number=46)
        
        result = MagicMock()
        result.scalars.return_value.all.return_value = [mock_task]
        session.execute = AsyncMock(return_value=result)

        mock_approval_service = AsyncMock()
        mock_approval_service.list_pending = AsyncMock(return_value=[mock_approval])
        # Simulate that approve_task raises ValueError because it is already resolved
        mock_approval_service.approve_task = AsyncMock(side_effect=ValueError("Task approval already resolved"))

        mock_github_service = AsyncMock()
        mock_github_service.fetch_issue_comments = AsyncMock(return_value=[
            {"body": "/approve", "user": {"login": "human", "type": "User"}}
        ])
        mock_github_service.post_issue_comment = AsyncMock()

        with patch("src.kortana.services.task_approval_service.TaskApprovalService", return_value=mock_approval_service),              patch("src.kortana.services.github_autonomy_service.GitHubAutonomyService", return_value=mock_github_service):
            await daemon._process_pending_approvals(session)
            
        mock_approval_service.approve_task.assert_awaited_once_with(
            "task-already-resolved", approved=True, reviewer="human", notes="/approve"
        )
        # Verify that post_issue_comment is NOT called because of the skip
        mock_github_service.post_issue_comment.assert_not_called()
