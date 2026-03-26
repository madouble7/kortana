from unittest.mock import MagicMock, patch
from backend.src.kortana.services.always_on_monitor import AlwaysOnMonitor

def test_monitor_shutdown_on_403():
    mock_svc = MagicMock()
    mock_svc.create_autonomy_branch.side_effect = PermissionError("403 Forbidden")
    monitor = AlwaysOnMonitor(mock_svc)
    
    with patch.object(monitor, 'signal_shutdown') as mock_shutdown:
        monitor.execute_maintenance()
        mock_shutdown.assert_called_once()