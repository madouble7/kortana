import pytest
from unittest.mock import patch
from src.heartbeat import refresh_token

@patch('src.heartbeat.logging')
@patch('src.heartbeat.token_manager.refresh_token')
def test_refresh_token(mock_refresh_token, mock_logging):
    mock_refresh_token.return_value = True  # Simulate successful token refresh

    result = refresh_token()

    assert result is True
    mock_logging.info.assert_called_once_with("Kor'tana is awake and the token has been refreshed.")