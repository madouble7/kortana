import os
from github import Github, GithubException

class AutonomyAuthError(Exception):
    """Custom exception for auth-related autonomy failure."""
    pass

class AlwaysOnMonitor:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.client = self._initialize_client()

    def _initialize_client(self):
        """Initializes client with scope validation."""
        if not self.token:
            raise AutonomyAuthError("GITHUB_TOKEN not found in environment.")
        
        g = Github(self.token)
        try:
            # Pre-flight check: Verify scopes
            # Note: PyGithub get_oauth_scopes works for PATs
            scopes = g.get_oauth_scopes()
            if 'repo' not in scopes:
                raise AutonomyAuthError("CRITICAL: Token scope lacks 'repo' permissions.")
            return g
        except Exception as e:
            raise AutonomyAuthError(f"Initialization failure: {str(e)}")

    def create_autonomy_branch(self, branch_name):
        """Structural fix for Branch Creation."""
        try:
            repo = self.client.get_repo("Kortana/Kortana-Prime")
            sb = repo.get_branch("main")
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=sb.commit.sha)
        except GithubException as e:
            if e.status == 403:
                self._handle_auth_escalation()
            raise

    def _handle_auth_escalation(self):
        """
        KOR'TANA PRIME PROTOCOL:
        In the event of a 403, trigger notification to administrative channel.
        """
        # Log error for system audit
        print("[CRITICAL] Permission elevation required. Auth scope mismatch detected.")
        # Implementation for automated notification would hook into the notification service here