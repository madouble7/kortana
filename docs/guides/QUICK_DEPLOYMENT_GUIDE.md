# 🚀 Quick Deployment Guide - KOR'TANA

## What's Next? The 3 Essential Steps

### ✅ Step 1: Configure Environment (15 minutes)

```bash
# Copy example to production
copy backend\.env.example backend\.env

# Edit backend\.env with YOUR values:
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx        # From github.com/settings/tokens
GEMINI_API_KEY=AIzaxxxxxxxxxxxxx      # From makersuite.google.com/app/apikey
DATABASE_URL=postgresql://user:pass@localhost/kortana_db
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_urlsafe(32))">
ENVIRONMENT=production
DEBUG=false
```

### ✅ Step 2: Setup Database (5 minutes)

```bash
# Create database (if needed)
# psql -U postgres -c "CREATE DATABASE kortana_db;"

# Apply migrations
cd backend
alembic upgrade head

# Verify
psql -d kortana_db -c "\dt"  # Should show 8+ tables
```

### ✅ Step 3: Start & Verify (5 minutes)

```bash
# Terminal 1: Start server
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2: Test endpoints
curl http://localhost:8000/api/pr/health
curl http://localhost:8000/api/testing/health
curl http://localhost:8000/api/code-review/health

# Browser: View API docs
open http://localhost:8000/docs
```

---

## What You Have Ready

| Component | Status | Details |
|-----------|--------|---------|
| **Phase 2 Code** | ✅ Done | 1,255+ lines, 3 routers |
| **API Endpoints** | ✅ Done | 17 endpoints ready |
| **Database Schema** | ✅ Done | Migration created |
| **Tests** | ✅ Done | 71+ passing |
| **Dependencies** | ✅ Done | All in requirements.txt |

---

## Critical Blockers (Must Resolve Before Deployment)

1. **GitHub Token** - Need for API access
   - Create at: <https://github.com/settings/tokens>
   - Add to `.env`: `GITHUB_TOKEN=xxx`

2. **Gemini API Key** - Need for code analysis
   - Create at: <https://makersuite.google.com/app/apikey>
   - Add to `.env`: `GEMINI_API_KEY=xxx`

3. **PostgreSQL Database** - Need for data storage
   - Install PostgreSQL 15+
   - Create database: `kortana_db`
   - Update `.env`: `DATABASE_URL=postgresql://...`

4. **Secret Key** - Need for session security
   - Generate: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
   - Add to `.env`: `SECRET_KEY=xxx`

---

## Production Deployment (Pick One)

### Option A: Direct Installation (Simplest)

```bash
# Install dependencies
pip install -r backend/requirements.txt

# Run with gunicorn
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker backend.main:app --bind 0.0.0.0:8000
```

### Option B: Docker (Recommended)

```bash
# Build image
docker build -t kortana .

# Run container
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=xxx \
  -e GEMINI_API_KEY=xxx \
  -e DATABASE_URL=xxx \
  kortana
```

### Option C: Cloud (AWS/GCP/Azure)

- AWS: Deploy to Lambda + API Gateway
- GCP: Deploy to Cloud Run
- Azure: Deploy to App Service

---

## Your API Endpoints

### PR Creation: `/api/pr`

```
POST   /api/pr/create/{task_id}        # Create PR
GET    /api/pr/status/{task_id}        # Check status
GET    /api/pr/health                  # Health check
```

### Testing: `/api/testing`

```
POST   /api/testing/run                # Run tests
GET    /api/testing/coverage           # Coverage report
GET    /api/testing/health             # Health check
```

### Code Review: `/api/code-review`

```
POST   /api/code-review/analyze        # Analyze code
POST   /api/code-review/security       # Security scan
GET    /api/code-review/health         # Health check
```

---

## What Happens Next After Deployment

1. **GitHub Issues** → KOR'TANA fetches and analyzes
2. **AI Analysis** → Gemini generates implementation plan
3. **Code Generation** → CodeGenerator creates code
4. **PR Creation** → Your PR router creates pull request
5. **Automated Tests** → Test orchestrator runs pytest
6. **Code Review** → Code reviewer scans for issues
7. **Auto-Merge** → Approved PRs merge automatically (optional)

---

## Troubleshooting Quick Fixes

**"Cannot connect to database"**

```bash
# Verify PostgreSQL is running
# Check DATABASE_URL format: postgresql://user:pass@host:port/db
# Verify database exists: psql -l
```

**"GitHub token not found"**

```bash
# Verify .env is in backend/ directory
# Source env: set (Windows) or export (Linux/Mac)
# Restart application
```

**"Port 8000 already in use"**

```bash
# Use different port: --port 8001
# Or kill existing process: lsof -ti:8000 | xargs kill -9
```

**"Import errors when starting"**

```bash
# Ensure requirements installed: pip install -r requirements.txt
# Check sys.path in main.py: should include backend directory
# Verify routers/__init__.py has all imports
```

---

## Files You'll Need to Edit

| File | What to Change | Example |
|------|----------------|---------|
| `backend/.env` | Credentials & config | `GITHUB_TOKEN=ghp_xxx` |
| `backend/main.py` | CORS origins (line ~100) | Add your domain |
| `docker-compose.yml` | Database config (if using) | Update PostgreSQL password |

---

## Estimated Timeline

| Task | Time | Blocker? |
|------|------|----------|
| Configure .env | 10 min | ⚠️ YES |
| Generate secrets | 5 min | ⚠️ YES |
| Setup database | 10 min | ⚠️ YES |
| Install dependencies | 5 min | ⚠️ YES |
| Apply migrations | 2 min | ⚠️ YES |
| Start server | 2 min | ⚠️ YES |
| Verify endpoints | 5 min | ⚠️ YES |
| **TOTAL** | **~40 minutes** | ✅ READY! |

---

## Need Help?

📖 **Documentation**: [PRE_DEPLOYMENT_CHECKLIST.md](PRE_DEPLOYMENT_CHECKLIST.md) - Detailed step-by-step guide

📋 **Features**: [PHASE_2_FINAL_STATUS.md](PHASE_2_FINAL_STATUS.md) - Complete feature list

🔒 **Security**: [backend/SECURITY.md](backend/SECURITY.md) - Security configuration

🗄️ **Database**: [backend/DB_SETUP_GUIDE.md](backend/DB_SETUP_GUIDE.md) - Database guide

---

**Status**: 🟡 Ready to deploy after configuring credentials
**Estimated Deployment Time**: 40 minutes to full production ✅
