# 🚀 KOR'TANA Pre-Deployment Checklist & Next Steps

**Date**: January 18, 2026
**Current Status**: Phase 2 Implementation Complete
**Next Phase**: Production Deployment

---

## 📋 Pre-Deployment Checklist

### ✅ Completed Tasks

- [x] Phase 2 modules implemented (PR creation, test orchestrator, code review)
- [x] All 3 routers integrated into main.py
- [x] Database migration created
- [x] 71+ tests passing
- [x] All dependencies specified in requirements.txt
- [x] Import errors fixed
- [x] Type annotations corrected
- [x] Error handling implemented

### ⚠️ Tasks Requiring Your Attention Before Deployment

#### 1. **Environment Configuration** (REQUIRED)

```bash
# ✅ Do you have these environment variables configured?
GITHUB_TOKEN=xxx              # GitHub API token
GEMINI_API_KEY=xxx            # Google Gemini API key
DATABASE_URL=xxx              # PostgreSQL connection
ENVIRONMENT=production         # Set to 'production'
SECRET_KEY=xxx                # FastAPI secret key (generate new one)
DEBUG=false                    # Set to false for production
CORS_ORIGINS=xxx              # Allowed origins (comma-separated)
```

**Action Required**: Review [backend/.env.example](backend/.env.example) and create your production `.env` file.

#### 2. **Database Setup** (REQUIRED)

```bash
# ✅ Have you:
[ ] Created PostgreSQL database?
[ ] Configured connection string in DATABASE_URL?
[ ] Run initial migration: alembic upgrade head?
[ ] Verified table creation?
```

**Action Required**: Execute these commands:

```bash
cd backend
alembic upgrade head                    # Apply migrations
python init_db.py                       # Initialize if needed
```

#### 3. **Secret Key Generation** (REQUIRED)

```bash
# Generate a new secret key for production
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Then update SECRET_KEY in your .env
```

**Action Required**: Generate and set new SECRET_KEY in `.env`.

#### 4. **GitHub Integration Setup** (REQUIRED)

```bash
# ✅ Do you have:
[ ] GitHub Personal Access Token created?
[ ] Token has 'repo' and 'workflow' scopes?
[ ] Token stored in GITHUB_TOKEN env var?
[ ] Webhook configured for your repository? (optional but recommended)
```

**Action Required**: Create GitHub token at <https://github.com/settings/tokens>

#### 5. **Gemini API Setup** (REQUIRED)

```bash
# ✅ Do you have:
[ ] Google Gemini API key?
[ ] API key enabled for your project?
[ ] Key stored in GEMINI_API_KEY env var?
```

**Action Required**: Create API key at <https://makersuite.google.com/app/apikey>

#### 6. **CORS Configuration** (RECOMMENDED)

Review [backend/main.py](backend/main.py) lines 100-130 and update CORS origins:

```python
CORSMiddleware(
    app,
    allow_origins=[
        "http://localhost:3000",      # Frontend dev
        "https://yourdomain.com",     # Production frontend
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
```

**Action Required**: Update CORS_ORIGINS in your `.env` file.

#### 7. **Security Headers Verification** (RECOMMENDED)

The system includes:

- [x] Security headers middleware
- [x] Rate limiting (10 req/sec per IP)
- [x] Request ID tracking
- [x] CORS protection
- [x] Path traversal protection

**Action Required**: Review [backend/middleware/security.py](backend/middleware/security.py)

#### 8. **Database Backup Strategy** (REQUIRED FOR PRODUCTION)

```bash
# Set up regular backups:
pg_dump kortana_db > backup_$(date +%Y%m%d).sql
```

**Action Required**: Configure automated PostgreSQL backups.

#### 9. **Monitoring Setup** (RECOMMENDED)

The system includes Prometheus metrics. Configure:

- [ ] Prometheus scrape endpoint: `http://localhost:8000/metrics`
- [ ] Grafana dashboard (optional)
- [ ] AlertManager (optional)
- [ ] Sentry error tracking (optional but recommended)

**Action Required**: Set SENTRY_DSN if using Sentry.

#### 10. **Health Check Verification** (REQUIRED)

```bash
# Before deployment, verify all health endpoints:
curl http://localhost:8000/api/pr/health
curl http://localhost:8000/api/testing/health
curl http://localhost:8000/api/code-review/health
curl http://localhost:8000/api/autonomy/health
```

**Action Required**: Run these after starting the server.

---

## 🎯 Deployment Steps (In Order)

### Step 1: Prepare Environment

```bash
cd c:\KOR-TANA\kortana

# Create production .env file
copy backend\.env.example backend\.env

# Edit backend\.env with your production values
# Required:
#   - GITHUB_TOKEN
#   - GEMINI_API_KEY
#   - DATABASE_URL
#   - SECRET_KEY (generate new)
#   - ENVIRONMENT=production
```

### Step 2: Install Dependencies

```bash
# If using virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install all dependencies
pip install -r backend/requirements.txt

# Optional: Install development tools
pip install -r backend/requirements-dev.txt
```

### Step 3: Database Setup

```bash
cd backend

# Create database (if not exists)
# psql -U postgres -c "CREATE DATABASE kortana_db;"

# Apply migrations
alembic upgrade head

# Verify migrations
psql -d kortana_db -c "\dt"  # Should show all tables
```

### Step 4: Run Tests (Optional but Recommended)

```bash
cd backend
pytest tests/ -v --tb=short

# Or with coverage
pytest tests/ --cov=. --cov-report=html
```

### Step 5: Start Server

```bash
# Development mode (with auto-reload)
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode (using gunicorn)
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app --bind 0.0.0.0:8000
```

### Step 6: Verify Deployment

```bash
# In another terminal, verify the API is responding
curl http://localhost:8000/health
curl http://localhost:8000/api/pr/health
curl http://localhost:8000/api/testing/health
curl http://localhost:8000/api/code-review/health

# Check API documentation
# Visit: http://localhost:8000/docs
```

---

## 🔒 Production Configuration Recommendations

### For Production Deployment

**Option A: Docker Containerization** (Recommended)

```dockerfile
# Create backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "main:app", "--bind", "0.0.0.0:8000"]
```

**Option B: Direct Installation** (Simpler)

```bash
# Install Python 3.13
# Create virtual environment
# Install dependencies
# Run with gunicorn or supervisor
```

**Option C: Cloud Deployment** (AWS/GCP/Azure)

- AWS: Use Lambda + API Gateway
- GCP: Use Cloud Run
- Azure: Use App Service

### Recommended Production Stack

- **OS**: Ubuntu 22.04 LTS
- **Python**: 3.13.1
- **Database**: PostgreSQL 15+
- **Web Server**: Gunicorn + Nginx
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack or Sentry
- **Containerization**: Docker (optional)

---

## 📊 Next Steps After Deployment

### Phase 3: Enhanced Features (Optional)

1. **Advanced Monitoring**

   ```bash
   # Set up metrics collection
   pip install prometheus-client
   # Configure Grafana dashboards
   ```

2. **Webhook Integration**
   - Configure GitHub webhook for automatic task queueing
   - Implement push notifications

3. **Auto-Merge Workflows**
   - Implement automatic PR merging for approved changes
   - Add configurable merge strategies

4. **Enhanced Code Analysis**
   - Add SonarQube integration
   - Implement custom linting rules
   - Add SAST (Static Application Security Testing)

5. **Scaling & Performance**
   - Add Redis for caching
   - Implement async task queue (Celery)
   - Configure database connection pooling

### Performance Optimization

```python
# Already configured in your system:
- [x] Async/await throughout
- [x] Connection pooling
- [x] Database indexing
- [x] Rate limiting
- [x] Request caching

# Consider adding:
- [ ] Redis caching layer
- [ ] Database query optimization
- [ ] API endpoint caching
- [ ] CDN for static assets
```

---

## ⚠️ Critical Before-Deployment Checklist

| Item | Status | Action |
|------|--------|--------|
| Environment variables configured | ⚠️ TODO | Set GITHUB_TOKEN, GEMINI_API_KEY, DATABASE_URL |
| Database created and migrated | ⚠️ TODO | Run `alembic upgrade head` |
| Secret key generated | ⚠️ TODO | Generate and set SECRET_KEY |
| CORS origins configured | ⚠️ TODO | Set CORS_ORIGINS for your domain |
| Rate limiting tested | ✅ Implemented | Verify in code |
| Security headers verified | ✅ Implemented | Verify in code |
| Health endpoints tested | ⚠️ TODO | curl <http://localhost:8000/*/health> |
| Tests passing | ✅ 71+ passing | Run `pytest` before deploy |
| Dependencies installed | ⚠️ TODO | Run `pip install -r requirements.txt` |
| Backups configured | ⚠️ TODO | Set up PostgreSQL backups |

---

## 🆘 Troubleshooting Pre-Deployment

### Issue: "ModuleNotFoundError: No module named 'xxx'"

```bash
# Solution: Ensure sys.path is configured in main.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# And install missing package
pip install [package-name]
```

### Issue: "Database connection refused"

```bash
# Check PostgreSQL is running
# Verify DATABASE_URL in .env
# Verify credentials and database name exist
```

### Issue: "GITHUB_TOKEN not found"

```bash
# Ensure .env file is in backend/ directory
# Check GITHUB_TOKEN is set in .env
# Restart the application
```

### Issue: "CORS error on frontend requests"

```bash
# Update CORS_ORIGINS in .env
# Ensure frontend domain is included
# Test with curl: curl -H "Origin: http://localhost:3000" http://localhost:8000/health
```

---

## 📚 Quick Reference

### Start Server

```bash
cd backend
python -m uvicorn main:app --reload
```

### Run Tests

```bash
cd backend
pytest tests/ -v
```

### Apply Migrations

```bash
cd backend
alembic upgrade head
```

### Access API Documentation

```
http://localhost:8000/docs           # Swagger UI
http://localhost:8000/redoc          # ReDoc
```

### Monitor Metrics

```
http://localhost:8000/metrics        # Prometheus metrics
```

---

## ✅ Ready to Deploy?

Once you've completed the checklist above, you're ready for production!

**Final Verification**:

```bash
# 1. Environment variables set
echo $env:GITHUB_TOKEN
echo $env:GEMINI_API_KEY
echo $env:DATABASE_URL

# 2. Database migrated
cd backend && alembic current

# 3. Tests passing
pytest tests/ -v

# 4. Server starts
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# 5. Health checks pass
curl http://localhost:8000/api/pr/health
curl http://localhost:8000/api/testing/health
curl http://localhost:8000/api/code-review/health
```

**Status**: 🟡 READY FOR DEPLOYMENT (after completing checklist)

---

**Questions?** Review the documentation:

- [PHASE_2_FINAL_STATUS.md](PHASE_2_FINAL_STATUS.md) - Complete feature list
- [backend/SECURITY.md](backend/SECURITY.md) - Security configuration
- [backend/DB_SETUP_GUIDE.md](backend/DB_SETUP_GUIDE.md) - Database setup
- [backend/README.md](backend/README.md) - API overview
