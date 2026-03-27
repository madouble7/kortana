# KOR'TANA Devcontainer Notes

This devcontainer attaches VS Code to a dedicated `devcontainer` service while reusing the repository's existing Docker Compose stack.

## What starts

The devcontainer configuration starts these services:

- `postgres`
- `redis`
- `devcontainer`

The main backend/UI services are intentionally not auto-started inside the devcontainer so you can choose whether to run them via tasks, debug profiles, or Compose.

## Port forwarding

Forwarded ports include:

- `8000` — backend API
- `3000` — compose frontend
- `3001` — Grafana
- `5173` — root Vite UI
- `5174` — `frontend/` Vite UI
- `5432` — PostgreSQL
- `6379` — Redis
- `8080` — cAdvisor
- `9090` — Prometheus
- `9093` — Alertmanager
- `3100` — Loki

## Bootstrap behavior

On first create, the container installs:

- backend Python requirements
- backend Python dev requirements
- root npm dependencies
- `frontend/` npm dependencies
- `vscode-extension/` npm dependencies

## Recommended flow

1. Reopen the repo in the devcontainer.
2. Run `backend: dev` or a KOR'TANA debug compound.
3. Start a UI task (`root: ui dev` or `frontend: ui dev`).
4. Start `monitoring: up` when you want Grafana/Prometheus online.

## Important environment note

The backend configuration does not automatically discover a repo-root `.env` unless VS Code or the process explicitly injects it. This workspace does that for debug and editor workflows, but if you run commands manually inside the container, keep that behavior in mind.
