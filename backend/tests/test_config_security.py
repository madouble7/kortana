import pytest
from unittest.mock import patch
from backend.src.kortana.services.github_autonomy_service import GitHubAutonomyService

def test_insufficient_scopes_trigger_read_only():
    with patch('requests.get') as mock_get:
        mock_get.return_value.status_code = 403
        with pytest.raises(PermissionError):
            GitHubAutonomyService()