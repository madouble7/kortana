class AdvancedOrchestrationService:
    def reconcile_state(self, report):
        if report.get("reason") == "SCOPE_MISMATCH":
            self.transition_to_state("CRITICAL_WAIT")
            self.notify_admin("KOR'TANA PRIME requires updated GITHUB_TOKEN with repo/workflow scopes.")

    def transition_to_state(self, state):
        self.current_state = state