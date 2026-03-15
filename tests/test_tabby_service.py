"""
Tabby Integration Test - Verification for Ghost Protocol Phase 2
"""

from unittest.mock import MagicMock, patch

import pytest

from kortana.core.services import _services, get_tabby_service, initialize_services
from kortana.core.services.tabby_service import TabbyService


@pytest.fixture
def mock_config():
    return {
        "TABBY_EXECUTABLE": "tabby",
        "TABBY_MODEL_ID": "StarCoder2-7B",
        "TABBY_PORT": 8080,
        "TABBY_DEVICE": "cpu",
    }


@pytest.mark.async_status
def test_tabby_registry(mock_config):
    # Reset registry for testing
    _services.clear()
    initialize_services(mock_config)

    # Get service from registry
    tabby = get_tabby_service()

    assert isinstance(tabby, TabbyService)
    assert tabby.model_id == "StarCoder2-7B"
    assert tabby.port == 8080


@pytest.mark.asyncio
async def test_tabby_start_stop(mock_config):
    tabby = TabbyService(config=mock_config)

    with patch("subprocess.Popen") as mock_popen:
        mock_process = MagicMock()
        mock_process.pid = 1234
        mock_popen.return_value = mock_process

        # Start server
        started = await tabby.start_server()
        assert started is True
        assert tabby._is_active is True
        assert tabby.get_status()["pid"] == 1234

        # Stop server
        stopped = await tabby.stop_server()
        assert stopped is True
        assert tabby._is_active is False
        mock_process.terminate.assert_called_once()
