import pytest
from fastapi import HTTPException
from backend.src.kortana.services.github_autonomy_service import AutonomyPermissionError

@pytest.mark.asyncio
async def test_always_on_branch_creation_403(mocker, always_on_monitor):
    mocker.patch('backend.src.kortana.services.github_autonomy_service.GitHubAutonomyService.create_autonomy_branch', 
                 side_effect=HTTPException(status_code=403))
    
    with pytest.raises(AutonomyPermissionError):
        await always_on_monitor.execute_task_94()