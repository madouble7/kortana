# Kor'tana Multi-Agent Coordination Guide

This guide defines the real-time protocol all autonomous/coding agents must follow when working concurrently in the same repo.

## Why this exists

Concurrent edits without ownership control cause:

- conflicting file writes
- duplicated work
- stale task ownership
- low signal for operators

The coordination mesh solves this with task and file claims plus heartbeat-based stale cleanup.

## Core tools

- `scripts/agent_mesh.py`: register, heartbeat, claim/release tasks and files
- `scripts/monitor_agent_mesh.py`: live operator dashboard
- `state/agent_mesh_state.json`: shared state file

## Mandatory protocol

1. Register on startup.
2. Claim task before editing any file.
3. Heartbeat every 30-60 seconds while task is active.
4. Release task on completion/failure/abandon.
5. Unregister on shutdown.

## Command templates

Register:

```bat
python scripts/agent_mesh.py register --agent <agent-id> --role <coding|planning|testing|monitoring> --branch <branch-name>
```

Create task:

```bat
python scripts/agent_mesh.py add-task --task-id <task-id> --title "<short title>" --description "<details>" --priority 80 --file <path>
```

Claim task:

```bat
python scripts/agent_mesh.py claim-task --agent <agent-id> --task-id <task-id>
```

Heartbeat:

```bat
python scripts/agent_mesh.py heartbeat --agent <agent-id> --status busy --task-id <task-id>
```

Release task:

```bat
python scripts/agent_mesh.py release-task --agent <agent-id> --task-id <task-id> --outcome completed --note "<summary>"
```

Unregister:

```bat
python scripts/agent_mesh.py unregister --agent <agent-id> --reason session_end
```

## Real-time operations

One-shot status:

```bat
python scripts/agent_mesh.py status
```

Live dashboard:

```bat
python scripts/monitor_agent_mesh.py --interval 5
```

Recommended next task for an agent:

```bat
python scripts/agent_mesh.py recommend --agent <agent-id>
```

Suggested assignments:

```bat
python scripts/agent_mesh.py assignments --max 10
```

## Conflict and stale-claim handling

- If task claim fails with file conflicts, do not edit; pick another task or wait.
- If ownership appears stale, run:

```bat
python scripts/agent_mesh.py sweep
```

- Do not use `--force` file claim unless you are the operator and conflict ownership is confirmed stale.
