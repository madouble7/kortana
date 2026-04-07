from typing import Any, Dict
from kortana_hub.skill_base import Skill
import datetime


class ExampleSkill(Skill):
    """A tiny example skill that handles 'echo' and 'time' intents."""

    def can_handle(self, intent: str, data: Dict[str, Any] | None = None) -> bool:
        name = intent.lower() if isinstance(intent, str) else str(intent).lower()
        return name in ("echo", "time")

    def handle(self, intent: str, data: Dict[str, Any] | None = None) -> str:
        intent_name = intent if isinstance(intent, str) else str(intent)
        intent_name = intent_name.lower()
        if intent_name == "echo":
            text = (data or {}).get("text") or ""
            return f"Echo: {text}"
        if intent_name == "time":
            now = datetime.datetime.now()
            return f"The current time is {now.strftime('%Y-%m-%d %H:%M:%S')}"
        return "I don't know how to do that yet."
