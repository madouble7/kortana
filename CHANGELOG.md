# Changelog

All notable changes to this project will be documented in this file.

## [2026-03-27] - Canonical runtime repair

Commit: `ee4a794` — `Add backend shims, celery & frontend build fixes`

### Added

- Compatibility shims for legacy backend entrypoints:
  - `backend/main.py`
  - `backend/auth.py`
  - `backend/routers/auth.py`
  - `backend/celery_config.py`
- Restored canonical Celery app module at `backend/src/kortana/celery_app.py`

### Changed

- Root npm scripts now target the canonical `frontend/` application instead of dead `client/` paths
- VS Code launch configurations now label legacy root UI surfaces more clearly and point the canonical frontend launch URL at the active dev server
- Legacy backend import paths now forward into `src.kortana` instead of maintaining divergent runtime behavior

### Fixed

- Repaired the canonical runtime path around `backend/src/kortana/main.py`
- Removed duplicate SPA runtime-config injection in `backend/src/kortana/main.py`
- Fixed frontend build configuration in `frontend/vite.config.ts`
- Fixed Tailwind config export format in `frontend/tailwind.config.cjs`
- Fixed frontend type-check blockers in:
  - `frontend/src/components/Dashboard.tsx`
  - `frontend/src/components/SystemStatus.tsx`
- Fixed repo-root detection in `backend/src/kortana/services/github_autonomy_service.py` so valid `backend/...` file changes are preserved during plan sanitization

### Verified

- `npm run build` passes
- `npm test` passes
- Canonical backend import via `backend/src/kortana/main.py` passes
- Legacy compatibility import via `backend/main.py` passes
- Targeted backend runtime slice passes:
  - `backend/tests/test_autonomy_daemon.py`
  - `backend/tests/test_always_on_monitor.py`
  - `backend/tests/test_github_autonomy_isolation.py`
  - Result: `48 passed`
