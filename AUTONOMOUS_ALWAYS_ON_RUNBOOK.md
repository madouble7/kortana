# Kor'tana Always-On Autonomous Monitoring Runbook

## What changed

`autonomous_monitor_simple.py` now uses a stable workload model:

- **Persistent supervised monitors**
  - `file_system_monitor.py`
  - `monitor_autonomous_activity.py` (API-gated)
  - `monitor_autonomous_development.py` (API-gated)
  - `monitor_autonomous_intelligence.py` (API-gated)
- **Periodic one-shot checks** (not treated as daemon failures)
  - `check_server.py` (60s)
  - `status_check.py` (120s, API-gated)
  - `autonomous_monitor.py` (600s)

Additional hardening:

- Script path discovery across root/`scripts`/`src`
- API health preflight + deferred startup for API-dependent monitors
- Child stderr logging to `logs/autonomous_children/*.stderr.log`
- UTF-8 child-process env (`PYTHONUTF8=1`, `PYTHONIOENCODING=utf-8`) for Windows cp1252 safety

## Correct startup order

1. Stop any existing stale monitor process (old in-memory version):

```bat
taskkill /F /IM python.exe
```

1. Start API server (if desired for API-based monitors):

```bat
python -m uvicorn src.kortana.main:app --host 127.0.0.1 --port 8000
```

1. In another terminal, start always-on monitor:

```bat
python autonomous_monitor_simple.py
```

## Expected behavior

- Without API: file-system monitor runs; API monitors stay **deferred** (not failed/thrashing).
- With API up: deferred API monitors auto-start on health cycle.
- One-shot scripts run on their schedule and do not create daemon restart storms.

## Debugging quick checks

- Main daemon log:
  - `autonomous_monitor_simple.log`
- Child stderr logs:
  - `logs/autonomous_children/*.stderr.log`

If a persistent child exits repeatedly, check its stderr file first.

## Real-Time Multi-Agent Coordination

Kor'tana now supports a filesystem-backed coordination mesh for concurrent agents.

### Mesh components

- Coordination core:
  - `src/kortana/core/agent_mesh.py`
- Operator/agent CLI:
  - `scripts/agent_mesh.py`
- Live dashboard monitor:
  - `scripts/monitor_agent_mesh.py`

`autonomous_monitor_simple.py` now supervises `monitor_agent_mesh.py` as a persistent monitor.

### Agent operating protocol (required for all concurrent agents)

1. Register once at session start:

```bat
python scripts/agent_mesh.py register --agent agent-coding-1 --role coding --branch feature/my-work
```

1. Send heartbeats every 30-60 seconds while working:

```bat
python scripts/agent_mesh.py heartbeat --agent agent-coding-1 --status busy --task-id task-123
```

1. Claim task ownership before coding:

```bat
python scripts/agent_mesh.py claim-task --agent agent-coding-1 --task-id task-123
```

1. If task has no mesh task entry yet, add then claim:

```bat
python scripts/agent_mesh.py add-task --task-id task-123 --title "Refactor model router" --description "..." --priority 80 --file src/kortana/model_router.py
python scripts/agent_mesh.py claim-task --agent agent-coding-1 --task-id task-123
```

1. Release task and claims at completion:

```bat
python scripts/agent_mesh.py release-task --agent agent-coding-1 --task-id task-123 --outcome completed --note "All checks green"
```

1. Unregister when done:

```bat
python scripts/agent_mesh.py unregister --agent agent-coding-1 --reason "session_end"
```

### Live supervision commands

- One-shot status:

```bat
python scripts/agent_mesh.py status
```

- Full raw state:

```bat
python scripts/agent_mesh.py show --json
```

- Suggested next task for one agent:

```bat
python scripts/agent_mesh.py recommend --agent agent-coding-1
```

- Suggested assignments across active agents:

```bat
python scripts/agent_mesh.py assignments --max 10
```

- Start live dashboard loop:

```bat
python scripts/monitor_agent_mesh.py --interval 5
```

### Stale ownership recovery

If an agent crashes or stops heartbeating, stale claims are auto-cleaned by sweep cycles.
Manual cleanup:

```bat
python scripts/agent_mesh.py sweep
```
