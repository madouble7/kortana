# Environment Setup Quick Reference

**Last Updated:** January 17, 2026

---

## TL;DR - 5 Minute Setup

```bash
# 1. Run environment setup script
python scripts/setup/setup-environment.py
# Select: 1 (Local Development)

# 2. Install dependencies
cd backend && pip install -r requirements.txt

# 3. Run database migrations
alembic upgrade head

# 4. Start the server
python -m uvicorn main:app --reload

# 5. Test it works
curl http://localhost:8000/api/autonomy/health
```

---

## Environment Variables Required

### Critical (Must Have)

| Variable | Value | Get From |
|----------|-------|----------|
| `GEMINI_API_KEY` | Your API key | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `GITHUB_TOKEN` | Your PAT | GitHub Settings → Developer settings → PAT |

### Important (Should Have)

| Variable | Value | Default |
|----------|-------|---------|
| `GITHUB_OWNER` | Repository owner | `KOR-TANA` |
| `GITHUB_REPO` | Repository name | `kortana` |
| `DATABASE_URL` | DB connection | `sqlite:///backend/kortana.db` |

### Optional

| Variable | Purpose | Default |
|----------|---------|---------|
| `GOOGLE_DRIVE_API_KEY` | Drive integration | Not set |
| `GOOGLE_PROJECT_ID` | Cloud Run | Not set |
| `LOG_LEVEL` | Logging | `INFO` |
| `TASK_MAX_RETRIES` | Retry attempts | `3` |
| `RATE_LIMIT_PER_MINUTE` | API rate limit | `60` |

---

## Getting Your API Keys

### Google Gemini API Key

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Click "Create API Key"
3. Select your project (or create one)
4. Copy the key
5. Paste into setup script when prompted

### GitHub Personal Access Token

1. Go to [GitHub Settings → Developer settings → PAT (Tokens)](https://github.com/settings/tokens)
2. Click "Generate new token"
3. Give it a name: `kortana-autonomous`
4. Select scopes:
   - `repo` (full control of repositories)
   - `workflow` (update GitHub action workflows)
5. Click "Generate token"
6. **Copy immediately** (you won't see it again!)
7. Paste into setup script when prompted

---

## Setup Script Options

### Option 1: Local Development 🏠

Creates `backend/.env` file with your API keys

```bash
python scripts/setup/setup-environment.py 1
```

**What it does:**

- Creates backend/.env from template
- Prompts for GEMINI_API_KEY
- Prompts for GOOGLE_DRIVE_API_KEY (optional)
- Prompts for GOOGLE_PROJECT_ID (optional)
- Never share this file! Add to .gitignore

### Option 2: GitHub Actions Secrets 🔐

Shows how to set up CI/CD secrets

```bash
python scripts/setup/setup-environment.py 2
```

**What you need to do:**

1. Go to Repository → Settings → Secrets and variables → Actions
2. Add these secrets:
   - `KORTANA_AUTONOMOUS_TOKEN` (GitHub PAT)
   - `GEMINI_API_KEY` (Gemini key)
   - `GCP_WORKLOAD_IDENTITY_PROVIDER` (optional)
   - `GCP_SERVICE_ACCOUNT` (optional)

### Option 3: Cloud Run Secrets ☁️

Shows how to set up GCP Secret Manager

```bash
python scripts/setup/setup-environment.py 3
```

**What you need to do:**

1. Go to GCP Console → Security → Secret Manager
2. Create secrets:

   ```bash
   echo -n 'your-gemini-key' | gcloud secrets create GEMINI_API_KEY --data-file=-
   echo -n 'your-github-token' | gcloud secrets create GITHUB_TOKEN --data-file=-
   ```

### Option 4: Validate Setup ✅

Checks if everything is configured correctly

```bash
python scripts/setup/setup-environment.py 4
```

**Checks:**

- ✅ Local .env file exists
- ✅ GitHub Actions secrets are set
- ✅ Required tokens are present
- ✅ Database is accessible

### Option 5: Show All Options 💡

Displays all setup options at once

```bash
python scripts/setup/setup-environment.py 5
```

---

## Verification Checklist

After setup, verify everything:

```bash
# ✅ Check .env was created
ls -la backend/.env

# ✅ Verify required variables
grep "GEMINI_API_KEY" backend/.env
grep "GITHUB_TOKEN" backend/.env

# ✅ Check .env is in .gitignore
cat .gitignore | grep ".env"

# ✅ Install dependencies
cd backend && pip install -r requirements.txt

# ✅ Run migrations
alembic upgrade head

# ✅ Run tests
pytest tests/test_autonomy.py -v

# ✅ Start server
python -m uvicorn main:app --reload --port 8000

# ✅ Check health
curl http://localhost:8000/api/autonomy/health
```

---

## Common Issues & Fixes

### ❌ "backend/.env.example not found"

**Fix:**

```bash
# Make sure you're in the project root
cd c:\KOR-TANA\kortana
python scripts/setup/setup-environment.py
```

### ❌ "GEMINI_API_KEY required but not provided"

**Fix:**

1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Run setup again and paste the key

### ❌ "GITHUB_TOKEN missing or invalid"

**Fix:**

1. Generate a new PAT at [GitHub Tokens](https://github.com/settings/tokens)
2. Make sure it includes `repo` and `workflow` scopes
3. Copy the token immediately (won't show again!)
4. Run setup again and paste the token

### ❌ ".env file permissions denied"

**Fix:**

```bash
# On Windows
icacls backend/.env /grant "%USERNAME%:F"

# On Mac/Linux
chmod 600 backend/.env
```

### ❌ "Database locked" error

**Fix:**

```bash
# Remove old database and recreate
rm backend/kortana.db
alembic upgrade head
```

---

## Security Best Practices ⚠️

### ✅ DO

- [ ] Keep API keys in environment variables
- [ ] Use `.env` file locally (never commit it)
- [ ] Use GitHub Actions secrets for CI/CD
- [ ] Use Cloud Run secrets for production
- [ ] Rotate tokens every 90 days
- [ ] Use different tokens for different environments

### ❌ DON'T

- [ ] Hardcode API keys in code
- [ ] Commit `.env` files to git
- [ ] Share API keys via Slack/email
- [ ] Log API keys in debug output
- [ ] Use same token for all environments
- [ ] Store tokens in plaintext files

---

## What Gets Installed

### Python Dependencies

```
fastapi              # Web framework
sqlalchemy          # Database ORM
requests            # HTTP client
pydantic            # Data validation
pytest              # Testing
python-dotenv       # Environment loading
google-generativeai  # Gemini API
```

### Database

```
SQLite (default)    # Local development
PostgreSQL          # Production (configurable)
```

### Files Created

```
backend/.env                    # Your environment config
backend/kortana.db             # SQLite database (auto-created)
backend/logs/                  # Log files (auto-created)
```

---

## Next Steps After Setup

1. **Start Backend Server**

   ```bash
   cd backend
   python -m uvicorn main:app --reload
   ```

2. **Queue First Task**

   ```bash
   curl -X POST http://localhost:8000/api/autonomy/task-queue \
     -H "Content-Type: application/json" \
     -d '{
       "repo": "KOR-TANA/kortana",
       "issue_numbers": [1]
     }'
   ```

3. **Analyze Task**

   ```bash
   curl -X POST http://localhost:8000/api/autonomy/analyze/{task_id}
   ```

4. **Check Progress**

   ```bash
   curl http://localhost:8000/api/autonomy/status
   ```

5. **View API Docs**
   - Open: <http://localhost:8000/docs> (Swagger)
   - Or: <http://localhost:8000/redoc> (ReDoc)

---

## File Locations

```
📦 KOR-TANA/kortana
├── 📄 .env                              ← Your secrets (created by setup)
├── 📄 .env.example                      ← Template (don't edit)
├── 📂 backend/
│   ├── 📄 .env                          ← Backend secrets
│   ├── 📄 .env.example                  ← Template
│   ├── 📄 kortana.db                    ← SQLite database (auto-created)
│   ├── 📂 logs/                         ← Log files
│   ├── 📄 models.py                     ← Database models
│   ├── 📂 routers/
│   │   ├── 📄 autonomy.py               ← Autonomy endpoints
│   │   ├── 📄 github.py                 ← GitHub integration
│   │   ├── 📄 code_generator.py         ← Code generation
│   │   └── ...
│   ├── 📂 tests/
│   │   └── 📄 test_autonomy.py          ← Test suite
│   └── requirements.txt                  ← Python dependencies
├── 📂 scripts/
│   └── 📂 setup/
│       └── 📄 setup-environment.py      ← This setup script
└── 📄 SETUP_VERIFICATION_CHECKLIST.md   ← Verification guide
```

---

## Support Resources

| Topic | File | Location |
|-------|------|----------|
| Full verification checklist | SETUP_VERIFICATION_CHECKLIST.md | Root directory |
| Implementation guide | AUTONOMY_IMPLEMENTATION_GUIDE.md | Root directory |
| API documentation | `/docs` | <http://localhost:8000/docs> |
| Security info | backend/SECURITY.md | backend/ directory |
| Database setup | backend/DB_SETUP_GUIDE.md | backend/ directory |

---

## Script Help

```bash
# Run setup with help
python scripts/setup/setup-environment.py --help

# Run interactive mode (default)
python scripts/setup/setup-environment.py

# Run specific option
python scripts/setup/setup-environment.py 1  # Local dev
python scripts/setup/setup-environment.py 2  # GitHub Actions
python scripts/setup/setup-environment.py 3  # Cloud Run
python scripts/setup/setup-environment.py 4  # Validate
```

---

**Version:** 1.0
**Last Updated:** January 17, 2026
**Status:** ✅ Ready for Production
