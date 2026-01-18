# KOR'TANA Deployment - Scaffolded Human Only Steps

> **🎯 Protocol**: KOR'TANA executes all AUTO steps automatically. Only these HO steps require your action.

---

## 🚨 HUMAN ONLY (HO) STEPS

### HO-1: Create GitHub Personal Access Token ⏱️ 2-3 min

**Step-by-step:**

1. Open: <https://github.com/settings/tokens>
2. Click **"Generate new token (classic)"**
3. **Note**: Give it a name like "KOR-TANA-Autonomy"
4. **Important**: Set expiration to "No expiration" or 1 year
5. **Select these scopes**:
   - [x] `repo` - Full control of private repositories
   - [x] `workflow` - Update GitHub Action workflows
   - [x] `read:org` - Read org and team membership
6. Click **"Generate token"**
7. **⚠️ COPY NOW** - You won't see it again!

**Token format**: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

---

### HO-2: Create Gemini API Key ⏱️ 1-2 min

**Step-by-step:**

1. Open: <https://makersuite.google.com/app/apikey>
2. Click **"Create API Key"**
3. Choose: **"Create API key in new project"**
4. Name: `KOR-TANA-Gemini`
5. Click **"Create"**
6. **⚠️ COPY NOW** - Store it safely!

**Key format**: `AIzaSy...`

---

### HO-3: Create PostgreSQL Database ⏱️ 5-10 min

**Option A: Local PostgreSQL**

```bash
# If PostgreSQL is installed
psql -U postgres

# In psql console:
CREATE DATABASE kortana;
CREATE USER kortana_user WITH PASSWORD 'YourSecurePassword123!';
GRANT ALL PRIVILEGES ON DATABASE kortana TO kortana_user;
\q
```

**Option B: Docker**

```bash
docker run --name kortana-db \
  -e POSTGRES_DB=kortana \
  -e POSTGRES_USER=kortana_user \
  -e POSTGRES_PASSWORD=YourSecurePassword123! \
  -p 5432:5432 \
  -d postgres
```

**Option C: Cloud (Supabase/Neon/Railway)**

1. Create account at <https://supabase.com> or <https://neon.tech>
2. Create new project
3. Copy connection string: `postgresql://user:pass@host:5432/kortana`

---

### HO-4: Configure Environment ⏱️ 2 min

**Open:** `backend/.env`

**Replace these values:**

```env
# GitHub Token (from HO-1)
GITHUB_TOKEN=ghp_your_github_token_here

# Gemini API Key (from HO-2)
GEMINI_API_KEY=your_gemini_api_key_here

# Database URL (from HO-3)
DATABASE_URL=postgresql://kortana_user:YourSecurePassword123!@localhost:5432/kortana
```

---

### HO-5: Verify Deployment ⏱️ 1 min

After completing HO-1 through HO-4:

```bash
# 1. Run migrations
cd backend
alembic upgrade head

# 2. Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Check these URLs:
# Health: http://localhost:8000/health
# API Docs: http://localhost:8000/docs
# Autonomy: POST http://localhost:8000/api/autonomy/task-queue
```

**Expected responses:**

- `/health` → `{"status": "alive"}`
- `/api/autonomy/health` → `{"status": "healthy"}`

---

## ✅ QUICK REFERENCE

| Step | What | Where | Time |
|------|------|-------|------|
| HO-1 | GitHub Token | github.com/settings/tokens | 2-3 min |
| HO-2 | Gemini Key | makersuite.google.com/app/apikey | 1-2 min |
| HO-3 | PostgreSQL | Local/Docker/Cloud | 5-10 min |
| HO-4 | Configure .env | backend/.env | 2 min |
| HO-5 | Verify | Browser + CLI | 1 min |

---

## 🎯 KOR'TANA AUTONOMY STATUS

```
AUTO Steps: [██████████] 100% Complete
HO Steps:   [░░░░░░░░░░░] 0% Complete - NEEDS YOUR ACTION
```

**KOR'TANA is waiting for you to complete HO-1 through HO-4.**

Once done, KOR'TANA will:

1. ✅ Run database migrations automatically
2. ✅ Install any missing dependencies
3. ✅ Start the server
4. ✅ Verify all health endpoints
5. ✅ Begin autonomous operations

---

*Protocol Version: 1.0.0*
*Last Updated: 2024-01-18*
*Owner: Matt (Primary Human)*
