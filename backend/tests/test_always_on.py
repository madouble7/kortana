import pytest
from unittest.mock import AsyncMock
from backend.src.kortana.services.always_on_monitor import AlwaysOnMonitor

@pytest.mark.asyncio
async def test_always_on_degrades_on_permission_error():
    monitor = AlwaysOnMonitor()
    monitor.github_service.execute_task = AsyncMock(side_effect=PermissionError)
    await monitor.run_cycle()
    assert monitor.self_awareness.state == "DEGRADED_MODE"