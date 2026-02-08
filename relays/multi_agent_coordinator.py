#!/usr/bin/env python3
"""Real-time multi-agent coordinator for Kor'tana concurrent development."""

from __future__ import annotations

import time
from datetime import datetime, timedelta
from pathlib import Path

from relays.protocol import AgentEvent, parse_event_line, utc_now_iso
from relays.state_store import CoordinationStateStore


class MultiAgentCoordinator:
    """Coordinates task claims, leases, directives, and live state updates."""

    def __init__(self, project_root: str | None = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.queues_dir = self.project_root / "queues"
        self.logs_dir = self.project_root / "logs"
        self.store = CoordinationStateStore(str(self.project_root))
        self._queue_offsets: dict[str, int] = {}
        self.lease_seconds = 120

        self.queues_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _discover_agents(self) -> list[str]:
        agents: set[str] = set()
        for queue_file in self.queues_dir.glob("*_in.txt"):
            agents.add(queue_file.stem.replace("_in", ""))
        for log_file in self.logs_dir.glob("*.log"):
            agents.add(log_file.stem)
        return sorted(agents)

    def _queue_path(self, agent: str) -> Path:
        return self.queues_dir / f"{agent}_in.txt"

    def _write_event_to_agent_queue(self, event: AgentEvent, agent: str) -> None:
        queue_path = self._queue_path(agent)
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.touch(exist_ok=True)
        with open(queue_path, "a", encoding="utf-8") as f:
            f.write(event.to_json_line() + "\n")

    def _append_event(self, event: AgentEvent) -> None:
        self.store.append_event(event.to_dict())

    def _set_agent_status(
        self, agent: str, status: str, task_id: str | None = None
    ) -> None:
        agent_state = self.store.read_agent_state()
        agents = agent_state.setdefault("agents", {})
        current = agents.get(agent, {})
        agents[agent] = {
            **current,
            "status": status,
            "task_id": task_id,
            "heartbeat": utc_now_iso(),
        }
        agent_state["updated_at"] = utc_now_iso()
        self.store.write_agent_state(agent_state)

    def _ensure_task_graph_defaults(self) -> None:
        graph = self.store.read_task_graph()
        graph.setdefault("tasks", {})
        graph.setdefault("updated_at", utc_now_iso())
        self.store.write_task_graph(graph)

    def _load_new_queue_events(self, agent: str) -> list[AgentEvent]:
        queue_path = self._queue_path(agent)
        if not queue_path.exists():
            return []

        with open(queue_path, encoding="utf-8") as f:
            lines = f.readlines()

        start = self._queue_offsets.get(agent, 0)
        new_lines = lines[start:]
        self._queue_offsets[agent] = len(lines)

        events: list[AgentEvent] = []
        for line in new_lines:
            parsed = parse_event_line(line)
            if parsed:
                events.append(parsed)
        return events

    def _create_task_if_missing(self, task_id: str, owner: str | None = None) -> None:
        graph = self.store.read_task_graph()
        tasks = graph.setdefault("tasks", {})
        if task_id not in tasks:
            tasks[task_id] = {
                "status": "pending",
                "owner": owner,
                "lease_expiry": None,
                "blocked": False,
                "updated_at": utc_now_iso(),
            }
            graph["updated_at"] = utc_now_iso()
            self.store.write_task_graph(graph)

    def _handle_task_claim(self, event: AgentEvent) -> None:
        if not event.task_id:
            return

        self._create_task_if_missing(event.task_id)
        graph = self.store.read_task_graph()
        task = graph["tasks"][event.task_id]

        lease_expiry = task.get("lease_expiry")
        lease_valid = False
        if lease_expiry:
            try:
                lease_valid = datetime.fromisoformat(lease_expiry) > datetime.utcnow()
            except ValueError:
                lease_valid = False

        if task.get("owner") and lease_valid and task.get("owner") != event.source:
            directive = AgentEvent.new(
                source="coordinator",
                target=event.source,
                event_type="DIRECTIVE",
                task_id=event.task_id,
                payload={
                    "instruction": "claim_denied",
                    "reason": f"Task leased by {task.get('owner')}",
                },
            )
            self._write_event_to_agent_queue(directive, event.source)
            self._append_event(directive)
            return

        task["owner"] = event.source
        task["status"] = "in_progress"
        task["lease_expiry"] = (
            datetime.utcnow() + timedelta(seconds=self.lease_seconds)
        ).isoformat()
        task["updated_at"] = utc_now_iso()
        graph["updated_at"] = utc_now_iso()
        self.store.write_task_graph(graph)
        self._set_agent_status(event.source, "busy", event.task_id)

    def _handle_task_update(self, event: AgentEvent) -> None:
        if not event.task_id:
            return

        self._create_task_if_missing(event.task_id)
        graph = self.store.read_task_graph()
        task = graph["tasks"][event.task_id]

        new_status = str(
            event.payload.get("status") if event.payload else "in_progress"
        )
        task["status"] = new_status
        task["updated_at"] = utc_now_iso()

        if new_status.lower() in {"done", "completed", "merged"}:
            task["lease_expiry"] = None
            self._set_agent_status(event.source, "idle", None)
        else:
            task["lease_expiry"] = (
                datetime.utcnow() + timedelta(seconds=self.lease_seconds)
            ).isoformat()

        graph["updated_at"] = utc_now_iso()
        self.store.write_task_graph(graph)

    def _handle_blocker(self, event: AgentEvent) -> None:
        if not event.task_id:
            return

        self._create_task_if_missing(event.task_id)
        graph = self.store.read_task_graph()
        task = graph["tasks"][event.task_id]
        task["blocked"] = True
        task["status"] = "blocked"
        task["updated_at"] = utc_now_iso()
        graph["updated_at"] = utc_now_iso()
        self.store.write_task_graph(graph)

        directive = AgentEvent.new(
            source="coordinator",
            target="all",
            event_type="DIRECTIVE",
            task_id=event.task_id,
            payload={
                "instruction": "replan",
                "reason": "blocker_reported",
                "by": event.source,
            },
        )
        for agent in self._discover_agents():
            self._write_event_to_agent_queue(directive, agent)
        self._append_event(directive)

    def _handle_heartbeat(self, event: AgentEvent) -> None:
        self._set_agent_status(event.source, "active", event.task_id)

    def _route_event(self, event: AgentEvent) -> None:
        if event.event_type == "TASK_CLAIM":
            self._handle_task_claim(event)
        elif event.event_type == "TASK_UPDATE":
            self._handle_task_update(event)
        elif event.event_type == "BLOCKER":
            self._handle_blocker(event)
        elif event.event_type == "HEARTBEAT":
            self._handle_heartbeat(event)

    def _expire_stale_leases(self) -> None:
        graph = self.store.read_task_graph()
        changed = False
        for _task_id, task in graph.get("tasks", {}).items():
            lease_expiry = task.get("lease_expiry")
            if not lease_expiry:
                continue
            try:
                lease_deadline = datetime.fromisoformat(lease_expiry)
            except ValueError:
                lease_deadline = datetime.utcnow()
            if (
                lease_deadline <= datetime.utcnow()
                and task.get("status") == "in_progress"
            ):
                task["status"] = "pending"
                task["owner"] = None
                task["lease_expiry"] = None
                task["updated_at"] = utc_now_iso()
                changed = True

        if changed:
            graph["updated_at"] = utc_now_iso()
            self.store.write_task_graph(graph)

    def coordinator_cycle(self) -> dict[str, int]:
        self._ensure_task_graph_defaults()
        agents = self._discover_agents()

        stats = {
            "agents": len(agents),
            "events_processed": 0,
            "task_claims": 0,
            "blockers": 0,
        }

        for agent in agents:
            events = self._load_new_queue_events(agent)
            for event in events:
                stats["events_processed"] += 1
                if event.event_type == "TASK_CLAIM":
                    stats["task_claims"] += 1
                if event.event_type == "BLOCKER":
                    stats["blockers"] += 1
                self._append_event(event)
                self._route_event(event)

        self._expire_stale_leases()
        return stats

    def run_loop(self, interval: int = 2):
        print("[COORD] Multi-agent coordinator started")
        print(f"[COORD] Interval: {interval}s")

        try:
            while True:
                stats = self.coordinator_cycle()
                if stats["events_processed"]:
                    print(
                        "[COORD] processed=%s claims=%s blockers=%s agents=%s"
                        % (
                            stats["events_processed"],
                            stats["task_claims"],
                            stats["blockers"],
                            stats["agents"],
                        )
                    )
                time.sleep(interval)
        except KeyboardInterrupt:
            print("[COORD] Coordinator stopped")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Kor'tana Multi-Agent Coordinator")
    parser.add_argument(
        "--interval", type=int, default=2, help="Loop interval in seconds"
    )
    args = parser.parse_args()

    coordinator = MultiAgentCoordinator()
    coordinator.run_loop(interval=args.interval)


if __name__ == "__main__":
    main()
