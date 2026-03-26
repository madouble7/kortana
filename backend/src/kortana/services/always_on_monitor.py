class AlwaysOnMonitor:
    def __init__(self, github_service):
        self.github_service = github_service

    def execute_maintenance(self):
        try:
            self.github_service.create_autonomy_branch("kortana-prime", "patch-94")
        except PermissionError as e:
            print(f"CRITICAL: {e}. Initiating safety shutdown.")
            self.signal_shutdown()

    def signal_shutdown(self):
        # Implementation for halting autonomous routines
        pass