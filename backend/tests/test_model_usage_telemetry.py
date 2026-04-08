"""Tests for runtime model usage telemetry."""

from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from src.kortana.model_usage_telemetry import (
    ModelUsageTelemetry,
    get_model_usage_telemetry,
)
from src.kortana.models import AuditLog


def test_model_usage_telemetry_summary_groups_events() -> None:
    telemetry = get_model_usage_telemetry()
    telemetry.reset()

    telemetry.record_generation(
        subsystem="llm_router",
        provider="gemini",
        model="gemini-2.0-flash",
        catalog="llm_router_defaults",
        selection="primary_default",
        runtime_lane="core",
        tokens_used=11,
    )
    telemetry.record_generation(
        subsystem="api_integration",
        provider="groq",
        model="mixtral-8x7b-32768",
        catalog="cost_router_defaults",
        selection="task:summary",
        runtime_lane="core",
    )

    summary = telemetry.get_summary()

    assert summary["total_generations"] == 2
    assert summary["total_tokens_used"] == 11
    assert summary["by_subsystem"]["llm_router"] == 1
    assert summary["by_subsystem"]["api_integration"] == 1
    assert summary["by_catalog"]["llm_router_defaults"] == 1
    assert summary["by_provider"]["gemini"] == 1
    assert summary["by_provider_tokens"]["gemini"] == 11
    assert summary["by_model_tokens"]["gemini-2.0-flash"] == 11
    assert len(summary["recent"]) == 2


@pytest.mark.asyncio
async def test_model_usage_telemetry_persists_and_summarizes(monkeypatch) -> None:
    telemetry = ModelUsageTelemetry()
    stored_logs: list[AuditLog] = []

    class FakeScalarResult:
        def __init__(self, rows: list[AuditLog]) -> None:
            self._rows = rows

        def all(self) -> list[AuditLog]:
            return self._rows

    class FakeResult:
        def __init__(self, value: object) -> None:
            self._value = value

        def scalar_one(self) -> object:
            return self._value

        def scalars(self) -> FakeScalarResult:
            rows = self._value if isinstance(self._value, list) else []
            return FakeScalarResult(rows)

    class FakeSession:
        def add(self, log: AuditLog) -> None:
            if log.created_at is None:
                log.created_at = datetime.utcnow()
            stored_logs.append(log)

        async def execute(self, stmt: object) -> FakeResult:
            if "count" in str(stmt).lower():
                return FakeResult(len(stored_logs))
            ordered = sorted(
                stored_logs,
                key=lambda entry: entry.created_at or datetime.min,
                reverse=True,
            )
            return FakeResult(ordered)

    class FakeDBManager:
        @asynccontextmanager
        async def session_scope(self):
            yield FakeSession()

    monkeypatch.setattr(
        "src.kortana.model_usage_telemetry.get_db_manager",
        lambda: FakeDBManager(),
    )

    telemetry.record_generation(
        subsystem="llm_router",
        provider="gemini",
        model="gemini-2.0-flash",
        catalog="llm_router_defaults",
        selection="primary_default",
        runtime_lane="core",
        tokens_used=21,
    )
    await telemetry.flush_persistence()

    summary = await telemetry.get_persisted_summary()

    assert len(stored_logs) == 1
    assert stored_logs[0].action == "model_usage"
    assert stored_logs[0].resource_type == "llm_router"
    assert summary["total_generations"] == 1
    assert summary["total_tokens_used"] == 21
    assert summary["by_subsystem"]["llm_router"] == 1
    assert summary["by_catalog"]["llm_router_defaults"] == 1
    assert summary["by_provider_tokens"]["gemini"] == 21
    assert summary["recent"][0]["selection"] == "primary_default"
