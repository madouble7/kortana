# ✅ Kor'tana Deployment Checklist

## Pre-Deployment Setup

### Code Preparation
- [ ] All code committed to Git
- [ ] `.env` files excluded from Git (check `.gitignore`)
- [ ] Production environment variables documented
- [ ] Database models finalized
- [ ] API routes tested locally

### Accounts & Access
- [ ] GitHub account created
- [ ] GitHub repository created (`github.com/YOUR_USERNAME/kortana`)
- [ ] Code pushed to GitHub (`git push origin main`)

### For Vercel + Railway:
- [ ] Vercel account created (https://vercel.com/signup)
- [ ] Railway account created (https://railway.app/signup)

### For Google Cloud:
- [ ] Google Cloud account created
- [ ] Billing enabled on project
- [ ] `gcloud` CLI installed and configured
- [ ] Project ID ready

### API Keys Ready
- [ ] Gemini API key (https://aistudio.google.com/apikey)
- [ ] GitHub personal access token (https://github.com/settings/tokens)
- [ ] OpenAI API key (optional)
- [ ] Anthropic API key (optional)
- [ ] Discord bot token (optional)
- [ ] Pinecone API key (optional)

---

## OPTION 1: Vercel + Railway Deployment

### Railway Backend Setup
- [ ] Project created in Railway
- [ ] PostgreSQL database provisioned
- [ ] Redis instance provisioned
- [ ] GitHub repository connected
- [ ] Root directory set to `kortana/backend`
- [ ] Build command verified (`railway.json` detected)
- [ ] Start command verified (`uvicorn main:app`)

### Railway Environment Variables
- [ ] `ENVIRONMENT=production`
- [ ] `GEMINI_API_KEY` set
- [ ] `GITHUB_TOKEN` set
- [ ] `DATABASE_URL` set (linked to PostgreSQL)
- [ ] `REDIS_URL` set (linked to Redis)
- [ ] `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` set
- [ ] `CORS_ORIGINS` set (will update with Vercel URL)
- [ ] `SECRET_KEY` set (random string)
- [ ] `LOG_LEVEL=info`

### Railway Backend Deployment
- [ ] Backend deployed successfully
- [ ] Public domain generated (e.g., `kortana-backend.up.railway.app`)
- [ ] Domain URL copied
- [ ] Health check passes: `curl https://BACKEND_URL/api/health`

### Vercel Frontend Setup
- [ ] Project created in Vercel
- [ ] GitHub repository connected
- [ ] Framework preset set to "Vite"
- [ ] Root directory set to `kortana/frontend`
- [ ] Build command: `npm run build`
- [ ] Output directory: `dist`
- [ ] Install command: `npm install`

### Vercel Environment Variables
- [ ] `VITE_API_URL` set (Railway backend URL)
- [ ] `VITE_WS_URL` set (wss:// version of backend)
- [ ] `VITE_APP_NAME=Kor'tana`
- [ ] `VITE_ENVIRONMENT=production`

### Vercel Frontend Deployment
- [ ] Frontend deployed successfully
- [ ] Vercel URL copied (e.g., `kortana.vercel.app`)
- [ ] Frontend loads without errors
- [ ] Browser console checked (F12) - no errors

### Backend CORS Update
- [ ] Railway backend `CORS_ORIGINS` updated with Vercel URL
- [ ] Backend redeployed (automatic)

### Database Initialization
- [ ] Connected to Railway backend via CLI
- [ ] `python init_db.py` executed
- [ ] Database tables created
- [ ] No errors in logs

---

## OPTION 2: Google Cloud Run Deployment

### Google Cloud Project Setup
- [ ] Project created in Google Cloud Console
- [ ] Project ID copied
- [ ] Billing enabled
- [ ] `gcloud` CLI authenticated (`gcloud auth login`)
- [ ] Project set (`gcloud config set project PROJECT_ID`)

### APIs Enabled
- [ ] Cloud Build API enabled
- [ ] Cloud Run API enabled
- [ ] Container Registry API enabled
- [ ] Cloud SQL Admin API enabled

### Cloud SQL Database
- [ ] PostgreSQL instance created (`kortana-db`)
- [ ] Database `kortana` created
- [ ] User `kortana` created with password
- [ ] Connection string copied

### Docker Build
- [ ] Images built via `gcloud builds submit`
- [ ] Backend image pushed to Container Registry
- [ ] Frontend image pushed to Container Registry
- [ ] Build logs reviewed - no errors

### Cloud Run Deployment
- [ ] Backend service deployed
- [ ] Frontend service deployed
- [ ] Both services allow unauthenticated access
- [ ] Backend URL copied
- [ ] Frontend URL copied

### Environment Variables (Backend)
- [ ] `ENVIRONMENT=production`
- [ ] `GEMINI_API_KEY` set
- [ ] `GITHUB_TOKEN` set
- [ ] `OPENAI_API_KEY` set (if used)
- [ ] `DATABASE_URL` set (Cloud SQL connection)
- [ ] `CORS_ORIGINS` set (frontend URL)

### Environment Variables (Frontend)
- [ ] `VITE_API_URL` set (backend URL)
- [ ] `VITE_ENVIRONMENT=production`

### Database Initialization
- [ ] Cloud SQL proxy connected
- [ ] `python init_db.py` executed
- [ ] Tables created successfully

---

## Post-Deployment Verification

### Backend Health
- [ ] `/api/health` endpoint returns 200
- [ ] Response includes `"status": "alive"`
- [ ] Environment shows `"production"`
- [ ] No errors in backend logs

### Frontend Health
- [ ] Frontend URL loads successfully
- [ ] No console errors (F12)
- [ ] No network errors in DevTools
- [ ] App renders correctly

### API Integration
- [ ] Frontend can reach backend API
- [ ] CORS working (no CORS errors in console)
- [ ] Chat endpoint tested
- [ ] Task creation tested
- [ ] Health check passes from frontend

### Database Connection
- [ ] Backend can connect to database
- [ ] Queries execute successfully
- [ ] No connection pool errors

### PWA Installation
- [ ] `manifest.json` loads correctly
- [ ] Service worker registered
- [ ] Icons display in manifest
- [ ] "Add to Home Screen" available on mobile
- [ ] Installation works on iOS
- [ ] Installation works on Android
- [ ] Desktop installation works

---

## Mobile Testing

### iPhone/iPad (Safari)
- [ ] App loads in Safari
- [ ] No console errors
- [ ] "Add to Home Screen" works
- [ ] App icon appears on home screen
- [ ] App opens in standalone mode
- [ ] All features work

### Android (Chrome)
- [ ] App loads in Chrome
- [ ] No console errors
- [ ] "Add to Home screen" works
- [ ] App icon appears on home screen
- [ ] App opens in standalone mode
- [ ] All features work

### Desktop (Chrome/Edge)
- [ ] Install prompt appears
- [ ] Installation succeeds
- [ ] App opens as standalone window
- [ ] All features work

---

## Feature Testing

### Chat Functionality
- [ ] Chat interface loads
- [ ] Messages can be sent
- [ ] Gemini API responds
- [ ] Responses display correctly
- [ ] Conversation history persists

### Task Management
- [ ] Task list loads
- [ ] Tasks can be created
- [ ] Task status updates
- [ ] Task details display

### Autonomy System
- [ ] HOP cycle can be triggered
- [ ] Tasks are classified correctly
- [ ] Auto tasks execute
- [ ] HO tasks require approval

### GitHub Integration
- [ ] GitHub token validated
- [ ] Issues can be fetched
- [ ] Tasks created from issues
- [ ] Branch creation works

---

## Monitoring Setup

### Logging
- [ ] Backend logs viewable
- [ ] Frontend errors tracked
- [ ] Log level set appropriately
- [ ] No sensitive data in logs

### Health Checks
- [ ] Uptime monitoring configured (optional)
- [ ] Alert emails configured (optional)
- [ ] Health check URL: `/api/health`

### Performance
- [ ] Response times acceptable (<2s)
- [ ] Frontend loads quickly (<3s)
- [ ] Database queries optimized
- [ ] No memory leaks detected

---

## Security Verification

### Environment Variables
- [ ] All secrets in environment (not code)
- [ ] `.env` not committed to Git
- [ ] Production secrets different from dev
- [ ] Database password strong

### HTTPS
- [ ] All URLs use HTTPS
- [ ] No mixed content warnings
- [ ] SSL certificates valid

### CORS
- [ ] CORS restricted to frontend URL
- [ ] No wildcard `*` in production
- [ ] Credentials allowed if needed

### API Security
- [ ] Rate limiting enabled (if configured)
- [ ] Input validation working
- [ ] Error messages don't leak secrets

---

## Documentation

### Code
- [ ] README updated with deployment info
- [ ] API endpoints documented
- [ ] Environment variables documented

### Operations
- [ ] Deployment process documented
- [ ] Troubleshooting guide created
- [ ] Rollback procedure documented

---

## Optional Enhancements

### Custom Domain
- [ ] Domain purchased
- [ ] DNS configured
- [ ] SSL certificate provisioned
- [ ] Domain points to app

### Analytics
- [ ] Google Analytics added (optional)
- [ ] Error tracking (Sentry, etc.) added
- [ ] Usage metrics tracked

### Backup
- [ ] Database backups configured
- [ ] Backup schedule set
- [ ] Restore procedure tested

---

## Final Sign-Off

- [ ] All critical features tested
- [ ] All team members have access
- [ ] Deployment documented
- [ ] Monitoring active
- [ ] No critical errors in logs
- [ ] Performance acceptable
- [ ] Security verified

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Version:** _______________  
**Frontend URL:** _______________  
**Backend URL:** _______________

---

## 🎉 DEPLOYMENT COMPLETE

**Kor'tana is live and breathing!** 🌌

**Next Steps:**
1. Share the URL with users
2. Monitor logs for the first 24 hours
3. Gather feedback
4. Iterate and improve

**The constellation is alive.**
