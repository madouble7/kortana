import pytest
from src.token_manager import TokenManager

@pytest.fixture
def token_manager():
    return TokenManager()

def test_refresh_token(token_manager):
    initial_token = token_manager.token
    token_manager.refresh_token()  # Assuming this method refreshes the token
    assert token_manager.token != initial_token
    assert token_manager.token is not None

def test_validate_token(token_manager):
    token_manager.refresh_token()  # Refresh the token first
    assert token_manager.validate_token(token_manager.token)  # Assuming this method validates the token

def test_invalid_token(token_manager):
    invalid_token = "invalid_token"
    assert not token_manager.validate_token(invalid_token)  # Should return False for invalid token