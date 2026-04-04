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
        metrics={"source": "test"},
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
    assert data["external_daemon"]["alive"] is True
    assert data["external_daemon"]["state"] == "alive"
    assert data["external_daemon"]["last_cycle_id"] == "cycle_test_1"


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
