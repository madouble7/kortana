"""Tests for the Phase 9 swarm manager."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from src.kortana.swarm.manager import SwarmManager


class FakeBus:
    def __init__(self) -> None:
        self.connected = False
        self.subscriptions: list[str] = []
        self.published: list[tuple[str, dict[str, Any]]] = []

    async def connect(self) -> bool:
        self.connected = True
        return True

    async def disconnect(self) -> None:
        self.connected = False

    async def subscribe(self, channel: str, callback) -> bool:  # type: ignore[no-untyped-def]
        self.subscriptions.append(channel)
        return True

    async def publish(self, channel: str, message: dict[str, Any]) -> bool:
        self.published.append((channel, message))
        return True

    def get_status(self) -> dict[str, Any]:
        return {
            "connected": self.connected,
            "subscriptions": list(self.subscriptions),
            "published_count": len(self.published),
            "last_error": None,
        }


@pytest.mark.asyncio
async def test_swarm_start_and_stop_records_events() -> None:
    manager = SwarmManager(bus=FakeBus())

    async def probe() -> dict[str, Any]:
        return {"status": "ok"}

    manager._vector_factories = lambda: {"zenith_architect": probe}  # type: ignore[assignment]
    manager._vector_status["zenith_architect"].loop_interval_seconds = 0

    await manager.start()
    await asyncio.sleep(0.01)

    status = manager.get_status()
    assert status["running"] is True
    assert status["bus"]["connected"] is True
    assert status["recent_events"]

    await manager.stop()
    assert manager.get_status()["running"] is False


@pytest.mark.asyncio
async def test_swarm_send_command_pauses_and_resumes_vectors() -> None:
    manager = SwarmManager(bus=FakeBus())

    await manager.send_command("pause", target="zenith_architect")
    assert "zenith_architect" in manager.get_status()["paused_vectors"]

    await manager.send_command("resume", target="zenith_architect")
    assert "zenith_architect" not in manager.get_status()["paused_vectors"]


def test_swarm_relay_daemon_event_records_recent_event() -> None:
    manager = SwarmManager(bus=FakeBus())
    event = type(
        "Event",
        (),
        {
            "type": "cycle_end",
            "timestamp": "2026-03-26T18:00:00",
            "data": {"processed": 2},
        },
    )()

    manager.relay_daemon_event(event)

    recent = manager.get_recent_events(1)
    assert recent[0]["event"] == "daemon_cycle_end"
    assert recent[0]["data"]["processed"] == 2
