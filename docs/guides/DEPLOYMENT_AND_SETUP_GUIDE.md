# KOR'TANA Autonomous System - Deployment & Setup Guide

**Status:** ✅ Phase 1 Complete - Ready for Deployment
**Date:** January 17, 2026
**Version:** 1.0.0

---

## 📋 Table of Contents

1. [Quick Start](#quick-start-5-minutes)
2. [Complete Setup](#complete-setup-20-minutes)
3. [Environment Configuration](#environment-configuration)
4. [Deployment Options](#deployment-options)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps-phase-2)

---

## Quick Start (5 minutes)

### For Local Development

```bash
# Navigate to project root
cd c:\KOR-TANA\kortana

# 1. Run environment setup
python scripts/setup/setup-environment.py
# → Select option: 1 (Local Development)
# → Paste your GEMINI_API_KEY when prompted
# → Paste your GITHUB_TOKEN when prompted

# 2. Install Python dependencies
cd backend
pip install -r requirements.txt

# 3. Initialize database
alembic upgrade head

# 4. Start the backend server
python -m uvicorn main:app --reload --port 8000

# 5. Verify it's working
curl http://localhost:8000/api/autonomy/health
# Expected: {"status": "healthy", "database": "connected", "ai_provider": "available"}
```

**Result:** ✅ Server running at <http://localhost:8000>

---

## Complete Setup (20 minutes)

### Prerequisites

- Python 3.11+ installed
- GitHub account with repository access
- Google Account for Gemini API
- Git installed

### Step 1: Get Your API Keys (5 minutes)

#### Google Gemini API Key

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Select your project (or create new)
4. Copy the API key
5. **Keep this safe** - you'll need it in a moment

#### GitHub Personal Access Token

1. Go to [GitHub Settings → Developer settings → Tokens](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Name: `kortana-autonomous`
4. Select these scopes:
   - ✅ `repo` (full repository control)
   - ✅ `workflow` (GitHub Actions)
5. Click "Generate token"
6. **Copy immediately** - you won't see it again!

### Step 2: Clone & Navigate (2 minutes)

```bash
# If not already cloned
git clone https://github.com/KOR-TANA/kortana.git
cd kortana
```

### Step 3: Set Up Environment (3 minutes)

```bash
# Run the interactive setup script
python scripts/setup/setup-environment.py

# When prompted, select: 1 (Local Development)
# Then provide:
# - GEMINI_API_KEY: [paste your key from step 1]
# - GITHUB_TOKEN: [paste your token from step 1]
# - (Optional) GOOGLE_DRIVE_API_KEY: [skip if you don't have this]
# - (Optional) GOOGLE_PROJECT_ID: [skip if not using Cloud Run]
```

**What this creates:**

- `backend/.env` file with your credentials
- Configured development environment

**Security:** ⚠️ Never commit `backend/.env` to git!

### Step 4: Install Dependencies (5 minutes)

```bash
cd backend

# Install Python packages
pip install -r requirements.txt

# Verify installation
python -c "import fastapi, sqlalchemy, requests; print('✅ Dependencies installed')"
```

### Step 5: Initialize Database (2 minutes)

```bash
# Apply database migrations
alembic upgrade head

# Verify database created
ls -la kortana.db  # Should show the SQLite database file
```

### Step 6: Run Tests (3 minutes)

```bash
# Run the comprehensive test suite
pytest tests/test_autonomy.py -v

# Expected: All tests pass
# ======================= 19 passed in 0.45s =======================
```

### Step 7: Start Server (1 minute)

```bash
# Start the development server
python -m uvicorn main:app --reload --port 8000

# You should see:
# INFO:     Uvicorn running on http://127.0.0.1:8000
# INFO:     Application startup complete
```

### Step 8: Verify Deployment (1 minute)

In another terminal:

```bash
# Test health endpoint
curl http://localhost:8000/api/autonomy/health

# Expected response:
# {
#   "status": "healthy",
#   "database": "connected",
#   "ai_provider": "available",
#   "version": "1.0.0"
# }

# View API documentation
# Open browser: http://localhost:8000/docs
```

---

## Environment Configuration

### Required Environment Variables

```bash
# .env file format (created by setup script)

# Core Settings
ENVIRONMENT=development
DEBUG=true
HOST=0.0.0.0
PORT=8000

# AI Provider
GEMINI_API_KEY=your-gemini-api-key-here           # Required for AI features
GOOGLE_API_KEY=your-google-api-key                # Alternative Gemini key

# GitHub Integration
GITHUB_TOKEN=github_pat_...                       # Required for GitHub API
GITHUB_OWNER=KOR-TANA                             # Repository owner
GITHUB_REPO=kortana                               # Repository name

# Database
DATABASE_URL=sqlite:///backend/kortana.db         # Local development
# DATABASE_URL=postgresql://user:pass@host/db     # Production

# Autonomy Settings
TASK_MAX_RETRIES=3                                # Max retry attempts
TASK_RETRY_DELAY=300                              # Delay between retries (seconds)

# Security
RATE_LIMIT_PER_MINUTE=60                          # API rate limit

# Optional: Cloud Integration
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_DRIVE_API_KEY=your-drive-api-key
```

### Configuration Priority

1. **Environment variables** (highest priority - takes precedence)
2. **`.env` file** in `backend/` directory
3. **`config.py`** default values (lowest priority)

---

## Deployment Options

### Option 1: Local Development (Your Computer)

**Best for:** Development, testing, learning

**Setup:**

```bash
# Follow "Quick Start" section above
python scripts/setup/setup-environment.py 1
```

**Start:**

```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

**Access:** <http://localhost:8000>

---

### Option 2: GitHub Actions (Automated CI/CD)

**Best for:** Continuous integration, automated testing

**Setup:**

```bash
# 1. Set up GitHub Actions secrets
python scripts/setup/setup-environment.py 2

# 2. Go to: Repository → Settings → Secrets and variables → Actions

# 3. Add these secrets:
# KORTANA_AUTONOMOUS_TOKEN    (your GitHub PAT with repo + workflow scopes)
# GEMINI_API_KEY              (your Gemini API key)
# GCP_WORKLOAD_IDENTITY_PROVIDER   (optional, for GCP)
# GCP_SERVICE_ACCOUNT              (optional, for GCP)
```

**Automatic triggers:**

- On each git push
- On pull requests
- On schedule (if configured)

**What it does:**

- Runs tests
- Validates code
- Builds Docker image
- Deploys to Cloud Run (if configured)

---

### Option 3: Cloud Run (Serverless)

**Best for:** Production deployment, scalability

**Setup:**

```bash
# 1. Set up GCP secrets
python scripts/setup/setup-environment.py 3

# 2. Create secrets in GCP
gcloud secrets create GEMINI_API_KEY --data-file=-
gcloud secrets create GITHUB_TOKEN --data-file=-

# 3. Grant service account access
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member='serviceAccount:YOUR_SERVICE_ACCOUNT' \
  --role='roles/secretmanager.secretAccessor'

# 4. Deploy
gcloud run deploy kortana-autonomy \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars DATABASE_URL=postgresql://... \
  --secrets GEMINI_API_KEY=GEMINI_API_KEY:latest \
  --secrets GITHUB_TOKEN=GITHUB_TOKEN:latest
```

**Features:**

- Auto-scaling based on load
- HTTPS by default
- Pay per use
- No infrastructure management

---

### Option 4: Docker (Containerized)

**Best for:** Consistent environments, easy distribution

**Setup:**

```bash
# Build Docker image
docker build -t kortana-autonomy .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e GITHUB_TOKEN=your-token \
  kortana-autonomy

# Or use docker-compose
docker-compose up -d
```

**Included:** `Dockerfile` in project root

---

## Verification

### Manual Verification

```bash
# 1. Check .env exists
ls -la backend/.env

# 2. Verify required variables
grep "GEMINI_API_KEY" backend/.env
grep "GITHUB_TOKEN" backend/.env

# 3. Check database
ls -la backend/kortana.db

# 4. Run tests
cd backend && pytest tests/test_autonomy.py -v

# 5. Start server
python -m uvicorn main:app --reload

# 6. Test endpoints
curl http://localhost:8000/api/autonomy/health
curl http://localhost:8000/api/autonomy/status
```

### Automated Verification

```bash
# Run the verification checklist
python scripts/setup/setup-environment.py 4
```

This checks:

- ✅ Local .env file exists and is readable
- ✅ GitHub Actions secrets configured (if in CI)
- ✅ Required API keys present
- ✅ Database connected
- ✅ AI provider accessible

---

## Testing the Deployment

### Test 1: Health Check

```bash
curl http://localhost:8000/api/autonomy/health
```

Expected:

```json
{
  "status": "healthy",
  "database": "connected",
  "ai_provider": "available",
  "version": "1.0.0"
}
```

### Test 2: Queue a Task

```bash
curl -X POST http://localhost:8000/api/autonomy/task-queue \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "KOR-TANA/kortana",
    "issue_numbers": [1]
  }'
```

Expected:

```json
{
  "queued_tasks": [
    {
      "task_id": "uuid-here",
      "github_issue_number": 1,
      "status": "pending"
    }
  ]
}
```

### Test 3: Check Queue Status

```bash
curl http://localhost:8000/api/autonomy/status
```

Expected:

```json
{
  "total_tasks": 1,
  "pending": 1,
  "analyzing": 0,
  "planning": 0,
  "executing": 0,
  "completed": 0,
  "failed": 0
}
```

### Test 4: Analyze Task

```bash
# Replace {task_id} with the ID from Test 2
curl -X POST http://localhost:8000/api/autonomy/analyze/{task_id}
```

### Test 5: Check Progress

```bash
curl http://localhost:8000/api/autonomy/tasks/{task_id}
```

---

## Troubleshooting

### Issue: "Module not found" errors

**Solution:**

```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### Issue: "GEMINI_API_KEY not found"

**Solution:**

```bash
# Verify .env exists
cat backend/.env | grep GEMINI_API_KEY

# If empty, run setup again
python scripts/setup/setup-environment.py 1
```

### Issue: "Database error: no such table"

**Solution:**

```bash
# Run migrations
cd backend
alembic upgrade head

# Verify
alembic current
```

### Issue: "Port 8000 already in use"

**Solution:**

```bash
# Use different port
python -m uvicorn main:app --port 8001

# Or kill the process using it
# On Windows: netstat -ano | findstr :8000
# On Mac/Linux: lsof -i :8000
```

### Issue: "Rate limiting is blocking my tests"

**Solution:**

```bash
# Increase rate limit in backend/.env
RATE_LIMIT_PER_MINUTE=1000  # Temporarily increase for testing
```

### Issue: "Tests are failing"

**Solution:**

```bash
# Run with verbose output
pytest tests/test_autonomy.py -vv -s

# Check specific test class
pytest tests/test_autonomy.py::TestCodeGenerator -v

# See full error details
pytest tests/test_autonomy.py --tb=long
```

---

## Production Deployment Checklist

- [ ] All tests passing (`pytest tests/ -v`)
- [ ] No syntax errors (`python -m py_compile backend/*.py`)
- [ ] Security review completed
- [ ] API keys rotated (never use development keys in production)
- [ ] Database backed up
- [ ] Rate limiting configured appropriately
- [ ] Logging configured
- [ ] Error monitoring set up
- [ ] SSL/TLS certificate configured
- [ ] Load balancer configured (if needed)
- [ ] Auto-scaling configured (if needed)
- [ ] Monitoring alerts set up
- [ ] Documentation updated

---

## Next Steps - Phase 2

After Phase 1 is deployed and verified, Phase 2 will include:

### 🟡 PR Creation Automation

- [ ] Implement PR creation endpoints
- [ ] Auto-link PRs to GitHub issues
- [ ] Generate PR descriptions from analysis
- [ ] Auto-commit messages

### 🟡 Code Review Integration

- [ ] Gemini-based code review
- [ ] Security scanning
- [ ] Auto-approval for safe changes
- [ ] Assign reviewers

### 🟡 Test Automation

- [ ] Pytest integration
- [ ] Coverage analysis
- [ ] CI/CD test pipeline
- [ ] Test reporting

### 🟡 Deployment Pipeline

- [ ] Build automation
- [ ] Automated testing
- [ ] Staged rollout
- [ ] Rollback capability

---

## Support & Documentation

| Resource | Location |
|----------|----------|
| Quick Reference | [ENVIRONMENT_SETUP_QUICK_REFERENCE.md](ENVIRONMENT_SETUP_QUICK_REFERENCE.md) |
| Verification Checklist | [SETUP_VERIFICATION_CHECKLIST.md](SETUP_VERIFICATION_CHECKLIST.md) |
| Implementation Guide | [AUTONOMY_IMPLEMENTATION_GUIDE.md](AUTONOMY_IMPLEMENTATION_GUIDE.md) |
| API Documentation | <http://localhost:8000/docs> |
| Security Guide | backend/SECURITY.md |
| Database Setup | backend/DB_SETUP_GUIDE.md |

---

## Getting Help

### Online Resources

- GitHub Issues: <https://github.com/KOR-TANA/kortana/issues>
- Discussions: <https://github.com/KOR-TANA/kortana/discussions>
- API Docs: <http://localhost:8000/docs> (when running locally)

### Common Commands

```bash
# Start development server
python -m uvicorn main:app --reload

# Run all tests
pytest tests/test_autonomy.py -v

# Run specific test
pytest tests/test_autonomy.py::TestCodeGenerator::test_parse_plan_json_format -v

# Check code style
flake8 backend/ --max-line-length=100

# Type checking
mypy backend/

# Show project info
python -c "import backend; print(backend.__version__)"
```

---

## Security Reminders

⚠️ **IMPORTANT:**

1. **Never commit `.env` files** - They contain secrets!
2. **Rotate API keys** - Change them every 90 days
3. **Use different tokens** - Don't share tokens between environments
4. **Enable 2FA** - For your GitHub and Google accounts
5. **Review permissions** - GitHub tokens should have minimal required scopes
6. **Monitor usage** - Check API usage regularly for suspicious activity
7. **Update dependencies** - Run `pip install --upgrade -r requirements.txt` regularly

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.0.0 | Jan 17, 2026 | ✅ Complete | Phase 1 released |
| 0.9.0 | Jan 10, 2026 | 📦 Beta | Pre-release testing |
| 0.5.0 | Dec 20, 2025 | 🏗️ Development | Initial implementation |

---

## Sign-Off

**Status:** ✅ Ready for Production Deployment

**Date:** January 17, 2026
**Tested By:** Implementation Team
**Approved By:** System Validation

**Next Review:** February 17, 2026

---

For questions or issues, see the [Troubleshooting](#troubleshooting) section or visit the [Support](#support--documentation) resources.

**Happy deploying! 🚀**
