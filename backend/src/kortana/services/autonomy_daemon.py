"""
Self-sustaining autonomy daemon.

Runs inside the FastAPI event loop and continuously:
  1. Discovers GitHub issues
  2. Moves tasks through analyze -> plan -> execute
  3. Self-regulates based on runtime health
  4. Accepts operator directives to change course without stopping the daemon
  5. Manifests self-repair work when core autonomy fails
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from src.kortana.services.task_approval_service import ApprovalDecision

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.config import get_settings
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.autonomy_loop_bridge_service import AutonomyLoopBridgeService
from src.kortana.services.local_backlog_service import LocalBacklogService
from src.kortana.services.operator_directive_service import (
    DirectiveSummary,
    get_active_operator_summary,
)
from src.kortana.services.self_awareness import get_self_awareness
from src.kortana.services.task_approval_service import TaskApprovalService
from src.kortana.services.workspace_bridge_service import get_workspace_bridge

logger = get_logger(__name__)


@dataclass
class DaemonEvent:
    type: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: dict[str, Any] = field(default_factory=dict)


EventCallback = Callable[[DaemonEvent], Any]


class AutonomyDaemon:
    """Always-on autonomous loop for GitHub-driven development work."""

    def __init__(self) -> None:
        settings = get_settings()
        self.enabled = os.getenv("AUTONOMY_DAEMON_ENABLED", "true").lower() == "true"
        self.base_cycle_interval = int(
            os.getenv("AUTONOMY_CYCLE_INTERVAL", str(settings.AUTONOMY_CYCLE_INTERVAL))
        )
        self.base_max_tasks = int(os.getenv("AUTONOMY_MAX_TASKS_PER_CYCLE", "3"))
        self.cycle_interval = self.base_cycle_interval
        self.max_tasks = self.base_max_tasks
        self.repo = (
            f"{os.getenv('GITHUB_OWNER') or settings.GITHUB_OWNER}/"
            f"{os.getenv('GITHUB_REPO') or settings.GITHUB_REPO}"
        )
        self.safe_mode = False
        self.live_execution_enabled = True
        self.control_mode = "execute"
        default_approval_mode = (
            (os.getenv("KORTANA_DEFAULT_APPROVAL_MODE") or "").strip().lower()
        )
        if default_approval_mode in {"auto", "manual", "self-aware"}:
            self.default_approval_mode: str | None = default_approval_mode
        elif os.getenv("KORTANA_SELF_AWARE_APPROVAL", "false").lower() == "true":
            self.default_approval_mode = "self-aware"
        else:
            self.default_approval_mode = None
        self.operator_guidance: dict[str, Any] | None = None
        self._adaptation_history: list[dict[str, Any]] = []
        self._deferred_tasks: set[str] = set()
        self._cycle_failed_task_ids: list[str] = []

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._listeners: list[EventCallback] = []
        self._db_manager = get_db_manager()
        self._workspace_bridge = get_workspace_bridge()

        self.metrics: dict[str, Any] = {
            "cycles_completed": 0,
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "tasks_deferred": 0,
            "self_heals_manifested": 0,
            "adaptive_adjustments": 0,
            "safe_mode_cycles": 0,
            "approvals_auto_granted": 0,
            "approvals_held": 0,
            "system_state": "nominal",
            "last_cycle": None,
            "last_assessment": None,
            "last_self_regulation": None,
            "operator_guidance": None,
            "workspace_bridge": None,
            "uptime_start": None,
            "errors": [],
        }

    def _github_mode(self) -> str:
        mode = (
            (os.getenv("KORTANA_GITHUB_MODE") or get_settings().KORTANA_GITHUB_MODE)
            .strip()
            .lower()
        )
        if mode in {"full", "deferred", "disabled"}:
            return mode
        return "full"

    async def start(self) -> None:
        if not self.enabled:
            logger.info("Autonomy daemon disabled via AUTONOMY_DAEMON_ENABLED")
            return
        if self._running:
            logger.warning("Autonomy daemon already running")
            return

        self._running = True
        self.metrics["uptime_start"] = datetime.utcnow().isoformat()
        logger.info(
            "Autonomy daemon started "
            f"(interval={self.cycle_interval}s, max_tasks={self.max_tasks})"
        )
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Autonomy daemon stopped")

    def on_event(self, callback: EventCallback) -> None:
        self._listeners.append(callback)

    def _emit(self, event: DaemonEvent) -> None:
        for callback in self._listeners:
            try:
                result = callback(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass

    async def _loop(self) -> None:
        await asyncio.sleep(5)
        while self._running:
            try:
                await self._run_cycle()
            except Exception as exc:
                logger.error(f"Daemon cycle error: {exc}")
                self.metrics["errors"].append(
                    {"time": datetime.utcnow().isoformat(), "error": str(exc)}
                )
                self.metrics["errors"] = self.metrics["errors"][-20:]

                # Write to IncidentMemory
                try:
                    from src.kortana.models import IncidentMemory

                    async for session in self._db_manager.get_session():
                        incident = IncidentMemory(
                            incident_type="daemon_crash",
                            description=str(exc),
                            stack_trace="omitted_for_brevity",
                            resolution_strategy="auto_restart",
                            resolved=False,
                        )
                        session.add(incident)
                        await session.commit()
                except Exception as log_exc:
                    logger.error(
                        f"Failed to write daemon crash to IncidentMemory: {log_exc}"
                    )

            await asyncio.sleep(self.cycle_interval)

    async def _heal_vectors(self, session: Any) -> None:
        """Vector Alpha Branch-Scoped Self Healing"""
        from sqlalchemy import select

        from src.kortana.models import IncidentMemory
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService
        from src.kortana.services.vector_alpha_branch_service import (
            VectorAlphaBranchService,
        )

        try:
            res = await session.execute(
                select(IncidentMemory).where(
                    IncidentMemory.resolved.is_(False),
                    IncidentMemory.fix_status.is_(None),
                )
            )
            incidents = res.scalars().all()

            for inc in incidents:
                alpha = VectorAlphaBranchService(session)
                if alpha.evaluate_incident(inc):
                    logger.info(
                        f"[Vector Alpha] Attempting to heal {inc.incident_type}"
                    )
                    branch = await alpha.create_healing_branch(inc)
                    if branch:
                        from src.kortana.services.patch_planner import PatchPlanner

                        planner = PatchPlanner(alpha.worktree_dir)
                        patch_success = await planner.apply_healing_patch(inc)

                        # Persist any evidence / resolution_strategy updates from the planner
                        session.add(inc)
                        await session.commit()

                        if patch_success:
                            alpha_dry_run = (
                                get_settings().VECTOR_ALPHA_DRY_RUN
                                or not self.live_execution_enabled
                            )
                            gh = GitHubAutonomyService(session)
                            success = await alpha.commit_and_propose(
                                inc, gh, dry_run=alpha_dry_run
                            )
                            if success:
                                if alpha_dry_run:
                                    logger.info(
                                        f"[Vector Alpha] Dry run completed for {inc.id}"
                                    )
                                else:
                                    logger.info(
                                        f"[Vector Alpha] Created PR for {inc.id}"
                                    )
                        else:
                            # Clean up the worktree correctly if we abort
                            import asyncio
                            import subprocess

                            await asyncio.to_thread(
                                subprocess.run,
                                [
                                    "git",
                                    "worktree",
                                    "remove",
                                    "--force",
                                    alpha.worktree_dir,
                                ],
                                cwd=alpha.repo_dir,
                                check=False,
                            )
        except Exception as e:
            logger.error(f"Vector Alpha execution failed: {e}")

    async def _analyze_architecture(self, session: Any) -> None:
        try:
            from sqlalchemy import func

            from src.kortana.models import ArchitectureMemory

            # Run only periodically, like once every 100 cycles, or if none exists
            count_res = await session.execute(
                select(func.count()).select_from(ArchitectureMemory)
            )
            count = count_res.scalar_one_or_none() or 0

            if self.metrics["cycles_completed"] % 100 == 0 or count == 0:
                logger.info("Running architectural analysis...")
                # In the future this calls an LLM summary of the repo structure.
                # For now, we populate a baseline self-awareness structural model.
                snapshot = {
                    "modules": [
                        "autonomy_daemon",
                        "fastapi_routers",
                        "celery_workers",
                        "github_webhook_bridge",
                    ],
                    "coupling": "moderate",
                    "observation": "Vector Gamma persistent memory active. Hopkins HOP boundary maintained.",
                }

                new_arch = ArchitectureMemory(
                    component_name="backend_engine",
                    description=snapshot.get("observation", "Architecture snapshot"),
                    knowledge_factors=snapshot,
                    confidence_score=0.95,
                )
                session.add(new_arch)
                await session.commit()

        except Exception as exc:
            logger.debug(f"Architecture analysis skip: {exc}")

    async def _run_cycle(self) -> None:
        cycle_start = time.monotonic()
        cycle_start_dt = datetime.utcnow()
        self._emit(DaemonEvent(type="cycle_start"))
        logger.info("--- Autonomy cycle starting ---")

        await self._self_regulate()
        guidance = await self._load_operator_guidance()
        self._apply_operator_guidance(guidance)
        workspace_status = await self._poll_workspace_bridge()
        self._cycle_failed_task_ids = []

        new_count = (
            processed
        ) = succeeded = failed = deferred = approvals_processed_count = 0
        async for session in self._db_manager.get_session():
            new_count = await self._discover_tasks(
                session,
                guidance=guidance,
                workspace_status=workspace_status,
            )
            effective_limit = (
                0
                if guidance.pause_requested
                or guidance.execution_mode == "observe"
                or guidance.override_mode == "halt"
                else self.max_tasks
            )
            processed, succeeded, failed, deferred = await self._process_tasks(
                session, max_tasks=effective_limit, guidance=guidance
            )
            app_count = await self._process_pending_approvals(session)
            approvals_processed_count += app_count
            await self._analyze_architecture(session)
            await self._heal_vectors(session)

        try:
            from dataclasses import asdict

            from src.kortana.services.adaptive_learner import get_adaptive_learner
            from src.kortana.services.goal_manager import get_goal_manager

            goal_manager = get_goal_manager()
            learner = await get_adaptive_learner()
            insights = [asdict(item) for item in learner.generate_insights()]
            goal_manager.reprioritise(
                system_state=str(self.metrics["system_state"]),
                insights=insights,
            )
            self.metrics["goal_status"] = goal_manager.get_status()
        except Exception as exc:
            logger.debug(f"Goal reprioritisation unavailable: {exc}")

        elapsed = round(time.monotonic() - cycle_start, 2)
        if self.safe_mode:
            self.metrics["safe_mode_cycles"] += 1

        self.metrics["cycles_completed"] += 1
        self.metrics["tasks_processed"] += processed
        self.metrics["tasks_succeeded"] += succeeded
        self.metrics["tasks_failed"] += failed
        self.metrics["tasks_deferred"] += deferred
        self.metrics["last_cycle"] = {
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": elapsed,
            "new_issues": new_count,
            "new_tasks": new_count,
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
            "deferred": deferred,
            "system_state": self.metrics["system_state"],
            "safe_mode": self.safe_mode,
            "live_execution_enabled": self.live_execution_enabled,
            "control_mode": self.control_mode,
            "operator_guidance": self.metrics["operator_guidance"],
            "workspace_bridge": workspace_status,
        }

        # Record Vector Gamma cycle memory
        try:
            from src.kortana.models import AutonomyCycleMemory

            async for session in self._db_manager.get_session():
                cycle_mem = AutonomyCycleMemory(
                    cycle_id=f"cycle_{int(time.time() * 1000)}",
                    start_time=cycle_start_dt,
                    end_time=datetime.utcnow(),
                    tasks_processed=processed,
                    approvals_processed=approvals_processed_count,
                    errors_encountered=failed,
                    metrics=self.metrics["last_cycle"],
                )
                session.add(cycle_mem)
                await session.commit()
        except Exception as e:
            logger.warning(f"Could not persist cycle memory: {e}")

        self._emit(DaemonEvent(type="cycle_end", data=self.metrics["last_cycle"]))

        logger.info(
            "--- Autonomy cycle complete "
            f"({elapsed}s, processed={processed}, succeeded={succeeded}, "
            f"deferred={deferred}, state={self.metrics['system_state']}) ---"
        )

    async def _self_regulate(self) -> None:
        """Apply runtime tuning from self-awareness."""
        try:
            decision = await get_self_awareness().regulate(
                base_cycle_interval=self.base_cycle_interval,
                base_max_tasks=self.base_max_tasks,
            )
        except Exception as exc:
            logger.warning(f"Self-regulation unavailable: {exc}")
            return

        profile = decision["runtime_profile"]
        assessment = decision["assessment"]
        previous = {
            "cycle_interval_seconds": self.cycle_interval,
            "max_tasks_per_cycle": self.max_tasks,
            "safe_mode": self.safe_mode,
            "live_execution_enabled": self.live_execution_enabled,
        }

        self.cycle_interval = int(profile["cycle_interval_seconds"])
        self.max_tasks = int(profile["max_tasks_per_cycle"])
        self.safe_mode = bool(profile["safe_mode"])
        self.live_execution_enabled = bool(profile["allow_live_execution"])
        self.metrics["system_state"] = profile["state"]
        self.metrics["last_assessment"] = assessment
        self.metrics["last_self_regulation"] = profile

        current = {
            "cycle_interval_seconds": self.cycle_interval,
            "max_tasks_per_cycle": self.max_tasks,
            "safe_mode": self.safe_mode,
            "live_execution_enabled": self.live_execution_enabled,
        }
        if current != previous:
            event = {
                "timestamp": datetime.utcnow().isoformat(),
                "state": profile["state"],
                "execution_confidence": profile["execution_confidence"],
                "reasons": profile["reasons"],
                "previous": previous,
                "current": current,
            }
            self.metrics["adaptive_adjustments"] += 1
            self._adaptation_history.append(event)
            self._adaptation_history = self._adaptation_history[-25:]
            self._emit(DaemonEvent(type="self_regulation", data=event))

    async def _load_operator_guidance(self) -> DirectiveSummary:
        try:
            return await get_active_operator_summary()
        except Exception as exc:
            logger.warning(f"Operator guidance unavailable: {exc}")
            return DirectiveSummary()

    async def _poll_workspace_bridge(self) -> dict[str, Any]:
        try:
            status = await self._workspace_bridge.poll()
            self.metrics["workspace_bridge"] = status
            return status
        except Exception as exc:
            logger.warning(f"Workspace bridge unavailable: {exc}")
            return self.metrics.get("workspace_bridge") or {}

    def _apply_operator_guidance(self, guidance: DirectiveSummary) -> None:
        default_live_execution = not self.safe_mode
        approval_mode = guidance.approval_mode or self.default_approval_mode
        self.operator_guidance = {
            "protocol_version": guidance.protocol_version,
            "active_count": guidance.active_count,
            "pause_requested": guidance.pause_requested,
            "focus_topics": guidance.focus_topics,
            "avoid_topics": guidance.avoid_topics,
            "max_tasks_override": guidance.max_tasks_override,
            "execution_mode": guidance.execution_mode,
            "approval_mode": approval_mode,
            "approval_required": guidance.approval_required,
            "handoff_rules": guidance.handoff_rules,
            "override_mode": guidance.override_mode,
        }
        self.metrics["operator_guidance"] = self.operator_guidance

        if guidance.max_tasks_override is not None:
            self.max_tasks = max(1, min(self.max_tasks, guidance.max_tasks_override))

        if guidance.override_mode == "halt":
            self.safe_mode = True
            self.live_execution_enabled = False
            self.control_mode = "operator_override_halt"
        elif guidance.pause_requested:
            self.safe_mode = True
            self.live_execution_enabled = False
            self.control_mode = "paused_by_operator"
        elif guidance.execution_mode == "observe":
            self.safe_mode = True
            self.live_execution_enabled = False
            self.control_mode = "observe_only"
        elif guidance.execution_mode == "plan":
            self.live_execution_enabled = False
            self.control_mode = "plan_only"
        elif guidance.approval_required:
            self.live_execution_enabled = False
            self.control_mode = "approval_required"
        elif approval_mode == "auto":
            self.live_execution_enabled = default_live_execution
            self.control_mode = (
                "auto_approval_execute"
                if self.live_execution_enabled
                else "auto_approval_observe"
            )
        elif approval_mode == "self-aware":
            self.live_execution_enabled = default_live_execution
            self.control_mode = (
                "self_approval_execute"
                if self.live_execution_enabled
                else "self_approval_observe"
            )
        elif guidance.override_mode == "execute" and not self.safe_mode:
            self.live_execution_enabled = True
            self.control_mode = "operator_override_execute"
        elif guidance.handoff_rules or guidance.focus_topics or guidance.avoid_topics:
            self.live_execution_enabled = default_live_execution
            self.control_mode = (
                "guided_execute" if self.live_execution_enabled else "guided_observe"
            )
        else:
            self.live_execution_enabled = default_live_execution
            self.control_mode = "safe_mode" if self.safe_mode else "execute"

    async def _discover_tasks(
        self,
        session: AsyncSession,
        *,
        guidance: DirectiveSummary,
        workspace_status: dict[str, Any] | None,
    ) -> int:
        discovered = 0
        try:
            local_service = LocalBacklogService(session)
            local_tasks = await local_service.discover_workspace_tasks(
                workspace_status=workspace_status,
                guidance=guidance,
            )
            discovered += len(local_tasks)
        except Exception as exc:
            logger.error(f"Local task discovery failed: {exc}")

        if self._github_mode() != "full":
            return discovered

        try:
            from src.kortana.services.github_autonomy_service import (
                GitHubAutonomyService,
            )

            service = GitHubAutonomyService(session)
            tasks = await service.fetch_and_queue_issues()
            discovered += len(tasks) if tasks else 0
        except Exception as exc:
            logger.error(f"Issue discovery failed: {exc}")
        return discovered

    @staticmethod
    def _github_comment_id(comment: dict[str, Any]) -> str | None:
        raw_id = comment.get("id")
        if raw_id in (None, ""):
            raw_id = comment.get("node_id")
        if raw_id in (None, ""):
            return None
        return str(raw_id)

    @staticmethod
    def _github_comment_url(comment: dict[str, Any]) -> str | None:
        raw_url = comment.get("html_url") or comment.get("url")
        if raw_url in (None, ""):
            return None
        return str(raw_url)

    def _comments_after_high_water_mark(
        self,
        comments: list[dict[str, Any]],
        last_processed_comment_id: str | None,
    ) -> list[dict[str, Any]]:
        if not last_processed_comment_id:
            return comments

        for index, comment in enumerate(comments):
            if self._github_comment_id(comment) == last_processed_comment_id:
                return comments[index + 1 :]

        try:
            last_processed_numeric = int(last_processed_comment_id)
        except (TypeError, ValueError):
            return comments

        filtered: list[dict[str, Any]] = []
        for comment in comments:
            comment_id = self._github_comment_id(comment)
            if comment_id is None:
                continue
            try:
                if int(comment_id) > last_processed_numeric:
                    filtered.append(comment)
            except (TypeError, ValueError):
                continue
        return filtered

    async def _process_pending_approvals(self, session: AsyncSession) -> int:
        """Poll GitHub comments for tasks awaiting operator approval."""
        from sqlalchemy import select

        from src.kortana.services.github_autonomy_service import GitHubAutonomyService
        from src.kortana.services.task_approval_service import TaskApprovalService

        approval_service = TaskApprovalService(session)
        github_service = GitHubAutonomyService(session)
        processed_count = 0

        # Check a reasonable window of pending approvals
        pending_approvals = await approval_service.list_pending(limit=20)
        task_ids = [str(a.github_task_id) for a in pending_approvals]
        if not task_ids:
            return processed_count

        stmt = select(GitHubTask).where(GitHubTask.id.in_(task_ids))
        result = await session.execute(stmt)
        tasks = {str(t.id): t for t in result.scalars().all()}

        for approval in pending_approvals:
            task = tasks.get(str(approval.github_task_id))
            if not task or not task.github_repo or task.github_issue_number < 1:
                continue

            comments = await github_service.fetch_issue_comments(task)
            if not comments:
                continue

            unseen_comments = self._comments_after_high_water_mark(
                comments,
                getattr(approval, "last_processed_github_comment_id", None),
            )
            if not unseen_comments:
                continue

            latest_seen_comment = unseen_comments[-1]
            latest_seen_comment_id = self._github_comment_id(latest_seen_comment)
            latest_seen_comment_url = self._github_comment_url(latest_seen_comment)
            handled_command = False

            # Process newest comments first to find the latest explicit command
            for comment in reversed(unseen_comments):
                body_raw = (comment.get("body") or "").strip()
                user = comment.get("user", {}).get("login", "operator")
                command_comment_id = self._github_comment_id(comment)
                command_comment_url = self._github_comment_url(comment)

                action = await approval_service.process_command_from_comment(
                    task_id=str(task.id),
                    body=body_raw,
                    reviewer=user,
                    github_comment_id=command_comment_id or "",
                    github_comment_url=command_comment_url,
                )

                if action == "approved":
                    logger.info(f"Task {task.id} approved via GitHub comment by {user}")
                    await github_service.post_issue_comment(
                        task,
                        f"✅ @{user} Phase 4 explicit approval confirmed. Resuming autonomous execution.",
                    )
                    # Advance high water mark to the latest seen
                    await approval_service.mark_comment_seen(
                        str(task.id),
                        github_comment_id=latest_seen_comment_id or "",
                        github_comment_url=latest_seen_comment_url,
                    )
                    handled_command = True
                    processed_count += 1
                    break
                elif action == "rejected":
                    logger.info(f"Task {task.id} rejected via GitHub comment by {user}")
                    await github_service.post_issue_comment(
                        task,
                        f"❌ @{user} Phase 4 explicit rejection confirmed. Halting context map and dropping task.",
                    )
                    await approval_service.mark_comment_seen(
                        str(task.id),
                        github_comment_id=latest_seen_comment_id or "",
                        github_comment_url=latest_seen_comment_url,
                    )
                    handled_command = True
                    processed_count += 1
                    break

            if not handled_command and latest_seen_comment_id:
                await approval_service.mark_comment_seen(
                    str(task.id),
                    github_comment_id=latest_seen_comment_id or "",
                    github_comment_url=latest_seen_comment_url,
                )

        return processed_count

    async def _manifest_self_healing(
        self,
        session: AsyncSession,
        candidate_task_ids: list[str] | None = None,
    ) -> None:
        """Create one recursive self-repair issue when core autonomy fails."""
        try:
            candidate_ids = [
                task_id
                for task_id in (candidate_task_ids or self._cycle_failed_task_ids)
                if task_id
            ]
            if not candidate_ids:
                return

            stmt_failed = (
                select(GitHubTask)
                .where(
                    GitHubTask.id.in_(candidate_ids),
                    GitHubTask.status == "failed",
                    GitHubTask.error_message.is_not(None),
                )
                .order_by(GitHubTask.updated_at.desc(), GitHubTask.created_at.desc())
                .limit(1)
            )
            latest_failed = (await session.execute(stmt_failed)).scalar_one_or_none()
            if latest_failed is None:
                return

            title = (
                "[AUTO] [SELF-REPAIR] Resolve systemic failure in "
                f"{latest_failed.title}"
            )
            repair_anchor = f"[SELF-REPAIR-ANCHOR] task:{latest_failed.id}"
            stmt_active = select(GitHubTask).where(
                GitHubTask.title == title,
                GitHubTask.status.in_(
                    [
                        "pending",
                        "analyzed",
                        "planning",
                        "planning_complete",
                        "executing",
                    ]
                ),
            )
            active_repairs = (await session.execute(stmt_active)).scalars().all()
            if active_repairs:
                return

            stmt_existing = select(GitHubTask).where(
                GitHubTask.title == title,
                GitHubTask.description.contains(repair_anchor),
            )
            existing_repairs = (await session.execute(stmt_existing)).scalars().all()
            if existing_repairs:
                return

            local_backlog = LocalBacklogService(session)
            if self._github_mode() != "full":
                created = await local_backlog.manifest_self_repair(
                    failed_task=latest_failed,
                    repair_anchor=repair_anchor,
                )
                if created is not None:
                    self.metrics["self_heals_manifested"] += 1
                return

            settings = get_settings()
            github_token = os.getenv("GITHUB_TOKEN") or settings.GITHUB_TOKEN
            if not github_token:
                created = await local_backlog.manifest_self_repair(
                    failed_task=latest_failed,
                    repair_anchor=repair_anchor,
                )
                if created is not None:
                    self.metrics["self_heals_manifested"] += 1
                else:
                    logger.error("Cannot manifest self-repair: GitHub token missing")
                return

            owner = os.getenv("GITHUB_OWNER") or settings.GITHUB_OWNER
            repo = os.getenv("GITHUB_REPO") or settings.GITHUB_REPO
            payload = {
                "title": title,
                "body": (
                    "**KOR'TANA PRIME PROTOCOL ACTIVATED.**\n\n"
                    f"The autonomy subsystem encountered a failure while attempting "
                    f"Task #{latest_failed.github_issue_number}.\n\n"
                    f"{repair_anchor}\n\n"
                    f"### Error Diagnostic\n```\n{latest_failed.error_message}\n```\n\n"
                    "Directive: audit the autonomy path, trace the failing service, "
                    "and create a structural patch that prevents recurrence."
                ),
            }
            headers = {
                "Authorization": f"token {github_token}",
                "Accept": "application/vnd.github.v3+json",
            }

            async with httpx.AsyncClient(timeout=15) as client:
                response = await client.post(
                    f"https://api.github.com/repos/{owner}/{repo}/issues",
                    json=payload,
                    headers=headers,
                )
            if response.status_code == 201:
                self.metrics["self_heals_manifested"] += 1
                logger.info("Manifested self-repair issue successfully")
            else:
                logger.error(
                    "Failed to manifest self-healing issue: "
                    f"status={response.status_code} body={response.text}"
                )
                created = await local_backlog.manifest_self_repair(
                    failed_task=latest_failed,
                    repair_anchor=repair_anchor,
                )
                if created is not None:
                    self.metrics["self_heals_manifested"] += 1
        except Exception as exc:
            logger.exception(f"Self-repair manifestation failed: {exc}")
            try:
                if (
                    "local_backlog" in locals()
                    and "latest_failed" in locals()
                    and latest_failed is not None
                ):
                    created = await local_backlog.manifest_self_repair(
                        failed_task=latest_failed,
                        repair_anchor=repair_anchor,
                    )
                    if created is not None:
                        self.metrics["self_heals_manifested"] += 1
            except Exception as fallback_exc:
                logger.error(
                    "Local self-repair fallback failed after manifestation error: "
                    f"{fallback_exc}"
                )

    async def _process_tasks(
        self,
        session: AsyncSession,
        max_tasks: int | None = None,
        guidance: DirectiveSummary | None = None,
    ) -> tuple[int, int, int, int]:
        """Drive tasks through analyze -> plan -> execute."""
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        limit = self.max_tasks if max_tasks is None else max_tasks
        if limit <= 0:
            return 0, 0, 0, 0

        stmt = (
            select(GitHubTask)
            .where(
                GitHubTask.status.in_(
                    ["queued", "pending", "analyzed", "planning_complete"]
                )
            )
            .order_by(GitHubTask.created_at)
            .limit(max(limit * 3, limit))
        )
        result = await session.execute(stmt)
        candidates = list(result.scalars().all())
        tasks = self._prioritize_tasks(candidates, guidance, limit)
        if not tasks:
            return 0, 0, 0, 0

        service = GitHubAutonomyService(session)
        approval_service = TaskApprovalService(session)
        processed = succeeded = failed = deferred = 0

        for task in tasks:
            processed += 1
            task_started = time.monotonic()
            self._emit(
                DaemonEvent(
                    type="task_progress",
                    data={
                        "task_id": str(task.id),
                        "title": task.title,
                        "step": task.status,
                    },
                )
            )

            try:
                # Shadow Path Execution (Diagnostic Signal Only)
                if get_settings().AUTONOMY_LOOP_SHADOW_ENABLED:
                    try:
                        # Only run shadow path for queued/pending/analyzed tasks so it pre-empts execution side-effects
                        if task.status in {"queued", "pending", "analyzed"}:
                            task_payload = {
                                "id": str(task.id),
                                "description": task.title
                                + "\n"
                                + (task.description or ""),
                                "priority": "normal",
                                "status": "new",
                                "created_at": str(task.created_at),
                            }
                            # Offload to a thread to avoid blocking the daemon's event loop
                            shadow_result = await asyncio.to_thread(
                                AutonomyLoopBridgeService.run_dry_run, task_payload
                            )
                            # Imbue the result with interpreted advisory logic
                            try:
                                if isinstance(shadow_result, dict):
                                    shadow_result[
                                        "advisory"
                                    ] = self._derive_shadow_advisory(shadow_result)
                            except Exception as e:
                                logger.warning(
                                    f"Failed to derive shadow advisory for {task.id}: {e}"
                                )

                            # Persist this as a diagnostic artifact
                            task.sandbox_result = shadow_result  # type: ignore[assignment]

                            self._emit(
                                DaemonEvent(
                                    type="shadow_loop_result",
                                    data={
                                        "task_id": str(task.id),
                                        "status": shadow_result.get("status"),
                                        "ok": shadow_result.get("ok"),
                                        "error": shadow_result.get("error"),
                                    },
                                )
                            )
                            logger.info(
                                f"[AUDIT] Task {task.id} shadow loop signal captured. Result ok: {shadow_result.get('ok')}"
                            )
                    except Exception as e:
                        logger.warning(
                            f"Shadow loop execution failed for {task.id}, continuing live loop. Error: {e}"
                        )

                if task.status in {"queued", "pending"}:
                    await service.analyze_task(task)
                    if task.status != "analyzed":
                        raise RuntimeError(
                            task.error_message
                            or "Task analysis did not complete successfully"
                        )
                if task.status == "analyzed":
                    await service.plan_task(task)
                    if task.status != "planning_complete":
                        raise RuntimeError(
                            task.error_message
                            or "Task planning did not complete successfully"
                        )
                if task.status == "planning_complete":
                    approval_decision = await approval_service.evaluate_task(
                        task,
                        approval_mode=(
                            guidance.approval_mode
                            if guidance and guidance.approval_mode
                            else self.default_approval_mode
                        ),
                        system_state=str(self.metrics["system_state"]),
                        runtime_profile=self.metrics.get("last_self_regulation"),
                        workspace_status=self.metrics.get("workspace_bridge"),
                    )
                    if approval_decision is not None:
                        if approval_decision.approved:
                            await approval_service.record_decision(
                                task, approval_decision
                            )
                            self.metrics["approvals_auto_granted"] += 1
                            self._emit(
                                DaemonEvent(
                                    type="approval_auto_granted",
                                    data={
                                        "task_id": str(task.id),
                                        "title": task.title,
                                        "risk_level": approval_decision.risk_level,
                                        "confidence": approval_decision.confidence,
                                    },
                                )
                            )
                        else:
                            # [Phase 3] Externalize Shadow Advisory to GitHub
                            comment_body = self._format_approval_hold_comment(
                                task, approval_decision
                            )

                            try:
                                success = await service.post_issue_comment(
                                    task, comment_body
                                )
                            except Exception as e:
                                logger.error(
                                    f"Error posting approval hold comment for {task.id}: {e}"
                                )
                                success = False

                            if not success:
                                logger.warning(
                                    f"Failed to post approval hold comment for {task.id}. Skipping state transition to retry."
                                )
                                # State remains 'planning_complete' since we didn't call record_decision
                                self._emit(
                                    DaemonEvent(
                                        type="github_comment_failed",
                                        data={"task_id": str(task.id)},
                                    )
                                )
                                continue

                            # On successful comment, actually persist the workflow state
                            await approval_service.record_decision(
                                task, approval_decision
                            )

                            deferred += 1
                            self.metrics["approvals_held"] += 1
                            self._defer_execution(
                                task,
                                reason=approval_decision.reason_code,
                            )
                            continue

                    if self.live_execution_enabled:
                        await service.execute_task(task, dry_run=False)
                        if task.status != "executed":
                            raise RuntimeError(
                                task.error_message
                                or "Task execution did not complete successfully"
                            )
                        self._deferred_tasks.discard(str(task.id))
                    else:
                        deferred += 1
                        self._defer_execution(
                            task,
                            reason=self._defer_reason(guidance),
                        )
                        continue

                succeeded += 1
                await self._record_outcome(
                    task=task,
                    success=True,
                    latency_seconds=time.monotonic() - task_started,
                    error=None,
                )
                self._emit(
                    DaemonEvent(
                        type="task_complete",
                        data={
                            "task_id": str(task.id),
                            "title": task.title,
                            "status": task.status,
                        },
                    )
                )
            except Exception as exc:
                failed += 1
                task_id = str(task.id)
                if (
                    task.status == "failed"
                    and task_id not in self._cycle_failed_task_ids
                ):
                    self._cycle_failed_task_ids.append(task_id)
                await self._record_outcome(
                    task=task,
                    success=False,
                    latency_seconds=round(time.monotonic() - task_started, 2),
                    error=str(exc),
                )
                self._emit(
                    DaemonEvent(
                        type="task_failed", data={"task_id": task_id, "error": str(exc)}
                    )
                )
                logger.exception(f"Task {task.id} failed: {exc}")

                # Write to IncidentMemory
                try:
                    from src.kortana.models import IncidentMemory

                    incident = IncidentMemory(
                        incident_type="task_failure",
                        description=f"Task {task_id} failed: {str(exc)}",
                        stack_trace="omitted_for_brevity",
                        resolution_strategy="Review required",
                        resolved=False,
                    )
                    session.add(incident)
                    await session.commit()
                except Exception as log_exc:
                    logger.error(
                        f"Failed to record IncidentMemory for task {task_id}: {log_exc}"
                    )

        return processed, succeeded, failed, deferred

    def _prioritize_tasks(
        self,
        candidates: list[GitHubTask],
        guidance: DirectiveSummary | None,
        limit: int,
    ) -> list[GitHubTask]:
        if not candidates:
            return []
        if guidance is None or (
            not guidance.focus_topics and not guidance.avoid_topics
        ):
            return candidates[:limit]

        ranked: list[tuple[int, GitHubTask]] = []
        fallback: list[GitHubTask] = []
        for task in candidates:
            corpus = f"{task.title} {task.description or ''}".lower()
            focus_hits = sum(topic in corpus for topic in guidance.focus_topics)
            avoid_hits = sum(topic in corpus for topic in guidance.avoid_topics)

            if avoid_hits and focus_hits == 0:
                continue

            score = focus_hits * 10 - avoid_hits * 5
            if score > 0:
                ranked.append((score, task))
            else:
                fallback.append(task)

        ranked.sort(key=lambda item: item[0], reverse=True)
        ordered = [task for _, task in ranked] + fallback
        return ordered[:limit]

    @staticmethod
    def _defer_reason(guidance: DirectiveSummary | None) -> str:
        if guidance is None:
            if os.getenv("KORTANA_SELF_AWARE_APPROVAL", "false").lower() == "true":
                return "self_approval_hold"
            return "live_execution_disabled"
        if guidance.override_mode == "halt":
            return "operator_override_halt"
        if guidance.pause_requested:
            return "paused_by_operator"
        if guidance.execution_mode == "observe":
            return "observe_only_mode"
        if guidance.execution_mode == "plan":
            return "plan_only_mode"
        if guidance.approval_required:
            return "approval_required"
        if guidance.approval_mode == "auto":
            return "auto_approved"
        if guidance.approval_mode == "self-aware":
            return "self_approval_hold"
        return "live_execution_disabled"

    def _defer_execution(
        self, task: GitHubTask, reason: str = "live_execution_disabled"
    ) -> None:
        task_key = str(task.id)
        if task_key in self._deferred_tasks:
            return

        self._deferred_tasks.add(task_key)
        event = DaemonEvent(
            type="task_deferred",
            data={
                "task_id": task_key,
                "title": task.title,
                "status": task.status,
                "reason": reason,
            },
        )
        self._emit(event)

    async def _record_outcome(
        self,
        *,
        task: GitHubTask,
        success: bool,
        latency_seconds: float,
        error: str | None = None,
    ) -> None:
        try:
            from src.kortana.services.adaptive_learner import (
                Outcome,
                get_adaptive_learner,
            )

            learner = await get_adaptive_learner()
            await learner.record(
                Outcome(
                    task_id=str(task.id),
                    task_type=self._infer_task_type(task),
                    success=success,
                    latency_seconds=round(latency_seconds, 3),
                    provider_used="gemini",
                    error=error,
                    metadata={
                        "status": task.status,
                        "repo": task.github_repo,
                        "safe_mode": self.safe_mode,
                    },
                )
            )
        except Exception as exc:
            logger.debug(f"Outcome recording failed for task {task.id}: {exc}")

    @staticmethod
    def _infer_task_type(task: GitHubTask) -> str:
        corpus = f"{task.title} {task.description or ''}".lower()
        if any(token in corpus for token in ("test", "coverage", "pytest")):
            return "test"
        if any(token in corpus for token in ("doc", "readme", "documentation")):
            return "docs"
        if any(token in corpus for token in ("deploy", "docker", "infra", "pipeline")):
            return "infra"
        if any(token in corpus for token in ("refactor", "cleanup", "restructure")):
            return "refactor"
        if any(
            token in corpus for token in ("bug", "fix", "error", "failure", "crash")
        ):
            return "code_fix"
        return "feature"

    def _format_approval_hold_comment(
        self, task: GitHubTask, decision: "ApprovalDecision"
    ) -> str:
        body = "## 🛑 HO Barrier Reached: Approval Required\n"
        body += f"**Task:** {task.title}\n"
        body += f"**Rationale:** {decision.rationale}\n\n"

        if decision.shadow_summary:
            body += "### 🪞 Shadow Trace Summary\n"
            ok = decision.shadow_summary.get("shadow_ok")
            if ok is not None:
                body += (
                    f"- **Simulation Status:** {'✅ Passed' if ok else '❌ Failed'}\n"
                )
            review = decision.shadow_summary.get("shadow_review_approved")
            if review is not None:
                body += (
                    f"- **Mock Review:** {'✅ Approved' if review else '❌ Rejected'}\n"
                )
            tests = decision.shadow_summary.get("shadow_test_exit_code")
            if tests is not None:
                body += f"- **Test Exit Code:** {tests} {'(Passed)' if tests == 0 else '(Failed)'}\n"
            risk = decision.shadow_summary.get("shadow_risk_assessment")
            if risk:
                body += f"- **Risk Assessment:** {risk}\n"

        settings = get_settings()
        dashboard_url = settings.KORTANA_FRONTEND_URL
        body += f"\n[Review in Dashboard]({dashboard_url})\n"
        return body

    def _derive_shadow_advisory(self, shadow_result: dict[str, Any]) -> dict[str, Any]:
        """Synthesize a lightweight operational summary from raw diagnostic sandbox output."""
        advisory = {
            "shadow_ok": shadow_result.get("ok", False),
            "shadow_review_approved": None,
            "shadow_test_exit_code": None,
            "shadow_risk_assessment": None,
        }
        artifacts = shadow_result.get("artifacts", {})
        if artifacts:
            review = artifacts.get("review_summary") or {}
            if "approved" in review:
                advisory["shadow_review_approved"] = review.get("approved")

            tests = artifacts.get("test_report") or {}
            if "exit_code" in tests:
                advisory["shadow_test_exit_code"] = tests.get("exit_code")

            plan = artifacts.get("plan") or {}
            if "risk_assessment" in plan:
                advisory["shadow_risk_assessment"] = plan.get("risk_assessment")

        return advisory

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "enabled": self.enabled,
            "cycle_interval_seconds": self.cycle_interval,
            "base_cycle_interval_seconds": self.base_cycle_interval,
            "max_tasks_per_cycle": self.max_tasks,
            "base_max_tasks_per_cycle": self.base_max_tasks,
            "repo": self.repo,
            "github_mode": self._github_mode(),
            "safe_mode": self.safe_mode,
            "live_execution_enabled": self.live_execution_enabled,
            "control_mode": self.control_mode,
            "adaptation_history": self._adaptation_history[-10:],
            "workspace_bridge": self.metrics.get("workspace_bridge"),
            **self.metrics,
        }


_daemon: AutonomyDaemon | None = None


def get_autonomy_daemon() -> AutonomyDaemon:
    global _daemon
    if _daemon is None:
        _daemon = AutonomyDaemon()
    return _daemon
