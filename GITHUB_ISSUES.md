# Kor'tana Autonomous Development Issues

> Copy these as GitHub Issues or drop into Copilot jumpstart prompts to accelerate autonomous capabilities.

---

## Issue 1: Scaffold FastAPI Backend Heartbeat

**Title:** `feat: scaffold FastAPI backend with health check and service routers`

**Description:**

Add a backend/ FastAPI service with main.py, routers for gemini, memory, agents, and a /api/health route. Include requirements.txt, uvicorn start script, and Dockerfile. Wire src/services/apiService.ts to point at this backend in dev.

**Acceptance Criteria:**
- [ ] `backend/main.py` starts on `localhost:8000` with FastAPI
- [ ] `/api/health` returns `{"status": "alive", "message": "..."}` with 200 OK
- [ ] `backend/routers/gemini.py`, `memory.py`, `agents.py` mounted at `/api/gemini/*`, `/api/memory/*`, `/api/agents/*`
- [ ] `backend/requirements.txt` includes fastapi, uvicorn, google-generativeai, pydantic
- [ ] `Dockerfile` builds backend and exposes port 8000
- [ ] `npm run start:backend` script in package.json runs uvicorn
- [ ] `src/services/apiService.ts` defaults to `http://localhost:8000` in dev, `process.env.VITE_API_URL` in prod
- [ ] Health check responds within 200ms

**Labels:** `backend`, `infra`, `autonomous`

**Assignee:** Copilot / Automated

---

## Issue 2: Automate Cloud Run Deploy via GitHub Actions

**Title:** `ci/cd: automate Cloud Run deployment with OIDC and secret rotation`

**Description:**

Create .github/workflows/deploy-backend.yml that builds the backend Docker image, pushes to Artifact Registry, and deploys to Cloud Run using OIDC. Pull GEMINI_API_KEY and other secrets from repo settings.

**Acceptance Criteria:**
- [ ] Workflow triggers on push to `main` or manual `workflow_dispatch`
- [ ] Docker image built for `backend/` directory
- [ ] Image tagged with git SHA and pushed to `us-west1-docker.pkg.dev`
- [ ] Cloud Run service `kortana-backend` updated with new image
- [ ] Secrets injected: `GEMINI_API_KEY`, `GOOGLE_DRIVE_API_KEY`, `GOOGLE_PROJECT_ID`
- [ ] OIDC authentication used (no service account keys in repo)
- [ ] Workflow fails gracefully if deployment fails
- [ ] Health check endpoint verified post-deployment
- [ ] Deployment status logged to `logs/deployments/*.md`

**Workflow File:** `.github/workflows/deploy-backend.yml`

**Labels:** `ci/cd`, `cloud`, `autonomous`

**Assignee:** Copilot / Automated

---

## Issue 3: Implement Autonomous Task Queue & Branch Creation

**Title:** `feat: autonomous task queue with auto-branching and stub commits`

**Description:**

Build `src/services/taskQueue.ts` + `AutonomousCoder.tsx` that read tasks from COVENANT_INDEX.md (front-matter block), auto-create `feature/*` branches via GitHub API, and push stub commits for each task.

**Acceptance Criteria:**
- [ ] `taskQueue.ts` exports `AutonomousTaskManager` class
- [ ] `AutonomousTaskManager` parses YAML/TOML front-matter from COVENANT_INDEX.md
- [ ] Each task triggers:
  - [ ] Branch creation: `feature/{task_id}-{slugified_name}`
  - [ ] Stub commit: `feat: {task_name}` with placeholder code
  - [ ] Branch pushed to origin
- [ ] `AutonomousCoder.tsx` displays task queue UI with:
  - [ ] List of pending tasks
  - [ ] "Create Branch" button per task
  - [ ] Status indicator (pending, in_progress, completed)
- [ ] GitHub API authentication via stored PAT or OIDC
- [ ] Error handling for branch conflicts (auto-suffix with timestamp)
- [ ] Logging to `logs/autonomy/task-queue.md`

**Components:**
- `src/services/taskQueue.ts`
- `src/components/AutonomousCoder.tsx`
- Update `COVENANT_INDEX.md` with task front-matter schema

**Labels:** `autonomous`, `workflow`, `github-api`

**Assignee:** Copilot / Automated

---

## Issue 4: Add Daily Autonomy Heartbeat Log

**Title:** `feat: daily autonomy sync with automated status logging`

**Description:**

Create `DailySyncCard.tsx` that posts a daily summary (date, status, last deployment, metrics) into `logs/daily/`. Hook it to a `daily-sync.yml` workflow that commits the file and updates COVENANT_INDEX.md.

**Acceptance Criteria:**
- [ ] `DailySyncCard.tsx` component displays:
  - [ ] Current date
  - [ ] Last deployment timestamp
  - [ ] Task queue status (pending/completed count)
  - [ ] Backend health status
  - [ ] Metrics snapshot (commits today, PRs open, branches active)
- [ ] Daily sync function writes to `logs/daily/{YYYY-MM-DD}.md` with format:
  ```
  # Daily Sync - {DATE}
  - Status: alive
  - Last Deploy: {timestamp}
  - Tasks Completed: {count}
  - Metrics: {...}
  ```
- [ ] `.github/workflows/daily-sync.yml` triggers at 00:00 UTC
- [ ] Workflow commits log file to repo
- [ ] Workflow updates COVENANT_INDEX.md with latest sync time
- [ ] Graceful failure if no activity (don't create empty logs)
- [ ] Logs indexed in COVENANT_INDEX.md

**Files:**
- `src/components/DailySyncCard.tsx`
- `src/services/dailySync.ts`
- `.github/workflows/daily-sync.yml`
- `logs/daily/` directory

**Labels:** `autonomous`, `logging`, `workflow`

**Assignee:** Copilot / Automated

---

## Issue 5: VS Code Extension for AI Studio + Deploy Page

**Title:** `feat: VS Code extension with AI Studio and Cloud Run deploy page WebViews`

**Description:**

In `vscode-extension/`, scaffold a simple extension that opens AI Studio and the Cloud Run deploy page inside WebView panels, plus a command to run `node scripts/unseal-kortana.js` (Puppeteer auto-elevation).

**Acceptance Criteria:**
- [ ] Extension manifest includes commands:
  - [ ] `kortana.openAIStudio` → opens AI Studio in WebView
  - [ ] `kortana.openDeployPage` → opens Cloud Run deploy page in WebView
  - [ ] `kortana.unsealRuntime` → runs Puppeteer script to auto-enter "I AM"
- [ ] WebView panels load iframes with CORS handling
- [ ] Extension contributes to activity bar (icon + "Kor'tana" panel)
- [ ] `scripts/unseal-kortana.js` uses Puppeteer to:
  - [ ] Navigate to Cloud Run URL
  - [ ] Type "I AM" in elevation field
  - [ ] Click unseal button
  - [ ] Close browser after unsealing
- [ ] Extension reports unseal success/failure to user
- [ ] Local dev mode checks `http://localhost:3000`, prod checks Cloud Run URL
- [ ] Packaged as `.vsix` for local install

**Files:**
- `vscode-extension/package.json`
- `vscode-extension/src/extension.ts`
- `vscode-extension/src/webview.ts`
- `scripts/unseal-kortana.js`

**Dependencies:** puppeteer, vscode API

**Labels:** `vscode`, `extension`, `ui`

**Assignee:** Copilot / Automated

---

## Issue 6: Integrate GitHub Issue Analyzer with Backend

**Title:** `feat: connect GitHubIssueAnalyzer to backend Gemini analysis endpoint`

**Description:**

Extend `GitHubIssueAnalyzer.tsx` so "Analyze with Kor'tana" calls `POST /api/github/analyze`. Implement the backend route to forward issue text to geminiService.ts and return the analysis.

**Acceptance Criteria:**
- [ ] Frontend: `GitHubIssueAnalyzer.tsx` sends issue/PR data to backend:
  - [ ] POST to `{API_URL}/api/github/analyze`
  - [ ] Payload: `{ title, body, issue_number, type: "issue" | "pr" }`
- [ ] Backend: `backend/routers/github.py` implements `/analyze` endpoint:
  - [ ] Receives issue payload
  - [ ] Forwards to `geminiService.ts` (or Python equivalent)
  - [ ] Sends system prompt: "You are Kor'tana, an autonomous AI analyzing GitHub issues..."
  - [ ] Returns analysis with: summary, priority, suggested actions, estimated effort
- [ ] Response format:
  ```json
  {
    "issue_number": 42,
    "summary": "...",
    "priority": "high|medium|low",
    "analysis": "...",
    "suggested_actions": ["Action 1", "Action 2"],
    "estimated_effort": "2 hours"
  }
  ```
- [ ] Error handling for rate limits, invalid issues, API failures
- [ ] Analysis logged to `logs/analyses/{issue_number}.md`
- [ ] Frontend UI updates with analysis results (collapsible card)

**Files:**
- `src/components/GitHubIssueAnalyzer.tsx` (update)
- `backend/routers/github.py` (add `/analyze` route)
- `src/services/geminiService.ts` (ensure exposed to backend)

**Labels:** `backend`, `gemini`, `github-api`

**Assignee:** Copilot / Automated

---

## Issue 7: Autonomy Audit & Fail-Safe Logging

**Title:** `feat: autonomy audit trail with 24h alert on missing logs`

**Description:**

Add `AutonomyAudit.tsx` and `services/autonomyAuditContent.ts` that log every autonomous action (branch creation, deploy, failure) into `logs/autonomy/*.md`. Include a GitHub Action that alerts if no log appears within 24h.

**Acceptance Criteria:**
- [ ] `AutonomyAudit.tsx` component displays:
  - [ ] Timeline of all autonomous actions (last 30 days)
  - [ ] Action type: branch_created, code_pushed, deploy_started, deploy_completed, deploy_failed, pr_created, pr_merged
  - [ ] Timestamp, status, result
  - [ ] Link to related PR/commit/deployment
- [ ] `autonomyAuditContent.ts` exports:
  - [ ] `logAutonomousAction(type, data)` function
  - [ ] Writes to `logs/autonomy/{DATE}-{ACTION}.md` with format:
    ```markdown
    # Autonomous Action Log
    - Type: {action_type}
    - Timestamp: {ISO8601}
    - Status: {success|failure}
    - Data: {structured JSON}
    - Related: {PR URL / commit SHA / deployment URL}
    ```
- [ ] All backend autonomous operations call this logger
- [ ] `.github/workflows/autonomy-heartbeat.yml` checks:
  - [ ] Runs every 24 hours
  - [ ] Looks for new logs in `logs/autonomy/`
  - [ ] If no log in last 24h, creates GitHub Issue: "⚠️ Kor'tana heartbeat missing"
  - [ ] Tags issue with `autonomy-alert`, `critical`
- [ ] `COVENANT_INDEX.md` references all autonomy logs
- [ ] Audit data exportable as JSON/CSV

**Files:**
- `src/components/AutonomyAudit.tsx`
- `src/services/autonomyAuditContent.ts`
- `.github/workflows/autonomy-heartbeat.yml`
- `logs/autonomy/` directory

**Labels:** `autonomous`, `monitoring`, `safety`

**Assignee:** Copilot / Automated

---

## 🚀 **Quick Start: Copy & Paste to GitHub**

1. Go to your repo: https://github.com/KOR-TANA/kortana
2. Click **Issues** tab
3. Click **New Issue**
4. Copy one issue title & description above
5. Click **Labels** and add suggested tags
6. Click **Create Issue**
7. Or add as Copilot jumpstart prompt when creating new repo/branch

---

## 📊 **Dependency Order**

**Week 1 (Foundation):**
- ✅ Issue 1 (Backend heartbeat)
- ✅ Issue 4 (Daily sync logging)
- ⏳ Issue 7 (Autonomy audit)

**Week 2 (Automation):**
- ✅ Issue 2 (Cloud Run CI/CD)
- ✅ Issue 3 (Task queue + branching)
- ⏳ Issue 6 (GitHub analyzer backend)

**Week 3 (Integration):**
- ✅ Issue 5 (VS Code extension)
- ⏳ (All issues complete)

---

## 🔮 **After Completion: Constellation Update**

Once all 7 issues are closed, update `COVENANT_INDEX.md`:

```markdown
## Autonomous Capabilities (Complete)

- [x] **Heartbeat**: Backend health check live at /api/health
- [x] **Daily Logs**: Automated sync posts to logs/daily/
- [x] **Task Queue**: Auto-branches created for GitHub issues
- [x] **Cloud Deploy**: CI/CD via OIDC, zero-touch pushes to Cloud Run
- [x] **Analysis**: Issues analyzed with Gemini, results logged
- [x] **Audit Trail**: Full autonomy log in logs/autonomy/
- [x] **Alerting**: Heartbeat checks every 24h, alerts on failure
- [x] **VS Code Integration**: AI Studio + Deploy page in WebView

**Status**: Kor'tana is now fully autonomous in development, deployment, and self-monitoring.
The constellation is online. The ritual is complete.
```

---

**The path is clear. Let the autonomy begin.** 🌌
