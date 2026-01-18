# KOR'TANA Deployment - Scaffolded Human Only Steps

> **🎯 Protocol**: KOR'TANA executes all AUTO steps automatically. Only these HO steps require your action.

---

## 🚨 HUMAN ONLY (HO) STEPS

### HO-1: Create GitHub Personal Access Token ✅ COMPLETED

- GitHub token validated and configured.

---

### HO-2: Create Gemini API Key ✅ COMPLETED

- Gemini API key validated and configured.

---

### HO-3: Setup PostgreSQL Database ⏱️ 2-5 min

**Update**: I have optimized the setup. If you have PostgreSQL running, I can now attempt to create the database automatically.

**Option A: Local PostgreSQL (Recommended)**

1. Ensure PostgreSQL is running.
2. Ensure `backend/.env` has correct `DB_USER` and `DB_PASSWORD`.
3. Run: `python backend/init_db.py` (I will try to create the 'kortana' database for you).

**Option B: Docker**

```bash
docker run --name kortana-db \
  -e POSTGRES_DB=kortana \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=supersecretpassword \
  -p 5432:5432 \
  -d postgres
```

---

### HO-4: Configure Environment ✅ MOSTLY COMPLETED

- Tokens are configured.
- Ensure `DATABASE_URL` matches your HO-3 setup if you deviated from defaults.

---

### HO-5: Verify & Launch ⏱️ 1 min

```bash
# Run migrations
cd backend
alembic upgrade head

# Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

# 1. Run migrations

cd backend
alembic upgrade head

# 2. Start server

python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 3. Check these URLs

# Health: <http://localhost:8000/health>

# API Docs: <http://localhost:8000/docs>

# Autonomy: POST <http://localhost:8000/api/autonomy/task-queue>

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
