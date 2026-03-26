import pytest
from unittest.mock import AsyncMock, patch
from kortana.services.always_on_monitor import AlwaysOnMonitor, TaskStatus
from kortana.services.github_autonomy_service import GithubForbiddenError

@pytest.mark.asyncio
async def test_github_permission_denial_handling():
    monitor = AlwaysOnMonitor()
    with patch("kortana.services.github_autonomy_service.GithubAutonomyService.create_autonomy_branch", side_effect=GithubForbiddenError):
        result = await monitor.attempt_self_repair()
        assert result == TaskStatus.SUSPENDED