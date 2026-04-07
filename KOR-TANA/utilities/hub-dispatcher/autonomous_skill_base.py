from typing import Any, Dict
from kortana_hub.skill_base import Skill


class AutonomousSkill(Skill):
    """Base class for skills that can run autonomously in the daemon loop.

    Implement `run_periodic(self, hub, memory, config)` to perform periodic
    background work. The daemon will call this method on a safe schedule.
    """

    def can_handle(self, intent: str, data: Dict[str, Any] | None = None) -> bool:
        # By default, autonomous skills don't directly handle interactive intents.
        return False

    def handle(self, intent: str, data: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError("AutonomousSkill doesn't implement interactive handle by default")

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        """Called by the daemon loop occasionally. Should be quick and idempotent.

        Avoid doing network calls directly here unless the user has explicitly
        configured API keys and approved the source. Use the config to check
        whether the skill is allowed to access the network.
        """
        raise NotImplementedError()
