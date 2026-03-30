"""Conservative autonomous daemon for Kortana hub.

This daemon demonstrates a safe, always-on loop that executes user-approved
autonomous skills on a schedule, persists notes to local memory, and exposes
simple pause/resume and logging controls. It is intentionally conservative:
- No network actions are performed unless explicitly allowed in `config`.
- Any sensitive or potentially destructive action must be approved by the user.

To use: create a small config dict and register skills, then call Agent.run_once()
or Agent.run_forever() from a controlled environment (console or service wrapper).
"""
import time
import json
import os
import threading
from typing import Dict, Any

from .hub import Hub
from .memory import MemoryStore
from .autonomous_skill_base import AutonomousSkill


class Agent:
    def __init__(self, hub: Hub | None = None, memory: MemoryStore | None = None, config: Dict[str, Any] | None = None):
        self.hub = hub or Hub()
        self.memory = memory or MemoryStore()
        self.config = config or {}
        self._stop_event = threading.Event()
        self._pause_event = threading.Event()
        self._pause_event.clear()  # not paused

    def register_skill(self, skill: AutonomousSkill) -> None:
        # register for interactive use as well
        self.hub.register(skill)

    def _approved_to_network(self) -> bool:
        # conservative check: explicit config flag required
        return bool(self.config.get("allow_network", False))

    def run_once(self) -> None:
        """Run one iteration of the periodic loop: call run_periodic on each skill."""
        skills = [s for s in self.hub._skills if isinstance(s, AutonomousSkill)]
        for s in skills:
            try:
                # Each skill must check config to confirm network actions.
                s.run_periodic(self.hub, self.memory, self.config)
            except NotImplementedError:
                continue
            except Exception as e:
                # log error to memory for later inspection
                self.memory.add_note(text=f"skill_error:{s.name}:{e}", source="agent")

    def run_forever(self, interval_seconds: int = 60) -> None:
        """Run the daemon loop. Use stop() to request termination or pause() to pause."""
        self._stop_event.clear()
        while not self._stop_event.is_set():
            if self._pause_event.is_set():
                time.sleep(0.5)
                continue
            self.run_once()
            # write a heartbeat
            self.memory.add_note(text=f"heartbeat", source="agent")
            for _ in range(int(interval_seconds * 2)):
                if self._stop_event.is_set() or self._pause_event.is_set():
                    break
                time.sleep(0.5)

    def start_in_thread(self, interval_seconds: int = 60) -> threading.Thread:
        t = threading.Thread(target=self.run_forever, args=(interval_seconds,), daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        self._stop_event.set()

    def pause(self) -> None:
        self._pause_event.set()

    def resume(self) -> None:
        self._pause_event.clear()

    def status(self) -> Dict[str, Any]:
        return {
            "stopped": self._stop_event.is_set(),
            "paused": self._pause_event.is_set(),
            "memory_path": self.memory.path,
            "allow_network": bool(self.config.get("allow_network", False)),
        }

    def shutdown(self):
        try:
            self.stop()
            self.memory.close()
        except Exception:
            pass


def load_config(path: str = "kortana_config.json") -> Dict[str, Any]:
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}
