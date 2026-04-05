from __future__ import annotations

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.kortana.models import AutonomyCycleMemory
from tests.conftest import SyncTestClient


@pytest.mark.asyncio
async def test_daemon_status_reports_external_worker_health(app_fixture, db):
    cycle = AutonomyCycleMemory(
        cycle_id="cycle_test_1",
        start_time=datetime.utcnow() - timedelta(seconds=45),
        end_time=datetime.utcnow() - timedelta(seconds=15),
        tasks_processed=2,
        approvals_processed=0,
        errors_encountered=0,
        metrics={
            "source": "test",
            "provider_health": {
                "github": "backoff_until:2026-04-05T12:00:00 (45s remaining)",
                "gemini": "ok",
            },
        },
    )
    db.add(cycle)
    await db.commit()

    fake_daemon = MagicMock()
    fake_daemon.get_status.return_value = {"running": False, "enabled": True}

    with (
        patch.dict(os.environ, {"KORTANA_DAEMON_IN_PROCESS": "false"}, clear=False),
        patch(
            "src.kortana.routers.daemon.get_autonomy_daemon",
            return_value=fake_daemon,
        ),
    ):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app_fixture),
            base_url="http://testserver",
        ) as client:
            response = await client.get("/api/daemon/status")

    assert response.status_code == 200
    data = response.json()
    assert data["deployment_mode"] == "external"
    assert data["control_available"] is False
    assert data["local_process"] == {"running": False, "enabled": True}
    assert data["provider_health"]["github"].startswith("backoff_until:")
    assert data["external_daemon"]["alive"] is True
    assert data["external_daemon"]["state"] == "alive"
    assert data["external_daemon"]["last_cycle_id"] == "cycle_test_1"
    assert data["external_daemon"]["provider_health"]["gemini"] == "ok"


@pytest.mark.asyncio
async def test_daemon_cycles_returns_task_event_log(app_fixture, db):
    cycle = AutonomyCycleMemory(
        cycle_id="cycle_test_events",
        start_time=datetime.utcnow() - timedelta(seconds=75),
        end_time=datetime.utcnow() - timedelta(seconds=30),
        tasks_processed=1,
        approvals_processed=0,
        errors_encountered=0,
        metrics={
            "deferred": 1,
            "system_state": "guarded",
            "task_events": [
                {
                    "type": "task_deferred",
                    "timestamp": "2026-04-05T03:40:00",
                    "data": {
                        "task_id": "task-guardrail",
                        "title": "Guardrail blocked task",
                        "reason": "patch_guardrail_rejected",
                    },
                }
            ],
        },
    )
    db.add(cycle)
    await db.commit()

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app_fixture),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/daemon/cycles?limit=5")

    assert response.status_code == 200
    data = response.json()
    matching = next(item for item in data if item["cycle_id"] == "cycle_test_events")
    assert matching["metrics"]["deferred"] == 1
    assert matching["metrics"]["task_events"][0]["type"] == "task_deferred"
    assert (
        matching["metrics"]["task_events"][0]["data"]["reason"]
        == "patch_guardrail_rejected"
    )


def test_daemon_start_rejected_in_external_mode(app_fixture):
    fake_daemon = MagicMock()
    fake_daemon.start = AsyncMock()

    with (
        patch.dict(os.environ, {"KORTANA_DAEMON_IN_PROCESS": "false"}, clear=False),
        patch(
            "src.kortana.routers.daemon.get_autonomy_daemon",
            return_value=fake_daemon,
        ),
    ):
        client = SyncTestClient(app_fixture)
        try:
            response = client.post("/api/daemon/start")
        finally:
            client.close()

    assert response.status_code == 409
    fake_daemon.start.assert_not_called()


def test_daemon_stop_rejected_in_external_mode(app_fixture):
    fake_daemon = MagicMock()
    fake_daemon.stop = AsyncMock()

    with (
        patch.dict(os.environ, {"KORTANA_DAEMON_IN_PROCESS": "false"}, clear=False),
        patch(
            "src.kortana.routers.daemon.get_autonomy_daemon",
            return_value=fake_daemon,
        ),
    ):
        client = SyncTestClient(app_fixture)
        try:
            response = client.post("/api/daemon/stop")
        finally:
            client.close()

    assert response.status_code == 409
    fake_daemon.stop.assert_not_called()


def test_daemon_start_allowed_in_embedded_mode(app_fixture):
    fake_daemon = MagicMock()
    fake_daemon.start = AsyncMock()
    fake_daemon.get_status.return_value = {"running": True, "enabled": True}

    with (
        patch.dict(os.environ, {"KORTANA_DAEMON_IN_PROCESS": "true"}, clear=False),
        patch(
            "src.kortana.routers.daemon.get_autonomy_daemon",
            return_value=fake_daemon,
        ),
    ):
        client = SyncTestClient(app_fixture)
        try:
            response = client.post("/api/daemon/start")
        finally:
            client.close()

    assert response.status_code == 200
    assert response.json()["status"] == "running"
    fake_daemon.start.assert_awaited_once()


def test_daemon_status_embedded_exposes_provider_health(app_fixture):
    fake_daemon = MagicMock()
    fake_daemon.get_status.return_value = {
        "running": True,
        "enabled": True,
        "provider_health": {"github": "ok", "gemini": "ok"},
    }

    with (
        patch.dict(os.environ, {"KORTANA_DAEMON_IN_PROCESS": "true"}, clear=False),
        patch(
            "src.kortana.routers.daemon.get_autonomy_daemon",
            return_value=fake_daemon,
        ),
    ):
        client = SyncTestClient(app_fixture)
        try:
            response = client.get("/api/daemon/status")
        finally:
            client.close()

    assert response.status_code == 200
    data = response.json()
    assert data["deployment_mode"] == "embedded"
    assert data["provider_health"] == {"github": "ok", "gemini": "ok"}
