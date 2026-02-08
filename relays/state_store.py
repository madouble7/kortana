#!/usr/bin/env python3
"""Shared coordination state store for multi-agent orchestration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


class CoordinationStateStore:
    """Lightweight JSON/jsonl-backed shared state for coordinator and relays."""

    def __init__(self, project_root: str | None = None):
        root = Path(project_root) if project_root else Path(__file__).parent.parent
        self.project_root = root
        self.data_dir = self.project_root / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.agent_state_file = self.data_dir / "agent_state.json"
        self.task_graph_file = self.data_dir / "task_graph.json"
        self.events_file = self.data_dir / "coordination_events.jsonl"

        self._ensure_defaults()

    def _atomic_write_json(self, path: Path, payload: dict[str, Any]) -> None:
        tmp = path.with_suffix(path.suffix + ".tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        os.replace(tmp, path)

    def _read_json(self, path: Path, default: dict[str, Any]) -> dict[str, Any]:
        if not path.exists():
            return default
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else default
        except (OSError, json.JSONDecodeError):
            return default

    def _ensure_defaults(self) -> None:
        if not self.agent_state_file.exists():
            self._atomic_write_json(
                self.agent_state_file,
                {"agents": {}, "updated_at": ""},
            )

        if not self.task_graph_file.exists():
            self._atomic_write_json(
                self.task_graph_file,
                {"tasks": {}, "updated_at": ""},
            )

        self.events_file.touch(exist_ok=True)

    def read_agent_state(self) -> dict[str, Any]:
        return self._read_json(self.agent_state_file, {"agents": {}, "updated_at": ""})

    def write_agent_state(self, state: dict[str, Any]) -> None:
        self._atomic_write_json(self.agent_state_file, state)

    def read_task_graph(self) -> dict[str, Any]:
        return self._read_json(self.task_graph_file, {"tasks": {}, "updated_at": ""})

    def write_task_graph(self, graph: dict[str, Any]) -> None:
        self._atomic_write_json(self.task_graph_file, graph)

    def append_event(self, event: dict[str, Any]) -> None:
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
