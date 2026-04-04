"""Runtime model usage telemetry for operator visibility."""

from __future__ import annotations

import asyncio
from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from sqlalchemy import func, select

from src.kortana.database import get_db_manager
from src.kortana.logger import get_logger
from src.kortana.model_lane_policy import describe_model_lane, get_active_model_lane
from src.kortana.models import AuditLog

logger = get_logger(__name__)


@dataclass(frozen=True)
class RuntimeModelUsageEvent:
    """A single successful runtime model usage event."""

    timestamp: str
    subsystem: str
    provider: str
    model: str
    lane: str
    runtime_lane: str
    catalog: str
    selection: str
    tokens_used: int | None = None
    task_type: str | None = None


class ModelUsageTelemetry:
    """Thread-safe in-memory summary of runtime model usage."""

    def __init__(self, max_recent: int = 100) -> None:
        self._lock = Lock()
        self._recent: deque[RuntimeModelUsageEvent] = deque(maxlen=max_recent)
        self._pending_persistence_tasks: set[asyncio.Task[None]] = set()
        self._total = 0
        self._by_subsystem: Counter[str] = Counter()
        self._by_provider: Counter[str] = Counter()
        self._by_model: Counter[str] = Counter()
        self._by_catalog: Counter[str] = Counter()

    def reset(self) -> None:
        """Clear all recorded events. Intended for tests."""
        with self._lock:
            pending_tasks = list(self._pending_persistence_tasks)
            self._pending_persistence_tasks.clear()
            self._recent.clear()
            self._total = 0
            self._by_subsystem.clear()
            self._by_provider.clear()
            self._by_model.clear()
            self._by_catalog.clear()

        for task in pending_tasks:
            try:
                task.cancel()
            except RuntimeError:
                # The originating loop may already be closed during test teardown.
                continue

    def _track_persistence_task(self, task: asyncio.Task[None]) -> None:
        with self._lock:
            self._pending_persistence_tasks.add(task)
        task.add_done_callback(self._finalize_persistence_task)

    def _finalize_persistence_task(self, task: asyncio.Task[None]) -> None:
        with self._lock:
            self._pending_persistence_tasks.discard(task)

        if task.cancelled():
            return

        try:
            error = task.exception()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Model usage persistence task inspection failed: %s", exc)
            return

        if error is not None:
            logger.debug("Model usage persistence task failed: %s", error)

    def record_generation(
        self,
        *,
        subsystem: str,
        provider: str,
        model: str,
        catalog: str,
        selection: str,
        runtime_lane: str | None = None,
        tokens_used: int | None = None,
        task_type: str | None = None,
    ) -> None:
        """Record a successful model generation event."""
        event = RuntimeModelUsageEvent(
            timestamp=datetime.now(timezone.utc).isoformat(),
            subsystem=subsystem,
            provider=provider,
            model=model,
            lane=describe_model_lane(model),
            runtime_lane=runtime_lane or get_active_model_lane().value,
            catalog=catalog,
            selection=selection,
            tokens_used=tokens_used,
            task_type=task_type,
        )
        with self._lock:
            self._recent.appendleft(event)
            self._total += 1
            self._by_subsystem[subsystem] += 1
            self._by_provider[provider] += 1
            self._by_model[model] += 1
            self._by_catalog[catalog] += 1

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        self._track_persistence_task(loop.create_task(self._persist_event(event)))

    async def _persist_event(self, event: RuntimeModelUsageEvent) -> None:
        """Persist a runtime usage event to the audit log."""
        try:
            async with get_db_manager().session_scope() as session:
                session.add(
                    AuditLog(
                        action="model_usage",
                        resource_type=event.subsystem,
                        details=asdict(event),
                    )
                )
        except Exception as exc:
            logger.debug("Failed to persist model usage event: %s", exc)

    async def flush_persistence(self) -> None:
        """Wait for any in-flight persistence tasks. Intended for tests and status reads."""
        while True:
            with self._lock:
                pending = tuple(self._pending_persistence_tasks)

            if not pending:
                return

            await asyncio.gather(*pending, return_exceptions=True)

    @staticmethod
    def _empty_summary() -> dict[str, Any]:
        return {
            "total_generations": 0,
            "last_recorded_at": None,
            "by_subsystem": {},
            "by_provider": {},
            "by_model": {},
            "by_catalog": {},
            "recent": [],
        }

    @classmethod
    def _summarize_events(
        cls,
        events: list[dict[str, Any]],
        *,
        total_generations: int | None = None,
        recent_limit: int = 20,
    ) -> dict[str, Any]:
        if not events and total_generations is None:
            return cls._empty_summary()

        by_subsystem: Counter[str] = Counter()
        by_provider: Counter[str] = Counter()
        by_model: Counter[str] = Counter()
        by_catalog: Counter[str] = Counter()

        for event in events:
            subsystem = str(event.get("subsystem", "unknown"))
            provider = str(event.get("provider", "unknown"))
            model = str(event.get("model", "unknown"))
            catalog = str(event.get("catalog", "unknown"))
            by_subsystem[subsystem] += 1
            by_provider[provider] += 1
            by_model[model] += 1
            by_catalog[catalog] += 1

        recent = events[:recent_limit]
        last_recorded_at = recent[0].get("timestamp") if recent else None
        return {
            "total_generations": (
                total_generations if total_generations is not None else len(events)
            ),
            "last_recorded_at": last_recorded_at,
            "by_subsystem": dict(by_subsystem.most_common()),
            "by_provider": dict(by_provider.most_common()),
            "by_model": dict(by_model.most_common()),
            "by_catalog": dict(by_catalog.most_common()),
            "recent": recent,
        }

    async def get_persisted_summary(
        self,
        *,
        recent_limit: int = 20,
        history_limit: int = 500,
    ) -> dict[str, Any]:
        """Return a persisted summary from audit logs so trends survive restarts."""
        await self.flush_persistence()

        try:
            async with get_db_manager().session_scope() as session:
                count_result = await session.execute(
                    select(func.count())
                    .select_from(AuditLog)
                    .where(AuditLog.action == "model_usage")
                )
                total_generations = int(count_result.scalar_one() or 0)

                rows_result = await session.execute(
                    select(AuditLog)
                    .where(AuditLog.action == "model_usage")
                    .order_by(AuditLog.created_at.desc())
                    .limit(max(history_limit, recent_limit))
                )
                rows = list(rows_result.scalars().all())
        except Exception as exc:
            logger.debug("Failed to load persisted model usage summary: %s", exc)
            return self._empty_summary()

        events: list[dict[str, Any]] = []
        for row in rows:
            details: dict[str, Any] = (
                row.details if isinstance(row.details, dict) else {}
            )
            timestamp = details.get("timestamp")
            if timestamp is None:
                timestamp = (
                    row.created_at.isoformat()
                    if row.created_at
                    else datetime.now(timezone.utc).isoformat()
                )
            event = {
                "timestamp": str(timestamp),
                "subsystem": str(
                    details.get("subsystem", row.resource_type or "unknown")
                ),
                "provider": str(details.get("provider", "unknown")),
                "model": str(details.get("model", "unknown")),
                "lane": str(details.get("lane", "unknown")),
                "runtime_lane": str(details.get("runtime_lane", "unknown")),
                "catalog": str(details.get("catalog", "unknown")),
                "selection": str(details.get("selection", "unknown")),
                "tokens_used": details.get("tokens_used"),
                "task_type": details.get("task_type"),
            }
            events.append(event)

        return self._summarize_events(
            events,
            total_generations=total_generations,
            recent_limit=recent_limit,
        )

    def get_summary(self, recent_limit: int = 20) -> dict[str, Any]:
        """Return a stable summary snapshot for operator status surfaces."""
        with self._lock:
            recent = [asdict(event) for event in list(self._recent)[:recent_limit]]
            last_recorded_at = recent[0]["timestamp"] if recent else None
            return {
                "total_generations": self._total,
                "last_recorded_at": last_recorded_at,
                "by_subsystem": dict(self._by_subsystem.most_common()),
                "by_provider": dict(self._by_provider.most_common()),
                "by_model": dict(self._by_model.most_common()),
                "by_catalog": dict(self._by_catalog.most_common()),
                "recent": recent,
            }


_model_usage_telemetry: ModelUsageTelemetry | None = None


def get_model_usage_telemetry() -> ModelUsageTelemetry:
    """Return the process-wide runtime model usage telemetry recorder."""
    global _model_usage_telemetry
    if _model_usage_telemetry is None:
        _model_usage_telemetry = ModelUsageTelemetry()
    return _model_usage_telemetry
