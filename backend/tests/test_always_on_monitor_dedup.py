import asyncio
from unittest.mock import AsyncMock

import pytest

from src.kortana.services.always_on_monitor import AlwaysOnMonitor


class StubDaemon:
    def get_status(self) -> dict[str, object]:
        return {
            "running": True,
            "safe_mode": True,
            "control_mode": "safe_mode",
            "live_execution_enabled": False,
            "tasks_processed": 3,
            "tasks_succeeded": 2,
            "tasks_failed": 1,
        }


@pytest.mark.asyncio
async def test_force_check_runs_when_idle(monkeypatch):
    monkeypatch.setattr(
        "src.kortana.services.always_on_monitor.get_autonomy_daemon",
        lambda: StubDaemon(),
    )

    monitor = AlwaysOnMonitor()
    monitor._monitoring_cycle = AsyncMock()

    status = await monitor.force_check()

    assert status["cycle_triggered"] is True
    assert status["cycle_in_progress"] is False
    monitor._monitoring_cycle.assert_awaited_once()


@pytest.mark.asyncio
async def test_force_check_skips_when_cycle_already_running(monkeypatch):
    monkeypatch.setattr(
        "src.kortana.services.always_on_monitor.get_autonomy_daemon",
        lambda: StubDaemon(),
    )

    monitor = AlwaysOnMonitor()
    started = asyncio.Event()
    release = asyncio.Event()

    async def slow_cycle() -> None:
        started.set()
        await release.wait()

    monitor._monitoring_cycle = slow_cycle

    first_cycle = asyncio.create_task(
        monitor._run_cycle_guarded(source="background", skip_if_running=False)
    )
    await started.wait()

    status = await monitor.force_check()

    assert status["cycle_triggered"] is False
    assert status["cycle_in_progress"] is True
    assert monitor.stats["cycles_skipped"] == 1

    release.set()
    assert await first_cycle is True
