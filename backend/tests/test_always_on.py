from unittest.mock import MagicMock
from backend.src.kortana.services.always_on_monitor import AlwaysOnMonitor

def test_monitor_suspends_on_permission_error():
    mock_service = MagicMock()
    mock_service.create_branch.side_effect = PermissionError
    monitor = AlwaysOnMonitor(mock_service)
    monitor.monitor_loop()
    assert monitor.state == "SUSPENDED"