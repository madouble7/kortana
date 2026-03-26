from enum import Enum
from kortana.services.github_autonomy_service import GithubForbiddenError

class TaskStatus(Enum):
    RUNNING = "RUNNING"
    SUSPENDED = "SUSPENDED"

class AlwaysOnMonitor:
    async def attempt_self_repair(self):
        try:
            # Logic for repair
            return TaskStatus.RUNNING
        except GithubForbiddenError:
            return TaskStatus.SUSPENDED