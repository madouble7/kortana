from typing import Dict, Any
from kortana_hub.autonomous_skill_base import AutonomousSkill


class ModelAgentSkill(AutonomousSkill):
    """Placeholder skill that represents a bridge to LLM/model agents.

    This class does NOT perform any network calls. It only demonstrates where
    and how a network-enabled model agent would be integrated. To actually
    enable network access you must set `allow_network` in the agent config and
    provide explicit credentials. Implementations should also implement
    strong rate-limiting, auditing, and human-in-the-loop approval flows.
    """

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        # conservative behavior: do not contact external services unless explicitly allowed
        if not config.get("allow_network"):
            memory.add_note(text="ModelAgentSkill: network-disabled - no action taken", source="model_agent")
            return

        # If allowed, the real implementation would call an LLM API here using
        # creds from config. We intentionally do not implement that in this repo.
        memory.add_note(text="ModelAgentSkill: would call external model (not implemented)", source="model_agent")
