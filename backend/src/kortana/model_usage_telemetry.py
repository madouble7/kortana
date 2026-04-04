"""Runtime model usage telemetry for operator visibility."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any

from src.kortana.model_lane_policy import describe_model_lane, get_active_model_lane


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
        self._total = 0
        self._by_subsystem: Counter[str] = Counter()
        self._by_provider: Counter[str] = Counter()
        self._by_model: Counter[str] = Counter()
        self._by_catalog: Counter[str] = Counter()

    def reset(self) -> None:
        """Clear all recorded events. Intended for tests."""
        with self._lock:
            self._recent.clear()
            self._total = 0
            self._by_subsystem.clear()
            self._by_provider.clear()
            self._by_model.clear()
            self._by_catalog.clear()

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
