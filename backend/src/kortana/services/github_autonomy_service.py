from ..config import settings

class GithubAutonomyService:
    def _validate_permissions(self):
        scopes = self.client.get_scopes()
        if not all(s in scopes for s in settings.GITHUB_REQUIRED_SCOPES):
            raise PermissionError(f"Missing required scopes: {settings.GITHUB_REQUIRED_SCOPES}")

    async def execute_task(self, task):
        self._validate_permissions()
        # Proceed with task execution...