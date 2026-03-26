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
from typing import Any, Callable

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.config import get_settings
from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.operator_directive_service import (
    DirectiveSummary,
    get_active_operator_summary,
)
from src.kortana.services.self_awareness import get_self_awareness
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
        self.operator_guidance: dict[str, Any] | None = None
        self._adaptation_history: list[dict[str, Any]] = []
        self._deferred_tasks: set[str] = set()

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
            "system_state": "nominal",
            "last_cycle": None,
            "last_assessment": None,
            "last_self_regulation": None,
            "operator_guidance": None,
            "workspace_bridge": None,
            "uptime_start": None,
            "errors": [],
        }

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

            await asyncio.sleep(self.cycle_interval)

    async def _run_cycle(self) -> None:
        cycle_start = time.monotonic()
        self._emit(DaemonEvent(type="cycle_start"))
        logger.info("--- Autonomy cycle starting ---")

        await self._self_regulate()
        guidance = await self._load_operator_guidance()
        self._apply_operator_guidance(guidance)
        workspace_status = await self._poll_workspace_bridge()

        new_count = processed = succeeded = failed = deferred = 0
        async for session in self._db_manager.get_session():
            new_count = await self._discover_issues(session)
            effective_limit = 0 if guidance.pause_requested else self.max_tasks
            processed, succeeded, failed, deferred = await self._process_tasks(
                session, max_tasks=effective_limit, guidance=guidance
            )
            await self._manifest_self_healing(session)

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
        self.operator_guidance = {
            "active_count": guidance.active_count,
            "pause_requested": guidance.pause_requested,
            "focus_topics": guidance.focus_topics,
            "avoid_topics": guidance.avoid_topics,
            "max_tasks_override": guidance.max_tasks_override,
        }
        self.metrics["operator_guidance"] = self.operator_guidance

        if guidance.max_tasks_override is not None:
            self.max_tasks = max(1, min(self.max_tasks, guidance.max_tasks_override))

        if guidance.pause_requested:
            self.safe_mode = True
            self.live_execution_enabled = False
            self.control_mode = "paused_by_operator"
        elif guidance.focus_topics or guidance.avoid_topics:
            self.control_mode = (
                "guided_execute" if self.live_execution_enabled else "guided_observe"
            )
        else:
            self.control_mode = "safe_mode" if self.safe_mode else "execute"

    async def _discover_issues(self, session: AsyncSession) -> int:
        try:
            from src.kortana.services.github_autonomy_service import (
                GitHubAutonomyService,
            )

            service = GitHubAutonomyService(session)
            tasks = await service.fetch_and_queue_issues()
            return len(tasks) if tasks else 0
        except Exception as exc:
            logger.error(f"Issue discovery failed: {exc}")
            return 0

    async def _manifest_self_healing(self, session: AsyncSession) -> None:
        """Create one recursive self-repair issue when core autonomy fails."""
        try:
            stmt_failed = (
                select(GitHubTask)
                .where(
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
            stmt_active = select(GitHubTask).where(
                GitHubTask.title == title,
                GitHubTask.status.in_(
                    ["pending", "analyzed", "planning", "planning_complete", "executing"]
                ),
            )
            active_repairs = (await session.execute(stmt_active)).scalars().all()
            if active_repairs:
                return

            settings = get_settings()
            github_token = os.getenv("GITHUB_TOKEN") or settings.GITHUB_TOKEN
            if not github_token:
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
        except Exception as exc:
            logger.error(f"Self-repair manifestation failed: {exc}")

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
                if task.status in {"queued", "pending"}:
                    await service.analyze_task(task)
                if task.status == "analyzed":
                    await service.plan_task(task)
                if task.status == "planning_complete":
                    if self.live_execution_enabled:
                        await service.execute_task(task, dry_run=False)
                        self._deferred_tasks.discard(str(task.id))
                    else:
                        deferred += 1
                        self._defer_execution(task)
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
                await self._record_outcome(
                    task=task,
                    success=False,
                    latency_seconds=time.monotonic() - task_started,
                    error=str(exc),
                )
                self._emit(
                    DaemonEvent(
                        type="error",
                        data={"task_id": str(task.id), "error": str(exc)},
                    )
                )
                logger.error(f"Task {task.id} failed: {exc}")

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

    def _defer_execution(self, task: GitHubTask) -> None:
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
                "reason": "live_execution_disabled",
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
        if any(token in corpus for token in ("bug", "fix", "error", "failure", "crash")):
            return "code_fix"
        return "feature"

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "enabled": self.enabled,
            "cycle_interval_seconds": self.cycle_interval,
            "base_cycle_interval_seconds": self.base_cycle_interval,
            "max_tasks_per_cycle": self.max_tasks,
            "base_max_tasks_per_cycle": self.base_max_tasks,
            "repo": self.repo,
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
