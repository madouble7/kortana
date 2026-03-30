from typing import Dict, Any
import os
from datetime import datetime
from kortana_hub.autonomous_skill_base import AutonomousSkill


class LocalWatcherSkill(AutonomousSkill):
    """Autonomous skill that watches a local directory for new text files.

    On each `run_periodic` invocation it will scan the configured `watch_dir`
    (from config) and add any unseen `.txt` files' contents into memory as notes.

    This skill is local-only and will not perform any network actions.
    """

    def __init__(self, watch_dir: str | None = None):
        self.watch_dir = watch_dir

    def run_periodic(self, hub, memory, config: Dict[str, Any]) -> None:
        path = self.watch_dir or config.get("watch_dir")
        if not path or not os.path.isdir(path):
            return

        for name in os.listdir(path):
            if not name.lower().endswith(".txt"):
                continue
            full = os.path.join(path, name)
            try:
                mtime = os.path.getmtime(full)
            except Exception:
                continue

            # Check memory for a record of processing this filename
            found = False
            for note in memory.search(name, limit=10):
                if name in (note.get("text") or "") or name == note.get("text"):
                    found = True
                    break
            if found:
                continue

            try:
                with open(full, "r", encoding="utf-8") as f:
                    text = f.read()
            except Exception:
                continue

            summary = f"Imported file {name} (mt:{int(mtime)})"
            memory.add_note(text=f"{summary}\n\n{text}", source="local_watcher")
