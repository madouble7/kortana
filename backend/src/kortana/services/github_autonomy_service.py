import requests
from ..config import settings

class GitHubAutonomyService:
    def __init__(self):
        self.is_read_only = False
        self._validate_permissions()

    def _validate_permissions(self):
        headers = {"Authorization": f"token {settings.GITHUB_PAT}"}
        response = requests.get("https://api.github.com/user", headers=headers)
        if response.status_code == 403:
            self.is_read_only = True
            raise PermissionError("CRITICAL: Token scope insufficient for autonomy.")

    def create_branch(self, branch_name: str):
        if self.is_read_only:
            return None
        # Implementation...