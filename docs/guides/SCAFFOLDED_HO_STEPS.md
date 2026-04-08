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

### HO-3: Setup PostgreSQL Database ✅ COMPLETED

- **Status**: PostgreSQL container (Docker) is active and reachable.
- **Verification**: `init_db.py` confirmed connection to `kortana` DB on `localhost:5432`.
- **Migrations**: `alembic upgrade head` successfully applied all schema versions.

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
HO Steps:   [██████████] 100% Complete - IGNITION READY

```

**KOR'TANA is primed for liftoff.**

Final Verification Checklist:
1. ✅ Database Connectivity Verified
2. ✅ Schema Migrations Applied
3. ✅ API Configuration Validated
4. ✅ AI Service Handshake Ready

**Run the command below to start the engine.**

---

*Protocol Version: 1.1.0 (Post-Optimization)*
*Last Updated: 2026-01-18*
*Owner: Matt (Primary Human)*
