"""Phase 9 Fractal Swarm runtime manager."""

from __future__ import annotations

import asyncio
import os
from collections import deque
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Awaitable, Callable

from sqlalchemy import func, select

from src.kortana.database import get_db_manager
from src.kortana.http_client import get_http_client
from src.kortana.logger import get_logger
from src.kortana.models import GitHubTask
from src.kortana.services.autonomy_daemon import AutonomyDaemon
from src.kortana.services.goal_manager import get_goal_manager
from src.kortana.services.workspace_bridge_service import get_workspace_bridge
from src.kortana.swarm.hive_bus import HiveBus, hive_bus

logger = get_logger(__name__)

VectorProbe = Callable[[], Awaitable[dict[str, Any]]]


def _utcnow() -> str:
    return datetime.utcnow().isoformat()


@dataclass
class SwarmVectorStatus:
    label: str
    loop_interval_seconds: int
    state: str = "idle"
    last_heartbeat: str | None = None
    last_error: str | None = None
    failures: int = 0
    details: dict[str, Any] = field(default_factory=dict)


class SwarmManager:
    """Phase 9 swarm runtime with six cooperative background vectors."""

    def __init__(self, bus: HiveBus | None = None) -> None:
        self.enabled = os.getenv("PHASE9_SWARM_ENABLED", "true").lower() == "true"
        self._bus = bus or hive_bus
        self._running = False
        self._uptime_start: str | None = None
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._recent_events: deque[dict[str, Any]] = deque(maxlen=100)
        self._recent_commands: deque[dict[str, Any]] = deque(maxlen=25)
        self._paused_vectors: set[str] = set()
        self._attached_daemon_id: int | None = None
        self._db_manager = get_db_manager()
        self._workspace_bridge = get_workspace_bridge()
        self._vector_status: dict[str, SwarmVectorStatus] = {
            "zenith_architect": SwarmVectorStatus("Zenith Architect", 45),
            "code_weaver": SwarmVectorStatus("Code Weaver", 30),
            "runtime_guardian": SwarmVectorStatus("Runtime Guardian", 20),
            "network_envoy": SwarmVectorStatus("Network Envoy", 60),
            "memory_scribe": SwarmVectorStatus("Memory Scribe", 90),
            "matrix_painter": SwarmVectorStatus("Matrix Painter", 45),
        }

    async def start(self) -> None:
        """Start the swarm if it is not already running."""
        if not self.enabled:
            logger.info("Phase 9 swarm disabled via PHASE9_SWARM_ENABLED")
            return
        if self._running:
            logger.info("Phase 9 swarm already running")
            return

        self._running = True
        self._uptime_start = _utcnow()
        await self._bus.connect()
        await self._bus.subscribe("commands", self._handle_command)

        for name, probe in self._vector_factories().items():
            interval = self._vector_status[name].loop_interval_seconds
            self._tasks[name] = asyncio.create_task(
                self._run_vector_loop(name, interval, probe)
            )

        await self.publish_event(
            "swarm_awakened",
            {
                "active_vectors": len(self._tasks),
                "bus_connected": self._bus.get_status()["connected"],
            },
        )
        logger.info("Phase 9 Fractal Swarm started")

    async def stop(self) -> None:
        """Stop all vectors and disconnect the Hive Bus."""
        if not self._running:
            return

        self._running = False
        await self.publish_event("swarm_stopping", {})
        for task in self._tasks.values():
            task.cancel()
        for task in self._tasks.values():
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()
        await self._bus.disconnect()
        logger.info("Phase 9 Fractal Swarm stopped")

    async def initialize_swarm(self) -> None:
        """Backward-compatible alias for old scripts."""
        await self.start()

    async def shutdown(self) -> None:
        """Backward-compatible alias for old scripts."""
        await self.stop()

    def attach_daemon(self, daemon: AutonomyDaemon) -> None:
        """Attach daemon events to the swarm once per daemon instance."""
        daemon_id = id(daemon)
        if self._attached_daemon_id == daemon_id:
            return
        daemon.on_event(self.relay_daemon_event)
        self._attached_daemon_id = daemon_id

    async def send_command(
        self,
        command: str,
        *,
        target: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Publish and locally apply a swarm command."""
        envelope = {
            "command": command,
            "target": target,
            "payload": payload or {},
            "timestamp": _utcnow(),
        }
        self._recent_commands.appendleft(envelope)
        await self._handle_command(envelope)
        await self._bus.publish("commands", envelope)
        return envelope

    async def publish_event(
        self, event: str, payload: dict[str, Any] | None = None
    ) -> None:
        """Remember and publish a swarm event."""
        envelope = {
            "event": event,
            "timestamp": _utcnow(),
            **(payload or {}),
        }
        self._remember_event("events", envelope)
        await self._bus.publish("events", envelope)

    def relay_daemon_event(self, event: Any) -> None:
        """Forward daemon events into the swarm event stream."""
        payload = {
            "event": f"daemon_{getattr(event, 'type', 'event')}",
            "type": getattr(event, "type", "event"),
            "timestamp": getattr(event, "timestamp", _utcnow()),
            "data": getattr(event, "data", {}),
        }
        self._remember_event("daemon", payload)
        if not self._running:
            return
        try:
            asyncio.get_running_loop().create_task(self._bus.publish("events", payload))
        except RuntimeError:
            logger.debug("Swarm daemon relay skipped: no running event loop")

    def get_status(self) -> dict[str, Any]:
        """Return current swarm status."""
        return {
            "enabled": self.enabled,
            "running": self._running,
            "uptime_start": self._uptime_start,
            "bus": self._bus.get_status(),
            "vectors": {
                name: asdict(status) for name, status in self._vector_status.items()
            },
            "paused_vectors": sorted(self._paused_vectors),
            "recent_events": list(self._recent_events),
            "recent_commands": list(self._recent_commands),
        }

    def get_recent_events(self, limit: int = 25) -> list[dict[str, Any]]:
        return list(self._recent_events)[: max(1, min(limit, 100))]

    async def _handle_command(self, payload: dict[str, Any]) -> None:
        command = str(payload.get("command") or "").strip().lower()
        target = payload.get("target")
        target_name = str(target).strip().lower() if target else None
        if not command:
            return

        if command == "shutdown":
            await self.stop()
            return

        if command == "pause":
            if target_name:
                self._paused_vectors.add(target_name)
            else:
                self._paused_vectors.update(self._vector_status)
            return

        if command == "resume":
            if target_name:
                self._paused_vectors.discard(target_name)
            else:
                self._paused_vectors.clear()
            return

        if command == "pulse" and target_name in self._vector_status:
            status = self._vector_status[target_name]
            status.state = "manual_pulse_requested"
            status.details["manual_pulse_at"] = _utcnow()

    async def _run_vector_loop(
        self, name: str, interval_seconds: int, probe: VectorProbe
    ) -> None:
        status = self._vector_status[name]
        while self._running:
            if name in self._paused_vectors:
                status.state = "paused"
                await asyncio.sleep(1)
                continue

            try:
                details = await probe()
                status.state = "nominal"
                status.last_heartbeat = _utcnow()
                status.last_error = None
                status.details = details
                await self.publish_event(
                    "vector_pulse",
                    {
                        "vector": name,
                        "label": status.label,
                        "state": status.state,
                        "details": details,
                    },
                )
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                status.state = "error"
                status.last_heartbeat = _utcnow()
                status.last_error = str(exc)
                status.failures += 1
                await self.publish_event(
                    "vector_failure",
                    {
                        "vector": name,
                        "label": status.label,
                        "error": str(exc),
                    },
                )
            await asyncio.sleep(interval_seconds)

    def _vector_factories(self) -> dict[str, VectorProbe]:
        return {
            "zenith_architect": self._zenith_architect_probe,
            "code_weaver": self._code_weaver_probe,
            "runtime_guardian": self._runtime_guardian_probe,
            "network_envoy": self._network_envoy_probe,
            "memory_scribe": self._memory_scribe_probe,
            "matrix_painter": self._matrix_painter_probe,
        }

    async def _zenith_architect_probe(self) -> dict[str, Any]:
        workspace = await self._workspace_bridge.poll()
        goals = get_goal_manager().get_status()
        return {
            "branch": workspace["branch"],
            "dirty": workspace["dirty"],
            "changed_count": workspace["changed_count"],
            "top_goals": goals["top_3"],
            "next_goal": goals["next_goal"]["title"] if goals["next_goal"] else None,
        }

    async def _code_weaver_probe(self) -> dict[str, Any]:
        async with self._db_manager.session_scope() as db:
            counts_stmt = (
                select(GitHubTask.status, func.count())
                .group_by(GitHubTask.status)
                .order_by(GitHubTask.status)
            )
            counts = {
                status: count for status, count in (await db.execute(counts_stmt)).all()
            }

            next_stmt = (
                select(
                    GitHubTask.github_issue_number,
                    GitHubTask.status,
                    GitHubTask.title,
                )
                .where(
                    GitHubTask.status.in_(("pending", "analyzed", "planning_complete"))
                )
                .order_by(GitHubTask.created_at.asc())
                .limit(3)
            )
            next_tasks = [
                {"issue": issue_number, "status": status, "title": title}
                for issue_number, status, title in (await db.execute(next_stmt)).all()
            ]

        return {"queued_by_status": counts, "next_tasks": next_tasks}

    async def _runtime_guardian_probe(self) -> dict[str, Any]:
        from src.kortana.services.autonomy_daemon import get_autonomy_daemon
        from src.kortana.services.always_on_monitor import get_always_on_monitor

        daemon_status = get_autonomy_daemon().get_status()
        monitor_status = get_always_on_monitor().get_status()
        return {
            "daemon_state": daemon_status.get("system_state"),
            "daemon_control_mode": daemon_status.get("control_mode"),
            "daemon_error_count": len(daemon_status.get("errors", [])),
            "monitor_running": monitor_status.get("is_running"),
            "monitor_last_run": monitor_status.get("statistics", {}).get("last_run"),
        }

    async def _network_envoy_probe(self) -> dict[str, Any]:
        return {
            "hive_bus_connected": self._bus.get_status()["connected"],
            "circuit_breakers": get_http_client().get_all_circuit_statuses(),
        }

    async def _memory_scribe_probe(self) -> dict[str, Any]:
        from src.kortana.services.adaptive_learner import get_adaptive_learner

        learner = await get_adaptive_learner()
        learner_status = learner.get_status()
        goal_status = get_goal_manager().get_status()
        return {
            "outcomes_recorded": learner_status["outcomes_recorded"],
            "strategy_count": learner_status["strategy_count"],
            "active_goals": goal_status["active"],
        }

    async def _matrix_painter_probe(self) -> dict[str, Any]:
        workspace = self._workspace_bridge.get_status()
        changed_files = workspace.get("changed_files", [])
        frontend_files = [
            path
            for path in changed_files
            if path.startswith("frontend/") or path.startswith("app/")
        ]
        repo_root = Path(workspace["repo_root"])
        return {
            "frontend_changed": frontend_files,
            "frontend_dirty": bool(frontend_files),
            "frontend_exists": (repo_root / "frontend").exists(),
            "app_exists": (repo_root / "app").exists(),
        }

    def _remember_event(self, channel: str, payload: dict[str, Any]) -> None:
        self._recent_events.appendleft({"channel": channel, **payload})


_swarm_manager: SwarmManager | None = None


def get_swarm_manager() -> SwarmManager:
    global _swarm_manager
    if _swarm_manager is None:
        _swarm_manager = SwarmManager()
    return _swarm_manager


async def main() -> None:
    manager = get_swarm_manager()
    try:
        await manager.start()
        while manager.get_status()["running"]:
            await asyncio.sleep(1)
    finally:
        await manager.stop()


if __name__ == "__main__":
    asyncio.run(main())
