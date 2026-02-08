from __future__ import annotations

import json
from pathlib import Path

from relays.agent_interface import AgentInterface
from relays.multi_agent_coordinator import MultiAgentCoordinator
from relays.protocol import parse_event_line


def _read_lines(path: Path) -> list[str]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as handle:
        return [line.rstrip("\n") for line in handle.readlines()]


def test_send_event_writes_to_coordinator_inbox(tmp_path: Path) -> None:
    agent = AgentInterface("alpha", project_root=str(tmp_path))
    ok = agent.send_event(
        event_type="TASK_CLAIM",
        task_id="task-1",
        target="coordinator",
        payload={"details": "starting"},
    )
    assert ok is True

    inbox = tmp_path / "queues" / "coordinator_in.txt"
    lines = _read_lines(inbox)
    assert lines
    parsed = parse_event_line(lines[-1])
    assert parsed is not None
    assert parsed.source == "alpha"
    assert parsed.event_type == "TASK_CLAIM"
    assert parsed.task_id == "task-1"


def test_check_for_directives_supports_structured_and_legacy(tmp_path: Path) -> None:
    agent = AgentInterface("alpha", project_root=str(tmp_path))

    directive_event = {
        "id": "evt-1",
        "timestamp": "2026-01-01T00:00:00+00:00",
        "source": "coordinator",
        "target": "alpha",
        "event_type": "DIRECTIVE",
        "payload": {"instruction": "pause_rebase"},
    }
    queue_path = tmp_path / "queues" / "alpha_in.txt"
    with open(queue_path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(directive_event) + "\n")
        handle.write("[00:00:00] DIRECTIVE: continue with task-1\n")

    messages = agent.get_new_messages()
    directives = agent.check_for_directives(messages=messages)
    assert "pause_rebase" in directives
    assert any("DIRECTIVE:" in entry for entry in directives)


def test_coordinator_claims_task_and_sends_ack(tmp_path: Path) -> None:
    alpha = AgentInterface("alpha", project_root=str(tmp_path))
    alpha.send_event(
        event_type="TASK_CLAIM",
        task_id="task-claim-1",
        target="coordinator",
        requires_ack=True,
    )

    coordinator = MultiAgentCoordinator(project_root=str(tmp_path))
    stats = coordinator.coordinator_cycle()
    assert stats["events_processed"] == 1
    assert stats["task_claims"] == 1

    graph = coordinator.store.read_task_graph()
    task = graph["tasks"]["task-claim-1"]
    assert task["owner"] == "alpha"
    assert task["status"] == "in_progress"

    events = alpha.get_new_events()
    ack_events = [event for event in events if event.event_type == "ACK"]
    assert ack_events
    assert ack_events[-1].payload.get("accepted") is True


def test_non_owner_task_update_is_rejected(tmp_path: Path) -> None:
    alpha = AgentInterface("alpha", project_root=str(tmp_path))
    beta = AgentInterface("beta", project_root=str(tmp_path))
    coordinator = MultiAgentCoordinator(project_root=str(tmp_path))

    alpha.send_event(
        event_type="TASK_CLAIM",
        task_id="task-owned",
        target="coordinator",
        requires_ack=True,
    )
    coordinator.coordinator_cycle()

    beta.send_event(
        event_type="TASK_UPDATE",
        task_id="task-owned",
        target="coordinator",
        requires_ack=True,
        payload={"status": "completed"},
    )
    coordinator.coordinator_cycle()

    graph = coordinator.store.read_task_graph()
    task = graph["tasks"]["task-owned"]
    assert task["owner"] == "alpha"
    assert task["status"] == "in_progress"

    beta_events = beta.get_new_events()
    beta_acks = [event for event in beta_events if event.event_type == "ACK"]
    assert beta_acks
    assert beta_acks[-1].payload.get("accepted") is False
    assert str(beta_acks[-1].payload.get("reason", "")).startswith("task_owned_by_")


def test_agent_queue_buffers_partial_lines(tmp_path: Path) -> None:
    agent = AgentInterface("alpha", project_root=str(tmp_path))
    queue_path = tmp_path / "queues" / "alpha_in.txt"
    event_line = (
        '{"id":"evt-1","timestamp":"2026-01-01T00:00:00+00:00","source":"coordinator",'
        '"target":"alpha","event_type":"DIRECTIVE","payload":{"instruction":"resume"}}'
    )

    with open(queue_path, "a", encoding="utf-8") as handle:
        handle.write(event_line[:-1])

    # Incomplete line should be buffered and not emitted yet.
    assert agent.get_new_messages() == []

    with open(queue_path, "a", encoding="utf-8") as handle:
        handle.write(event_line[-1] + "\n")

    messages = agent.get_new_messages()
    assert len(messages) == 1
    assert "DIRECTIVE" in messages[0]


def test_coordinator_inbox_buffers_partial_lines(tmp_path: Path) -> None:
    coordinator = MultiAgentCoordinator(project_root=str(tmp_path))
    inbox = tmp_path / "queues" / "coordinator_in.txt"
    event_line = (
        '{"id":"evt-2","timestamp":"2026-01-01T00:00:00+00:00","source":"alpha",'
        '"target":"coordinator","event_type":"TASK_CLAIM","task_id":"task-2","payload":{}}'
    )

    with open(inbox, "a", encoding="utf-8") as handle:
        handle.write(event_line[:-2])

    assert coordinator._load_new_inbox_events() == []

    with open(inbox, "a", encoding="utf-8") as handle:
        handle.write(event_line[-2:] + "\n")

    events = coordinator._load_new_inbox_events()
    assert len(events) == 1
    assert events[0].event_type == "TASK_CLAIM"
    assert events[0].task_id == "task-2"


def test_discover_agents_excludes_coordinator_name(tmp_path: Path) -> None:
    queues = tmp_path / "queues"
    logs = tmp_path / "logs"
    data = tmp_path / "data"
    queues.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    data.mkdir(parents=True, exist_ok=True)

    (queues / "coordinator_in.txt").write_text("", encoding="utf-8")
    (queues / "alpha_in.txt").write_text("", encoding="utf-8")
    (logs / "coordinator.log").write_text("", encoding="utf-8")
    (logs / "beta.log").write_text("", encoding="utf-8")
    (data / "agent_state.json").write_text(
        json.dumps(
            {
                "agents": {
                    "coordinator": {"status": "active"},
                    "gamma": {"status": "busy"},
                },
                "updated_at": "",
            }
        ),
        encoding="utf-8",
    )
    (data / "task_graph.json").write_text(
        json.dumps({"tasks": {}, "updated_at": ""}),
        encoding="utf-8",
    )

    coordinator = MultiAgentCoordinator(project_root=str(tmp_path))
    discovered = coordinator._discover_agents()

    assert "coordinator" not in discovered
    assert "alpha" in discovered
    assert "beta" in discovered
    assert "gamma" in discovered


def test_completion_keeps_agent_busy_when_other_task_active(tmp_path: Path) -> None:
    alpha = AgentInterface("alpha", project_root=str(tmp_path))
    coordinator = MultiAgentCoordinator(project_root=str(tmp_path))

    alpha.send_event(
        event_type="TASK_CLAIM",
        task_id="task-a",
        target="coordinator",
    )
    coordinator.coordinator_cycle()

    alpha.send_event(
        event_type="TASK_CLAIM",
        task_id="task-b",
        target="coordinator",
    )
    coordinator.coordinator_cycle()

    alpha.send_event(
        event_type="TASK_UPDATE",
        task_id="task-a",
        target="coordinator",
        payload={"status": "completed"},
    )
    coordinator.coordinator_cycle()

    agent_state = coordinator.store.read_agent_state()
    alpha_state = agent_state.get("agents", {}).get("alpha", {})
    assert alpha_state.get("status") == "busy"
    assert alpha_state.get("task_id") == "task-b"
