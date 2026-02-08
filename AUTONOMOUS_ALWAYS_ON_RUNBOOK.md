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
