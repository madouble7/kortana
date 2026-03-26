from github import Github, GithubException

class GithubAutonomyEngine:
    def __init__(self, token):
        self.gh = Github(token)
        self._validate_permissions()

    def _validate_permissions(self):
        scopes = self.gh.get_oauth_scopes() if self.gh.get_oauth_scopes() else []
        if 'repo' not in scopes:
            raise PermissionError("PAT lacks 'repo' scope for write operations.")

    def create_autonomy_branch(self, repo_name, branch_name):
        try:
            repo = self.gh.get_repo(repo_name)
            main_ref = repo.get_git_ref("heads/main")
            return repo.create_git_ref(f"refs/heads/{branch_name}", main_ref.object.sha)
        except GithubException as e:
            if e.status == 403:
                raise PermissionError("403 Forbidden: Check repository permissions.")
            raise