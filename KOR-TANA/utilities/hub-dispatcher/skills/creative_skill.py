import random
from datetime import datetime
from typing import Any, Dict

from kortana_hub.autonomous_skill_base import AutonomousSkill


class CreativeSkill(AutonomousSkill):
    """A safe, local-only autonomous skill that generates simple creative
    outputs (song ideas and short lyric lines) and stores them in memory.

    This skill intentionally avoids any network or LLM calls. It's a visible
    'alive' behavior — Kortana writes to memory and optionally to a local
    outbox file so you can see activity over time.
    """

    THEMES = [
        "midnight city",
        "paper boats",
        "lost letters",
        "neon rain",
        "quiet rebellion",
        "summer afterglow",
        "slow sunrise",
    ]

    LINES = [
        "I keep the light on for the songs you forgot",
        "We write the maps where stars refuse to fade",
        "Echoes gather like old photographs",
        "A needle stitches time into the night",
        "Your name is a chorus I sing when the streets sleep",
    ]

    def __init__(self, outbox_path: str | None = None):
        self.outbox_path = outbox_path

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        # Generate a small creative item
        theme = random.choice(self.THEMES)
        line = random.choice(self.LINES)
        timestamp = datetime.utcnow().isoformat()
        title = f"Idea: {theme} @ {timestamp}"
        content = f"{title}\n{line}\n"

        # Store in memory
        try:
            memory.add_note(text=content, source="creative_skill")
        except Exception:
            pass

        # Optionally write to an outbox file so the user can see Kortana 'publishing'
        if self.outbox_path:
            try:
                with open(self.outbox_path, "a", encoding="utf-8") as f:
                    f.write(content + "\n")
            except Exception:
                pass
