# Autonomous Deployment Guide

This is the current deployment model for Kor'tana.

## Service Topology

Kor'tana is deployed as split services:

- `web`: FastAPI API and static frontend host
- `daemon`: autonomous loop worker (`python -m src.kortana.daemon_worker`)
- `redis`: cache / rate-limit / queue backend
- `postgres`: primary persistence

The web process does not host the daemon unless `KORTANA_DAEMON_IN_PROCESS=true` is set explicitly.

## Required Environment

Common variables:

- `ENVIRONMENT=production`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
- `SESSION_SALT`
- `HEARTBEAT_TOKEN`
- `KORTANA_BACKEND_URL`
- `KORTANA_FRONTEND_URL`
- `GITHUB_TOKEN`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`

Web service values:

- `KORTANA_DAEMON_IN_PROCESS=false`
- `AUTONOMY_DAEMON_ENABLED=false`

Daemon service values:

- `KORTANA_DAEMON_IN_PROCESS=false`
- `AUTONOMY_DAEMON_ENABLED=true`

## Railway

Expected services:

- web service: deploys `backend/railway.json`
- daemon service: uses the same repo and `backend/Procfile` command `daemon`

GitHub Actions secrets:

- `RAILWAY_TOKEN`
- `RAILWAY_WEB_SERVICE_NAME` or legacy `RAILWAY_SERVICE_NAME`
- `RAILWAY_DAEMON_SERVICE_NAME`
- `KORTANA_BACKEND_URL`
- `VERCEL_TOKEN` if the frontend is deployed separately

## Render

`render.yaml` now declares:

- `kortana-api` as the web service
- `kortana-daemon` as the worker service

## Docker Compose

`docker-compose.prod.yml` now runs:

- `backend`
- `daemon`
- `postgres`
- `redis`

## Health Verification

Web health:

- `GET /api/health`

Daemon health:

- `GET /api/daemon/status`

In split deployments, the route reports:

- `deployment_mode=external`
- `control_available=false`
- `external_daemon.alive=true|false`

This is the canonical web-visible signal for whether the autonomous worker is still cycling.

## Local Smoke Check

```powershell
cd C:\kortana\backend
python -m pytest tests/test_daemon_router.py tests/test_main.py tests/test_health.py -q
cd C:\kortana\frontend
npm run lint
npm run type-check
npm run build
```
