from .self_awareness import SelfAwarenessService

class AlwaysOnMonitor:
    def __init__(self):
        self.self_awareness = SelfAwarenessService()

    async def run_cycle(self):
        try:
            await self.github_service.execute_task()
        except PermissionError:
            self.self_awareness.set_state("DEGRADED_MODE")
            await self.self_awareness.alert_admin("GitHub Auth Failure")