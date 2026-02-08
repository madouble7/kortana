#!/usr/bin/env python3
"""Real-time multi-agent coordinator for Kor'tana concurrent development."""

from __future__ import annotations

from collections import deque
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from relays.protocol import AgentEvent, append_text_line, parse_event_line, utc_now_iso
from relays.state_store import CoordinationStateStore


class MultiAgentCoordinator:
    """Coordinates task claims, leases, directives, and live state updates."""

    def __init__(self, project_root: str | None = None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent.parent
        )
        self.queues_dir = self.project_root / "queues"
        self.coordinator_inbox = self.queues_dir / "coordinator_in.txt"
        self.logs_dir = self.project_root / "logs"
        self.store = CoordinationStateStore(str(self.project_root))
        self._inbox_offset = 0
        self._inbox_remainder = ""
        self._seen_event_ids: set[str] = set()
        self._seen_order: deque[str] = deque()
        self._seen_limit = 5000
        self.lease_seconds = 120

        self.queues_dir.mkdir(parents=True, exist_ok=True)
        self.coordinator_inbox.touch(exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _discover_agents(self) -> list[str]:
        agents: set[str] = set()
        for queue_file in self.queues_dir.glob("*_in.txt"):
            name = queue_file.stem.replace("_in", "")
            if name != "coordinator":
                agents.add(name)
        for log_file in self.logs_dir.glob("*.log"):
            if log_file.stem != "coordinator":
                agents.add(log_file.stem)
        for agent_name in self.store.read_agent_state().get("agents", {}):
            if agent_name != "coordinator":
                agents.add(agent_name)
        return sorted(agents)

    def _queue_path(self, agent: str) -> Path:
        return self.queues_dir / f"{agent}_in.txt"

    def _write_event_to_agent_queue(self, event: AgentEvent, agent: str) -> None:
        queue_path = self._queue_path(agent)
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        queue_path.touch(exist_ok=True)
        append_text_line(queue_path, event.to_json_line())

    def _append_event(self, event: AgentEvent) -> None:
        self.store.append_event(event.to_dict())

    def _parse_iso_utc(self, value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _active_task_for_agent(
        self,
        graph: dict,
        agent: str,
        exclude_task_id: str | None = None,
    ) -> str | None:
        now = datetime.now(UTC)
        for task_id, task in graph.get("tasks", {}).items():
            if exclude_task_id and task_id == exclude_task_id:
                continue
            if task.get("owner") != agent:
                continue
            if str(task.get("status", "")).lower() != "in_progress":
                continue
            lease_expiry = task.get("lease_expiry")
            if lease_expiry:
                parsed = self._parse_iso_utc(str(lease_expiry))
                if parsed and parsed <= now:
                    continue
            return str(task_id)
        return None

    def _mark_seen(self, event_id: str) -> bool:
        if event_id in self._seen_event_ids:
            return False
        self._seen_event_ids.add(event_id)
        self._seen_order.append(event_id)
        # Keep seen-set bounded.
        while len(self._seen_order) > self._seen_limit:
            stale = self._seen_order.popleft()
            self._seen_event_ids.discard(stale)
        return True

    def _send_ack(self, event: AgentEvent, accepted: bool, reason: str = "") -> None:
        ack_event = AgentEvent.new(
            source="coordinator",
            target=event.source,
            event_type="ACK",
            task_id=event.task_id,
            payload={
                "ack_for_event_id": event.id,
                "accepted": accepted,
                "reason": reason,
            },
        )
        self._write_event_to_agent_queue(ack_event, event.source)
        self._append_event(ack_event)

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
        changed = False
        if "tasks" not in graph:
            graph["tasks"] = {}
            changed = True
        if "updated_at" not in graph:
            graph["updated_at"] = utc_now_iso()
            changed = True
        if changed:
            self.store.write_task_graph(graph)

    def _load_new_inbox_events(self) -> list[AgentEvent]:
        if not self.coordinator_inbox.exists():
            return []

        with open(self.coordinator_inbox, encoding="utf-8") as f:
            size = self.coordinator_inbox.stat().st_size
            if self._inbox_offset > size:
                self._inbox_offset = 0
                self._inbox_remainder = ""
            f.seek(self._inbox_offset)
            chunk = f.read()
            self._inbox_offset = f.tell()
        if not chunk and not self._inbox_remainder:
            return []

        merged = f"{self._inbox_remainder}{chunk}"
        lines = merged.splitlines()
        if merged and not merged.endswith(("\n", "\r")):
            self._inbox_remainder = lines.pop() if lines else merged
        else:
            self._inbox_remainder = ""

        events: list[AgentEvent] = []
        for line in lines:
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
            if event.requires_ack:
                self._send_ack(event, accepted=False, reason="missing_task_id")
            return

        self._create_task_if_missing(event.task_id)
        graph = self.store.read_task_graph()
        task = graph["tasks"][event.task_id]

        lease_expiry = task.get("lease_expiry")
        lease_valid = False
        if lease_expiry:
            parsed_expiry = self._parse_iso_utc(str(lease_expiry))
            lease_valid = bool(parsed_expiry and parsed_expiry > datetime.now(UTC))

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
            if event.requires_ack:
                self._send_ack(event, accepted=False, reason="task_already_leased")
            return

        task["owner"] = event.source
        task["status"] = "in_progress"
        task["lease_expiry"] = (
            datetime.now(UTC) + timedelta(seconds=self.lease_seconds)
        ).isoformat()
        task["updated_at"] = utc_now_iso()
        graph["updated_at"] = utc_now_iso()
        self.store.write_task_graph(graph)
        self._set_agent_status(event.source, "busy", event.task_id)
        if event.requires_ack:
            self._send_ack(event, accepted=True)

    def _handle_task_update(self, event: AgentEvent) -> None:
        if not event.task_id:
            if event.requires_ack:
                self._send_ack(event, accepted=False, reason="missing_task_id")
            return

        self._create_task_if_missing(event.task_id)
        graph = self.store.read_task_graph()
        task = graph["tasks"][event.task_id]
        owner = task.get("owner")
        if owner and owner != event.source and task.get("status") == "in_progress":
            if event.requires_ack:
                self._send_ack(
                    event,
                    accepted=False,
                    reason=f"task_owned_by_{owner}",
                )
            return

        new_status = str(
            event.payload.get("status") if event.payload else "in_progress"
        )
        task["status"] = new_status
        if not task.get("owner"):
            task["owner"] = event.source
        task["updated_at"] = utc_now_iso()

        if new_status.lower() in {"done", "completed", "merged"}:
            task["lease_expiry"] = None
            active_task = self._active_task_for_agent(
                graph,
                event.source,
                exclude_task_id=event.task_id,
            )
            if active_task:
                self._set_agent_status(event.source, "busy", active_task)
            else:
                self._set_agent_status(event.source, "idle", None)
        else:
            task["lease_expiry"] = (
                datetime.now(UTC) + timedelta(seconds=self.lease_seconds)
            ).isoformat()
            self._set_agent_status(event.source, "busy", event.task_id)

        graph["updated_at"] = utc_now_iso()
        self.store.write_task_graph(graph)
        if event.requires_ack:
            self._send_ack(event, accepted=True)

    def _handle_blocker(self, event: AgentEvent) -> None:
        if not event.task_id:
            if event.requires_ack:
                self._send_ack(event, accepted=False, reason="missing_task_id")
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
        if event.requires_ack:
            self._send_ack(event, accepted=True)

    def _handle_heartbeat(self, event: AgentEvent) -> None:
        heartbeat_task_id = event.task_id
        if heartbeat_task_id is None:
            current_agents = self.store.read_agent_state().get("agents", {})
            current = current_agents.get(event.source, {})
            if str(current.get("status", "")).lower() == "busy":
                heartbeat_task_id = current.get("task_id")
        self._set_agent_status(event.source, "active", heartbeat_task_id)
        if event.requires_ack:
            self._send_ack(event, accepted=True)

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
        owners_to_refresh: set[str] = set()
        for task_id, task in graph.get("tasks", {}).items():
            lease_expiry = task.get("lease_expiry")
            if not lease_expiry:
                continue
            lease_deadline = self._parse_iso_utc(str(lease_expiry))
            if lease_deadline is None:
                lease_deadline = datetime.now(UTC)
            if (
                lease_deadline <= datetime.now(UTC)
                and task.get("status") == "in_progress"
            ):
                previous_owner = task.get("owner")
                task["status"] = "pending"
                task["owner"] = None
                task["lease_expiry"] = None
                task["updated_at"] = utc_now_iso()
                changed = True
                if previous_owner:
                    owners_to_refresh.add(str(previous_owner))

        if changed:
            graph["updated_at"] = utc_now_iso()
            self.store.write_task_graph(graph)
            for owner in owners_to_refresh:
                active_task = self._active_task_for_agent(
                    graph,
                    owner,
                    exclude_task_id=None,
                )
                if active_task:
                    self._set_agent_status(owner, "busy", active_task)
                else:
                    self._set_agent_status(owner, "idle", None)

    def coordinator_cycle(self) -> dict[str, int]:
        self._ensure_task_graph_defaults()
        agents = self._discover_agents()

        stats = {
            "agents": len(agents),
            "events_processed": 0,
            "events_skipped": 0,
            "task_claims": 0,
            "blockers": 0,
        }

        events = self._load_new_inbox_events()
        for event in events:
            if not self._mark_seen(event.id):
                stats["events_skipped"] += 1
                continue
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
