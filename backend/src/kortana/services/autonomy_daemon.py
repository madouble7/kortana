"""
Self-Sustaining Autonomy Daemon

Runs as a FastAPI background task (no Celery dependency) that continuously:
  1. Discovers new GitHub issues and creates tasks
  2. Drives pending tasks through analyze → plan → execute pipeline
  3. Tracks cycle metrics and self-heals on failure
  4. Emits real-time events for WebSocket / Discord consumers

Configurable via environment:
  AUTONOMY_DAEMON_ENABLED=true
  AUTONOMY_CYCLE_INTERVAL=300      (seconds between full cycles)
  AUTONOMY_MAX_TASKS_PER_CYCLE=3   (max tasks to process per cycle)
"""

from __future__ import annotations

import asyncio
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------


@dataclass
class DaemonEvent:
    type: str  # cycle_start, task_progress, task_complete, cycle_end, error
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    data: dict[str, Any] = field(default_factory=dict)


EventCallback = Callable[[DaemonEvent], Any]


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------


class AutonomyDaemon:
    """Self-sustaining autonomy loop that runs inside FastAPI's event loop."""

    def __init__(self) -> None:
        self.enabled = os.getenv("AUTONOMY_DAEMON_ENABLED", "true").lower() == "true"
        self.cycle_interval = int(os.getenv("AUTONOMY_CYCLE_INTERVAL", "300"))
        self.max_tasks = int(os.getenv("AUTONOMY_MAX_TASKS_PER_CYCLE", "3"))
        self.repo = f"{os.getenv('GITHUB_OWNER', 'KOR-TANA')}/{os.getenv('GITHUB_REPO', 'kortana')}"

        self._running = False
        self._task: asyncio.Task[None] | None = None
        self._listeners: list[EventCallback] = []
        self._db_manager = get_db_manager()

        # Metrics
        self.metrics: dict[str, Any] = {
            "cycles_completed": 0,
            "tasks_processed": 0,
            "tasks_succeeded": 0,
            "tasks_failed": 0,
            "last_cycle": None,
            "uptime_start": None,
            "errors": [],
        }

    # ----- lifecycle -----

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
            f"Autonomy daemon started — cycle every {self.cycle_interval}s, "
            f"max {self.max_tasks} tasks/cycle"
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

    # ----- event system -----

    def on_event(self, callback: EventCallback) -> None:
        self._listeners.append(callback)

    def _emit(self, event: DaemonEvent) -> None:
        for cb in self._listeners:
            try:
                result = cb(event)
                if asyncio.iscoroutine(result):
                    asyncio.create_task(result)
            except Exception:
                pass  # Listeners must not crash the daemon

    # ----- main loop -----

    async def _loop(self) -> None:
        # small initial delay to let the app finish startup
        await asyncio.sleep(5)

        while self._running:
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"Daemon cycle error: {e}")
                self.metrics["errors"].append(
                    {"time": datetime.utcnow().isoformat(), "error": str(e)}
                )
                # Keep only last 20 errors
                self.metrics["errors"] = self.metrics["errors"][-20:]

            await asyncio.sleep(self.cycle_interval)

    async def _run_cycle(self) -> None:
        cycle_start = time.monotonic()
        self._emit(DaemonEvent(type="cycle_start"))
        logger.info("--- Autonomy cycle starting ---")

        async for session in self._db_manager.get_session():
            # Phase 1: Discover new issues
            new_count = await self._discover_issues(session)

            # Phase 2: Drive pending tasks through pipeline
            processed, succeeded, failed = await self._process_tasks(session)

        elapsed = round(time.monotonic() - cycle_start, 2)
        self.metrics["cycles_completed"] += 1
        self.metrics["tasks_processed"] += processed
        self.metrics["tasks_succeeded"] += succeeded
        self.metrics["tasks_failed"] += failed
        self.metrics["last_cycle"] = {
            "completed_at": datetime.utcnow().isoformat(),
            "duration_seconds": elapsed,
            "new_issues": new_count,
            "processed": processed,
            "succeeded": succeeded,
            "failed": failed,
        }

        self._emit(DaemonEvent(type="cycle_end", data=self.metrics["last_cycle"]))
        logger.info(
            f"--- Autonomy cycle complete — {elapsed}s, "
            f"+{new_count} issues, {succeeded}/{processed} tasks ok ---"
        )

    # ----- phases -----

    async def _discover_issues(self, session: AsyncSession) -> int:
        """Call the GitHub autonomy service to fetch new issues into the task queue."""
        try:
            from src.kortana.services.github_autonomy_service import (
                GitHubAutonomyService,
            )

            service = GitHubAutonomyService(session)
            tasks = await service.fetch_and_queue_issues()
            return len(tasks) if tasks else 0
        except Exception as e:
            logger.error(f"Issue discovery failed: {e}")
            return 0

    async def _process_tasks(self, session: AsyncSession) -> tuple[int, int, int]:
        """Drive pending tasks through analyze → plan → execute."""
        from src.kortana.services.github_autonomy_service import GitHubAutonomyService

        # Fetch pending tasks
        stmt = (
            select(GitHubTask)
            .where(GitHubTask.status.in_(["pending", "analyzed", "planning_complete"]))
            .order_by(GitHubTask.created_at)
            .limit(self.max_tasks)
        )
        result = await session.execute(stmt)
        tasks = list(result.scalars().all())

        if not tasks:
            return 0, 0, 0

        service = GitHubAutonomyService(session)
        processed = succeeded = failed = 0

        for task in tasks:
            processed += 1
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
                # Advance through pipeline stages
                if task.status == "pending":
                    await service.analyze_task(task)
                if task.status == "analyzed":
                    await service.plan_task(task)
                if task.status == "planning_complete":
                    await service.execute_task(task, dry_run=True)

                succeeded += 1
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
            except Exception as e:
                failed += 1
                logger.error(f"Task {task.id} failed: {e}")
                self._emit(
                    DaemonEvent(
                        type="error",
                        data={
                            "task_id": str(task.id),
                            "error": str(e),
                        },
                    )
                )

        return processed, succeeded, failed

    # ----- introspection -----

    def get_status(self) -> dict[str, Any]:
        return {
            "running": self._running,
            "enabled": self.enabled,
            "cycle_interval_seconds": self.cycle_interval,
            "max_tasks_per_cycle": self.max_tasks,
            "repo": self.repo,
            **self.metrics,
        }


# Singleton
_daemon: AutonomyDaemon | None = None


def get_autonomy_daemon() -> AutonomyDaemon:
    global _daemon
    if _daemon is None:
        _daemon = AutonomyDaemon()
    return _daemon
