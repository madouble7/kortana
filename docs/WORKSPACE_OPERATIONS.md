# KOR'TANA Workspace Operations

This document is the canonical operator manual for running KOR'TANA from VS Code.

## Control surfaces

KOR'TANA has four main control layers in this repository:

1. `C:\Users\madou\AppData\Roaming\Code\User\settings.json` — global editor baseline.
2. `.vscode/settings.json` — KOR'TANA-specific workspace tuning.
3. `.vscode/tasks.json` — run, validate, awaken, and monitoring rituals.
4. `.vscode/launch.json` — debug compounds for backend, UI surfaces, monitoring, and the VS Code extension.

Supporting operator notes live in:

- `.vscode/README.md`
- `.devcontainer/README.md`

## Primary workflows

### Awaken the local constellation

Use one of these debug compounds in **Run and Debug**:

- `KORTANA: Backend + Root UI`
- `KORTANA: Backend + Frontend UI`
- `KORTANA: Awaken Everything (Root UI + Monitoring)`
- `KORTANA: Awaken Everything (Frontend UI + Monitoring)`

Or use tasks directly:

- `stack: backend + root ui`
- `stack: backend + frontend ui`
- `awaken: complete constellation`

### Sanctify before shipping

Validation tasks are grouped under the `sanctify:` prefix:

- `sanctify: backend`
- `sanctify: root ui`
- `sanctify: frontend ui`
- `sanctify: vscode extension`
- `sanctify: full stack`

These orchestrate linting, type-checking, build steps, backend tests, and the extension smoke tests.

### Observe the system

Monitoring is isolated from the main dev stack through `docker-compose.monitoring.yml` and the `monitoring` profile.

Useful tasks:

- `monitoring: up`
- `monitoring: stop`

Useful launch profiles:

- `Monitoring: Grafana`
- `Monitoring: Prometheus`
- `KORTANA: Monitoring Dashboards`

Default ports:

- `8000` — backend API
- `3001` — Grafana
- `9090` — Prometheus
- `9093` — Alertmanager
- `8080` — cAdvisor
- `3100` — Loki

## VS Code extension workflow

The `vscode-extension/` project now includes a minimal smoke-test harness.

Available tasks:

- `extension: install deps`
- `extension: compile`
- `extension: watch`
- `extension: lint`
- `extension: test`

Primary debug compound:

- `KORTANA: Control Panel + Backend`

What the smoke tests verify:

- the extension loads in an Extension Host
- the extension activates
- the core commands are both contributed and registered

## Environment behavior

The backend config does **not** automatically discover a repo-root `.env` by walking above the `backend/` directory.

That means:

- VS Code debug/task settings explicitly inject `${workspaceFolder}/.env`
- manual shell commands may need environment variables exported or a `backend/.env` present

## Devcontainer workflow

The devcontainer starts:

- `postgres`
- `redis`
- `devcontainer`

It does **not** automatically start the backend or UI servers. That is intentional so you can choose between tasks, debug compounds, and Compose workflows.

Recommended order inside the container:

1. Reopen in container.
2. Run `backend: dev` or a KOR'TANA debug compound.
3. Run one UI task.
4. Run `monitoring: up` if you want observability online.

## Suggested operator rhythm

For everyday development:

1. Use `KORTANA: Backend + Root UI` or `KORTANA: Backend + Frontend UI`.
2. Run `sanctify: backend` or `sanctify: full stack` before committing.
3. Use `KORTANA: Monitoring Dashboards` when inspecting live system behavior.

For extension work:

1. Run `extension: install deps` once.
2. Run `extension: watch` during active development.
3. Launch `KORTANA: Control Panel + Backend`.
4. Run `extension: test` before changing extension packaging or commands.

## Troubleshooting

### Backend looks offline in the extension

- Confirm something is serving on `http://localhost:8000/api/health`.
- If you started the backend manually, ensure the correct environment variables are loaded.

### Monitoring won’t start

- Check whether Grafana (`3001`) or Prometheus (`9090`) are already in use.
- Use `monitoring: stop` before restarting the monitoring profile.

### Extension tests fail immediately

- Run `extension: install deps` first.
- Run `extension: compile` if `out/` is stale.
- Ensure contributed command IDs in `vscode-extension/package.json` still match registrations in `src/extension.ts`.
