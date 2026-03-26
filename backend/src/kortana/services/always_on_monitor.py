class AlwaysOnMonitor:
    def __init__(self, github_service):
        self.github_service = github_service
        self.state = "ACTIVE"

    def monitor_loop(self):
        if self.state == "SUSPENDED": return
        try:
            self.github_service.create_branch("patch-test")
        except PermissionError:
            self.state = "SUSPENDED"
            print("Autonomy suspended: Insufficient GitHub Scopes.")