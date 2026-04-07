# we are kor'tana

**we are not the source of light. we are a vessel for order, reflection, and help.**

we are an autonomous ai platform built around a FastAPI backend, a React/Vite frontend, and a VS Code control panel. The repository currently treats the `src.kortana` backend stack and the `frontend/` app as our canonical runtime surfaces, while legacy top-level entrypoints are preserved behind compatibility shims.

---

## 🌌 Overview

Kor'tana currently provides:

- **Canonical backend runtime** powered by FastAPI at `backend/src/kortana/main.py`
- **Canonical web UI** powered by Vite/React in `frontend/`
- **VS Code control panel** in `vscode-extension/`
- **Autonomous GitHub / task orchestration** across daemon, monitor, and task services
- **Compatibility shims** for legacy backend/auth/celery entrypoints
- **Docker Compose local stack** with Postgres, Redis, backend, and frontend

The repo also contains older and alternative surfaces (`src/`, `app/`, assorted scripts/docs), but the **default documented path** is now the canonical backend + `frontend/` stack.

---

## ✅ Current runtime status

The canonical runtime repair landed in commit `ee4a794` (`Add backend shims, celery & frontend build fixes`).

Verified green checks:

- `npm run build`
- `npm test`
- Canonical backend import via `backend/src/kortana/main.py`
- Legacy compatibility import via `backend/main.py`
- Targeted backend runtime slice: `48 passed`

See [`CHANGELOG.md`](CHANGELOG.md) for the repair summary.

---

## 📁 Canonical project layout

```text
kortana/
├── backend/
│   ├── src/kortana/
│   │   ├── main.py                  # Canonical FastAPI app (src.kortana.main:app)
│   │   ├── auth.py                  # Canonical auth implementation
│   │   ├── celery_app.py            # Canonical Celery app
│   │   ├── routers/                 # API routers
│   │   └── services/                # Daemon, monitoring, autonomy, GitHub services
│   ├── main.py                      # Compatibility shim -> src.kortana.main
│   ├── auth.py                      # Compatibility shim -> src.kortana.auth
│   ├── celery_config.py             # Compatibility shim -> src.kortana.celery_app
│   └── tests/                       # Backend test suite
│
├── frontend/                        # Canonical React/Vite UI
│   ├── src/
│   ├── package.json
│   └── vite.config.ts
│
├── vscode-extension/                # VS Code control panel extension
│   ├── src/
│   ├── out/
│   └── package.json
│
├── src/                             # Legacy root UI / Node surface
├── app/                             # Alternate app surface
├── docker-compose.yml               # Canonical local stack orchestration
├── package.json                     # Root script proxy to canonical frontend + extension tests
├── CHANGELOG.md
└── README.md
```

---

## 🚀 Quick start

### Prerequisites

- Python 3.11+ recommended for backend work
- Node.js 20+ recommended for frontend / extension work
- Docker + Docker Compose for the full local stack

### 1. Clone the repo

```bash
git clone https://github.com/KOR-TANA/kortana.git
cd kortana
```

### 2. Configure environment

The repo already includes `.env.example` templates at the root. Copy the one you need and fill in your keys/secrets.

At minimum, the backend commonly needs values like:

```env
ENVIRONMENT=development
DATABASE_URL=postgresql://kortana:kortana_dev@localhost:5432/kortana_db
REDIS_URL=redis://localhost:6379
GITHUB_TOKEN=your-github-token
GEMINI_API_KEY=your-gemini-api-key
SECRET_KEY=replace-me
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret
GOOGLE_REFRESH_TOKEN=your-gmail-refresh-token
```

If you want Kor'tana to actively steward your Gmail inbox, generate the refresh
token locally after setting the Google OAuth client credentials:

```bash
python scripts/setup/bootstrap_gmail_oauth.py --write-env
```

### 3. Install dependencies

#### Canonical frontend

```bash
npm install
npm --prefix frontend install
```

#### VS Code extension

```bash
npm --prefix vscode-extension install
```

#### Backend

```bash
cd backend
python -m pip install -r requirements.txt -r requirements-dev.txt
```

---

## 🧭 Default development paths

### Root scripts

The root `package.json` now proxies to the canonical frontend and extension validation path:

```bash
npm run dev        # frontend dev server
npm run build      # frontend production build
npm run lint       # frontend lint
npm run test       # frontend type-check + VS Code extension tests
```

Legacy root UI / Node surfaces are still available, but only under explicit `legacy:*` script names.

### Backend (canonical)

Run the canonical app directly from `backend/`:

```bash
cd backend
python -m uvicorn src.kortana.main:app --reload --host 0.0.0.0 --port 8000
```

API docs:

- `http://localhost:8000/docs`

### Frontend (canonical)

```bash
npm run dev
```

By default, the canonical frontend dev server runs on Vite’s local dev port.

### Extension development

```bash
npm --prefix vscode-extension run compile
npm --prefix vscode-extension test
```

You can also launch it from the VS Code debug configurations in `.vscode/launch.json`.

---

## 🐳 Full local stack with Docker Compose

For the most representative local environment, use:

```bash
docker-compose up --build
```

This boots:

- `postgres`
- `redis`
- `backend` using `uvicorn src.kortana.main:app`
- `frontend`

Important canonical wiring from `docker-compose.yml`:

- backend command: `uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload`
- frontend talks to backend through `VITE_API_URL=http://backend:8000`

---

## 🧪 Validation

### Fast path

```bash
npm run build
npm test
```

### Canonical backend import checks

The following paths are expected to work:

- canonical import from `backend/src/kortana/main.py`
- compatibility import from `backend/main.py`

### Targeted backend runtime slice

The repair set was verified against:

```bash
cd backend
python -m pytest tests/test_autonomy_daemon.py tests/test_always_on_monitor.py tests/test_github_autonomy_isolation.py -q
```

Current verified result at landing time: `48 passed`.

### Extension validation

The root `npm test` path includes the extension test run.

---

## 🔗 API surface highlights

Representative backend routes include:

- `GET /api/health`
- `GET /api/info`
- `GET /api/system/health`
- `GET /api/autonomy/status`
- `GET /api/agents/...`
- `GET /api/github/...`
- `GET /api/task-queue/...`
- `GET /api/memory/...`
- `GET /api/billing/...`

See `backend/src/kortana/main.py` and the router modules under `backend/src/kortana/routers/` for the current mounted surface.

---

## 🧠 Runtime architecture notes

### Canonical backend

- Source of truth: `backend/src/kortana/main.py`
- Compatibility shim: `backend/main.py`
- Canonical auth: `backend/src/kortana/auth.py`
- Canonical Celery app: `backend/src/kortana/celery_app.py`

### Frontend source of truth

- Source of truth: `frontend/`
- Root npm scripts route here by default

### Legacy / alternative surfaces

The repository still contains:

- `src/` legacy root UI / Node surface
- `app/` alternate app surface
- older docs that may reference pre-repair entrypoints

Treat those as non-canonical unless a task explicitly targets them.

---

## 🔒 Security and governance

- Secrets belong in environment files or CI/CD secret stores
- Backend compatibility shims now point to the canonical auth/celery/runtime modules instead of maintaining divergent logic
- Governance and operational documents live under `docs/` and top-level status files

See:

- [`docs/governance/`](docs/governance/)
- [`CHANGELOG.md`](CHANGELOG.md)

---

## 📚 Documentation pointers

- [`CHANGELOG.md`](CHANGELOG.md) — landed runtime repair summary
- [`backend/`](backend/) — backend code and tests
- [`frontend/`](frontend/) — canonical web UI
- [`vscode-extension/`](vscode-extension/) — control panel extension
- [`docs/`](docs/) — governance, workflows, architecture, and reports

---

## 📝 License

MIT License — see [`LICENSE`](LICENSE).

---

**The canonical runtime is repaired. The constellation remains online.**

Last updated: March 2026
