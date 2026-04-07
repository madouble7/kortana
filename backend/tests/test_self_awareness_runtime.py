from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.kortana.services.self_awareness import SelfAwarenessEngine


@pytest.mark.asyncio
async def test_force_live_override_allows_execution_in_degraded_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTONOMY_FORCE_LIVE_EXECUTION", "true")
    monkeypatch.setenv("SA_EXEC_CONF_MIN", "0.72")

    awareness = SelfAwarenessEngine()
    awareness.assess = AsyncMock(
        return_value={
            "state": "degraded",
            "snapshot": {
                "success_rate": 78.95,
                "cpu_percent": 16.0,
                "memory_percent": 77.0,
                "avg_cycle_time": 3.36,
                "pending_tasks": 1,
            },
            "corrections": [],
        }
    )

    result = await awareness.regulate(base_cycle_interval=600, base_max_tasks=3)
    profile = result["runtime_profile"]

    assert profile["safe_mode"] is False
    assert profile["allow_live_execution"] is True
    assert "low_execution_confidence" in profile["reasons"]
    assert "force_live_execution_override" in profile["reasons"]


@pytest.mark.asyncio
async def test_force_live_override_does_not_bypass_critical_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUTONOMY_FORCE_LIVE_EXECUTION", "true")

    awareness = SelfAwarenessEngine()
    awareness.assess = AsyncMock(
        return_value={
            "state": "critical",
            "snapshot": {
                "success_rate": 10.0,
                "cpu_percent": 95.0,
                "memory_percent": 91.0,
                "avg_cycle_time": 1200.0,
                "pending_tasks": 12,
            },
            "corrections": [],
        }
    )

    result = await awareness.regulate(base_cycle_interval=600, base_max_tasks=3)
    profile = result["runtime_profile"]

    assert profile["safe_mode"] is True
    assert profile["allow_live_execution"] is False
    assert "critical_system_state" in profile["reasons"]
    assert "force_live_execution_override" not in profile["reasons"]
