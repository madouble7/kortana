import logging
from kortana.config import settings

class GithubForbiddenError(Exception): pass

class GithubAutonomyService:
    async def create_autonomy_branch(self, branch_name: str):
        try:
            # Implementation with explicit permission checking
            pass
        except Exception as e:
            logging.error(f"GITHUB_API_ERROR: {str(e)}")
            if "403" in str(e):
                raise GithubForbiddenError("Insufficient PAT scopes")
            raise