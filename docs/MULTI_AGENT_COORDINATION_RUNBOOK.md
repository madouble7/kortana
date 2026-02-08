# Kor'tana Multi-Agent Real-Time Coordination Runbook

## Overview

This runbook describes the new concurrent multi-agent control stack:

- `relays/protocol.py` - structured event schema (`TASK_CLAIM`, `TASK_UPDATE`, `BLOCKER`, `HEARTBEAT`, etc.)
- `relays/state_store.py` - shared coordination state in `data/`
- `relays/multi_agent_coordinator.py` - real-time lease + directive loop
- `relays/agent_interface.py` - structured + legacy agent communication interface
- `relays/master_orchestrator.py` - startup entrypoint including coordinator

## Shared state artifacts

- `data/agent_state.json`
  - live per-agent status (`active`, `busy`, `idle`), task ownership, heartbeat
- `data/task_graph.json`
  - task ownership, status transitions, lease expiry, blocker state
- `data/coordination_events.jsonl`
  - append-only event stream for traceability and replay

## Startup (recommended order)

From repo root:

```bat
python relays\master_orchestrator.py
```

This launches:

1. relay orchestrator
2. multi-agent coordinator
3. claude worker
4. flash worker
5. weaver worker

## Event protocol usage (for agents)

Use `AgentInterface` helpers:

- `send_event(event_type=..., target=..., task_id=..., payload=...)`
- `heartbeat(task_id=..., details=...)`
- `claim_task(task_id=..., details=...)`
- `update_task_status(task_id=..., status=..., details=..., progress=...)`

Example statuses for `TASK_UPDATE` payload:

- `in_progress`
- `blocked`
- `completed`

## Lease + conflict behavior

- Coordinator assigns task lease on `TASK_CLAIM`.
- Default lease TTL: 120s.
- If task is leased by another active owner, coordinator returns a `DIRECTIVE` with `claim_denied` reason.
- Blockers trigger broadcast `DIRECTIVE` events requesting replanning.
- Expired in-progress leases are reset to `pending`.

## Operational checks

1. Check coordinator output logs for cycle processing.
2. Inspect state files under `data/` for live ownership/health.
3. Tail `data/coordination_events.jsonl` for event-level debugging.

## Manual recovery

If coordination deadlocks or stale tasks persist:

1. Stop orchestrator.
2. Review `task_graph.json` for stale owners/leases.
3. Remove or adjust stale tasks manually.
4. Restart orchestrator.

## Safety notes

- Keep worker tasks module-scoped to reduce collision probability.
- Require `TASK_CLAIM` before edits.
- Ensure periodic heartbeats from each worker.
- Prefer structured event envelopes over free-form messages for routability.
