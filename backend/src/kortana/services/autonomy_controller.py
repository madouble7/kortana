class AutonomyController:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.is_diagnosing = False

    def handle_system_failure(self, failure_context):
        if self.is_diagnosing:
            return
        
        self.is_diagnosing = True
        try:
            self.orchestrator.remediate(failure_context)
        finally:
            self.is_diagnosing = False