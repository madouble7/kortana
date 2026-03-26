import pytest
from unittest.mock import patch
from backend.src.kortana.services.github_autonomy_service import GithubAutonomyEngine

def test_auth_failure_raises_exception():
    with patch('github.Github') as mock_gh:
        mock_gh.return_value.get_oauth_scopes.return_value = []
        with pytest.raises(PermissionError):
            GithubAutonomyEngine("invalid-token")