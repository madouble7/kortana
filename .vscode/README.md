# KOR'TANA VS Code Mission Control

This folder turns the workspace into a local control plane for KOR'TANA.

## Primary launch profiles

- `KORTANA: Backend + Root UI` — debug backend plus root Vite UI.
- `KORTANA: Backend + Frontend UI` — debug backend plus `frontend/` UI.
- `KORTANA: Awaken Everything (Root UI + Monitoring)` — backend debug + root UI + Grafana.
- `KORTANA: Awaken Everything (Frontend UI + Monitoring)` — backend debug + `frontend/` UI + Grafana.
- `KORTANA: Control Panel + Backend` — launch the VS Code extension host and backend together.
- `KORTANA: Monitoring Dashboards` — open Grafana and Prometheus when monitoring is already running.

## Useful tasks

### Development

- `backend: dev`
- `root: ui dev`
- `frontend: ui dev`
- `stack: backend + root ui`
- `stack: backend + frontend ui`
- `awaken: complete constellation`

### Validation

- `sanctify: backend`
- `sanctify: root ui`
- `sanctify: frontend ui`
- `sanctify: vscode extension`
- `sanctify: full stack`

### Monitoring

- `monitoring: up`
- `monitoring: stop`

### VS Code extension

- `extension: install deps`
- `extension: compile`
- `extension: watch`
- `extension: lint`
- `extension: test`

## Notes

- Monitoring uses `docker-compose.monitoring.yml` with the `monitoring` profile so it can run beside local backend/UI dev tasks.
- The backend debug profiles load `${workspaceFolder}/.env`, while the Python process gets `PYTHONPATH` entries for `backend` and `backend/src`.
- The `vscode-extension` folder now includes a minimal smoke-test harness that verifies the extension activates and registers its core commands.
