"""
Always-on monitor facade for legacy HTTP routes.

The autonomy daemon now owns the actual continuous execution loop. This module
keeps the older `/api/always-on/*` monitor endpoints working by exposing a
lightweight background observer that reports daemon/task state.
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.autonomy_daemon import get_autonomy_daemon

logger = get_logger(__name__)


class AlwaysOnMonitor:
    """Lightweight observer for the always-on daemon."""

    def __init__(self) -> None:
        self.db_manager = get_db_manager()
        self.monitoring_enabled = (
            os.getenv("ALWAYS_ON_MONITORING", "true").lower() == "true"
        )
        self.check_interval = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.is_running = False
        self.last_check: str | None = None
        self._task: asyncio.Task[None] | None = None
        self.stats: dict[str, Any] = {
            "issues_fetched": 0,
            "tasks_created": 0,
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "human_interventions": 0,
            "last_run": None,
        }

    async def start_monitoring(self) -> None:
        if not self.monitoring_enabled or self.is_running:
            return

        self.is_running = True
        logger.info(
            "Always-on monitor started "
            f"(interval={self.check_interval}s, max_concurrent={self.max_concurrent_tasks})"
        )
        try:
            while self.is_running:
                await self._monitoring_cycle()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            raise
        finally:
            self.is_running = False

    async def _monitoring_cycle(self) -> None:
        daemon_status = get_autonomy_daemon().get_status()
        self.last_check = datetime.utcnow().isoformat()
        self.stats["last_run"] = self.last_check
        self.stats["tasks_processed"] = int(daemon_status.get("tasks_processed", 0) or 0)
        self.stats["tasks_completed"] = int(
            daemon_status.get("tasks_succeeded", 0) or 0
        )
        self.stats["tasks_failed"] = int(daemon_status.get("tasks_failed", 0) or 0)

    def stop_monitoring(self) -> None:
        self.is_running = False
        if self._task is not None and not self._task.done():
            self._task.cancel()
        self._task = None
        logger.info("Always-on monitor stopped")

    def get_status(self) -> dict[str, Any]:
        daemon_status = get_autonomy_daemon().get_status()
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "is_running": self.is_running,
            "last_check": self.last_check,
            "check_interval": self.check_interval,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "statistics": self.stats,
            "daemon": {
                "running": daemon_status.get("running"),
                "safe_mode": daemon_status.get("safe_mode"),
                "control_mode": daemon_status.get("control_mode"),
                "live_execution_enabled": daemon_status.get(
                    "live_execution_enabled"
                ),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def get_task_status(self) -> dict[str, Any]:
        async with self.db_manager.session_scope() as db:
            async def count_filtered(filter_expr: Any = None) -> int:
                stmt = select(func.count()).select_from(GitHubTask)
                if filter_expr is not None:
                    stmt = stmt.where(filter_expr)
                result = await db.execute(stmt)
                return int(result.scalar_one())

            total_tasks = await count_filtered()
            pending = await count_filtered(GitHubTask.status == "pending")
            analyzing = await count_filtered(GitHubTask.status == "analyzing")
            planning = await count_filtered(GitHubTask.status == "planning")
            planning_complete = await count_filtered(
                GitHubTask.status == "planning_complete"
            )
            executing = await count_filtered(GitHubTask.status == "executing")
            completed = await count_filtered(GitHubTask.status == "completed")
            failed = await count_filtered(GitHubTask.status == "failed")
            waiting_ho = await count_filtered(GitHubTask.status == "waiting_for_ho")

            auto_tasks = await count_filtered(GitHubTask.classification == "auto")
            ho_tasks = await count_filtered(GitHubTask.classification == "ho")
            approval_tasks = await count_filtered(
                GitHubTask.classification == "approval"
            )

        return {
            "total_tasks": total_tasks,
            "by_status": {
                "pending": pending,
                "analyzing": analyzing,
                "planning": planning,
                "planning_complete": planning_complete,
                "executing": executing,
                "completed": completed,
                "failed": failed,
                "waiting_for_ho": waiting_ho,
            },
            "by_classification": {
                "auto": auto_tasks,
                "ho": ho_tasks,
                "approval": approval_tasks,
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    async def force_check(self) -> dict[str, Any]:
        await self._monitoring_cycle()
        return self.get_status()


_monitor: AlwaysOnMonitor | None = None


def get_always_on_monitor() -> AlwaysOnMonitor:
    global _monitor
    if _monitor is None:
        _monitor = AlwaysOnMonitor()
    return _monitor


async def start_always_on_monitor() -> None:
    monitor = get_always_on_monitor()
    monitor._task = asyncio.current_task()
    await monitor.start_monitoring()


def stop_always_on_monitor() -> None:
    global _monitor
    if _monitor is not None:
        _monitor.stop_monitoring()
        _monitor = None
