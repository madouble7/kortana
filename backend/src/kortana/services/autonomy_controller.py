import asyncio
from .github_autonomy_service import GithubAutonomyService

class AutonomyController:
    async def execute_task(self, task):
        try:
            return await GithubAutonomyService().create_branch(task.branch_name)
        except PermissionError as e:
            print(f"[CRITICAL] Authorization Failure: {e}")
            # Transition to CRITICAL_WAIT for manual token intervention
            return {"status": "FAILED", "reason": "SCOPE_MISMATCH", "action": "REQUEST_TOKEN_UPDATE"}