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

### HO-3: Setup PostgreSQL Database ✅ COMPLETED (Auto-Creation Ready)

- Database auto-creation logic implemented in `backend/init_db.py`.
- Alembic configured to sync with `get_settings()`.

---

### HO-4: Configure Environment ✅ COMPLETED

- GitHub, Gemini, and Database settings are fully configured in `backend/.env`.

---

### HO-5: Verify & Launch ⏱️ 1 min (Action Required)

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
