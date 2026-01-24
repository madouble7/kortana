# 🚦 KOR'TANA GO/NO-GO CHECKLIST

**Execute in < 60 Seconds**

---

### 1. 📂 Environment Readiness

- [ ] `.env` exists in `backend/` with a valid `GEMINI_API_KEY`.
- [ ] `CORS_ORIGINS` includes your deployment domains.
- [ ] `DATABASE_URL` is configured for PostgreSQL.

### 2. 🏥 System Health

- [ ] Backend starts: `python backend/main.py` shows "Kor'tana API starting".
- [ ] Health check: `curl http://localhost:8000/api/health` returns `status: alive`.
- [ ] DB test: `python backend/init_db.py` completes without errors.

### 3. 🌐 Frontend & PWA

- [ ] Build successful: `cd frontend && npm run build` creates `dist/`.
- [ ] Icons present: `frontend/public/icon-192.png` exists.
- [ ] Manifest valid: `/manifest.json` correctly lists icons.

### 4. 🛰️ Unified Routing

- [ ] SPA Routing: Navigating to `http://localhost:8000/vision` returns `index.html`.
- [ ] Injection: `view-source` shows `window.__KORTANA__` script in `<head>`.

### 5. 🚢 Deployment Scripts

- [ ] `validate_deployment.py` is present in `scripts/testing/`.
- [ ] `Dockerfile` in root is up to date with multi-stage logic.

---
**ALL CHECKS PASSED? Initiate Deployment Ritual.** 🔱
