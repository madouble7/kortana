"""Always-on monitoring service for the autonomous runtime."""

from __future__ import annotations

import asyncio
import inspect
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

from sqlalchemy import func, select

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.autonomy_daemon import get_autonomy_daemon
from src.kortana.services.local_backlog_service import LocalBacklogService
from src.kortana.services.operator_directive_service import get_active_operator_summary
from src.kortana.services.workspace_bridge_service import get_workspace_bridge

logger = get_logger(__name__)

try:
    from src.kortana.services.github_autonomy_service import GitHubAutonomyService
except Exception:  # pragma: no cover - patched in tests or unavailable at runtime
    GitHubAutonomyService = None

try:
    from src.kortana.services.hop_autonomy_service import HOPAutonomyService
except Exception:  # pragma: no cover - patched in tests or unavailable at runtime
    HOPAutonomyService = None


class _PassthroughTaskFilter:
    async def filter_and_rank_tasks(
        self, tasks: list[GitHubTask], _repo: str | None = None
    ) -> list[tuple[GitHubTask, Any]]:
        return [(task, None) for task in tasks]


class AlwaysOnMonitor:
    """Background observer/coordinator around the autonomy daemon."""

    def __init__(self) -> None:
        self.monitoring_enabled = (
            os.getenv("ALWAYS_ON_MONITORING", "true").lower() == "true"
        )
        self.check_interval = int(os.getenv("MONITOR_CHECK_INTERVAL", "60"))
        self.max_concurrent_tasks = int(os.getenv("MAX_CONCURRENT_TASKS", "5"))
        self.is_running = False
        self._task: asyncio.Task[None] | None = None
        self._cycle_in_progress = False
        self.last_check: str | None = None
        self.db_manager = get_db_manager()
        self.task_filter: Any = _PassthroughTaskFilter()
        self.github_service: Any = None
        self.hop_service: Any = None
        self.stats: dict[str, Any] = {
            "issues_fetched": 0,
            "local_tasks_created": 0,
            "tasks_created": 0,
            "tasks_processed": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "human_interventions": 0,
            "cycles_skipped": 0,
            "last_run": None,
        }

    async def start_monitoring(self) -> None:
        if not self.monitoring_enabled:
            logger.info("Always-on monitoring disabled")
            return
        if self.is_running:
            logger.warning("Always-on monitor already running")
            return

        self.is_running = True
        try:
            while self.is_running:
                await self._run_cycle_guarded(
                    source="background", skip_if_running=False
                )
                if not self.is_running:
                    break
                await asyncio.sleep(self.check_interval)
        except KeyboardInterrupt:
            logger.info("Always-on monitor interrupted")
        finally:
            self.is_running = False
            self._cycle_in_progress = False

    def stop_monitoring(self) -> None:
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
        self._task = None

        for service in (self.github_service, self.hop_service):
            if service is None:
                continue
            close = getattr(service, "close", None)
            if callable(close):
                try:
                    close()
                except Exception:
                    pass

    async def force_check(self) -> dict[str, Any]:
        cycle_triggered = await self._run_cycle_guarded(
            source="force_check",
            skip_if_running=True,
        )
        status = self.get_status()
        status["cycle_triggered"] = cycle_triggered
        return status

    async def _run_cycle_guarded(self, *, source: str, skip_if_running: bool) -> bool:
        if self._cycle_in_progress:
            if skip_if_running:
                self.stats["cycles_skipped"] += 1
                logger.info(f"Always-on cycle skipped ({source})")
                return False
            return False

        self._cycle_in_progress = True
        try:
            await self._monitoring_cycle()
            return True
        finally:
            self._cycle_in_progress = False

    async def _monitoring_cycle(self) -> None:
        daemon_status = get_autonomy_daemon().get_status()
        self.stats["tasks_processed"] = int(daemon_status.get("tasks_processed") or 0)
        self.stats["tasks_completed"] = int(daemon_status.get("tasks_succeeded") or 0)
        self.stats["tasks_failed"] = int(daemon_status.get("tasks_failed") or 0)

        try:
            tasks = await self._fetch_new_issues()
            self.stats["issues_fetched"] += len(tasks)
            self.stats["tasks_created"] += len(tasks)
        except Exception as exc:
            logger.error(f"Always-on issue fetch failed: {exc}")

        try:
            await self._process_task_pipeline()
        except Exception as exc:
            logger.error(f"Always-on pipeline failed: {exc}")

        try:
            await self._run_hop_cycle()
        except Exception as exc:
            logger.error(f"Always-on HOP cycle failed: {exc}")

        self.last_check = datetime.utcnow().isoformat()
        self.stats["last_run"] = self.last_check

    async def _fetch_new_issues(self) -> list[GitHubTask]:
        try:
            async with self._session_scope() as session:
                discovered: list[GitHubTask] = []
                guidance = await get_active_operator_summary()
                workspace_status = await get_workspace_bridge().poll()

                local_service = LocalBacklogService(session)
                local_tasks = await local_service.discover_workspace_tasks(
                    workspace_status=workspace_status,
                    guidance=guidance,
                )
                if local_tasks:
                    self.stats["local_tasks_created"] += len(local_tasks)
                    discovered.extend(local_tasks)

                if GitHubAutonomyService is None:
                    return discovered

                if daemon_status := get_autonomy_daemon().get_status():
                    if daemon_status.get("github_mode") != "full":
                        return discovered

                service = GitHubAutonomyService(session)
                self.github_service = service
                tasks = await service.fetch_and_queue_issues()
                if tasks:
                    discovered.extend(list(tasks))
                return discovered
        except Exception as exc:
            logger.error(f"Failed to fetch new issues: {exc}")
            return []

    async def _process_task_pipeline(self) -> None:
        async with self._session_scope() as session:
            stmt = (
                select(GitHubTask)
                .where(
                    GitHubTask.status.in_(
                        ["pending", "queued", "analyzed", "planning_complete"]
                    )
                )
                .order_by(GitHubTask.created_at)
                .limit(self.max_concurrent_tasks)
            )
            result = await session.execute(stmt)
            tasks = list(result.scalars().all())
            if not tasks:
                return

            ranked = await self.task_filter.filter_and_rank_tasks(tasks, None)
            for item in ranked[: self.max_concurrent_tasks]:
                task = item[0] if isinstance(item, tuple) else item
                await self._process_single_task(task, session)

    async def _process_single_task(self, task: GitHubTask, session: Any) -> None:
        if GitHubAutonomyService is None:
            return
        service = GitHubAutonomyService(session)
        self.github_service = service

        if task.status in {"pending", "queued"}:
            await service.analyze_task(task)
            return
        if task.status == "analyzed":
            await service.plan_task(task)
            return
        if task.status == "planning_complete":
            daemon_status = get_autonomy_daemon().get_status()
            if daemon_status.get("live_execution_enabled"):
                await service.execute_task(task)
            else:
                self.stats["human_interventions"] += 1

    async def _run_hop_cycle(self) -> None:
        if HOPAutonomyService is None:
            return

        service = HOPAutonomyService()
        self.hop_service = service
        run_hop_cycle = getattr(service, "run_hop_cycle", None)
        if callable(run_hop_cycle):
            try:
                await run_hop_cycle()
            except Exception as exc:
                logger.error(f"HOP cycle failed: {exc}")

    async def get_task_status(self) -> dict[str, Any]:
        async with self._session_scope() as session:
            counts: dict[str, int] = {}
            for status_name in [
                "pending",
                "queued",
                "analyzed",
                "planning_complete",
                "waiting_for_approval",
                "executing",
                "executed",
                "failed",
            ]:
                result = await session.execute(
                    select(func.count()).where(GitHubTask.status == status_name)
                )
                counts[status_name] = int(await self._maybe_await(result.scalar_one()))
            return counts

    def get_status(self) -> dict[str, Any]:
        daemon = get_autonomy_daemon().get_status()
        return {
            "monitoring_enabled": self.monitoring_enabled,
            "is_running": self.is_running,
            "last_check": self.last_check,
            "check_interval": self.check_interval,
            "max_concurrent_tasks": self.max_concurrent_tasks,
            "statistics": self.stats,
            "cycle_in_progress": self._cycle_in_progress,
            "daemon": {
                "running": daemon.get("running"),
                "safe_mode": daemon.get("safe_mode"),
                "control_mode": daemon.get("control_mode"),
                "live_execution_enabled": daemon.get("live_execution_enabled"),
                "github_mode": daemon.get("github_mode"),
            },
            "timestamp": datetime.utcnow().isoformat(),
        }

    @asynccontextmanager
    async def _session_scope(self) -> AsyncIterator[Any]:
        manager_dict = getattr(self.db_manager, "__dict__", {})
        get_session = getattr(self.db_manager, "get_session", None)
        if callable(get_session) and "get_session" in manager_dict:
            session_provider = get_session()
            if hasattr(session_provider, "__aenter__"):
                async with session_provider as session:
                    yield session
                return

            async for session in session_provider:
                yield session
                return

        session_scope = getattr(self.db_manager, "session_scope", None)
        if callable(session_scope):
            async with session_scope() as session:
                yield session
            return

        if callable(get_session):
            session_provider = get_session()
            if hasattr(session_provider, "__aenter__"):
                async with session_provider as session:
                    yield session
                return

            async for session in session_provider:
                yield session
                return

        raise RuntimeError("Database manager does not expose a usable session API")

    @staticmethod
    async def _maybe_await(value: Any) -> Any:
        if inspect.isawaitable(value):
            return await value
        return value


_monitor: AlwaysOnMonitor | None = None


def get_always_on_monitor() -> AlwaysOnMonitor:
    global _monitor
    if _monitor is None:
        _monitor = AlwaysOnMonitor()
    return _monitor


async def start_always_on_monitor() -> AlwaysOnMonitor:
    monitor = get_always_on_monitor()
    if not monitor.is_running and monitor.monitoring_enabled:
        monitor._task = asyncio.create_task(monitor.start_monitoring())
    return monitor


def stop_always_on_monitor() -> None:
    global _monitor
    if _monitor is not None:
        _monitor.stop_monitoring()
    _monitor = None
