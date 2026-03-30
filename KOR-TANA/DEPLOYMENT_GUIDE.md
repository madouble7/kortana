# 🌌 KOR'TANA DEPLOYMENT GUIDE
**Deploy to Vercel + Railway OR Google Cloud Run**

## 📱 What You'll Get

**After deployment, Kor'tana will be:**
- ✅ Live at a public URL (e.g., `kortana.vercel.app`)
- ✅ Accessible on PC, mobile, and tablet
- ✅ Installable as a Progressive Web App (PWA)
- ✅ Running on production infrastructure with auto-scaling

---

## 🚀 OPTION 1: VERCEL + RAILWAY (RECOMMENDED)

**Best for:** Fast deployment, free tier, auto-scaling

### Prerequisites
1. ✅ GitHub account
2. ✅ Vercel account (free) - https://vercel.com/signup
3. ✅ Railway account (free) - https://railway.app/signup
4. ✅ Your code pushed to GitHub

### Step-by-Step Deployment

#### 1. Push Code to GitHub
```bash
cd C:\KOR-TANA
git init
git add .
git commit -m "Initial Kor'tana deployment"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/kortana.git
git push -u origin main
```

#### 2. Deploy Backend to Railway

**A. Create PostgreSQL Database**
1. Go to https://railway.app/new
2. Click "New Project"
3. Select "Provision PostgreSQL"
4. Wait for provisioning (~30 seconds)
5. Copy the `DATABASE_URL` from the "Connect" tab

**B. Create Redis Database**
1. In the same Railway project, click "New"
2. Select "Provision Redis"
3. Copy the `REDIS_URL` from the "Connect" tab

**C. Deploy Backend Service**
1. Click "New" → "GitHub Repo"
2. Select your `kortana` repository
3. Railway will auto-detect `kortana/backend/railway.json`
4. Configure Service:
   - **Name:** `kortana-backend`
   - **Root Directory:** `kortana/backend`
   - **Start Command:** (auto-detected from railway.json)

**D. Add Environment Variables**
Click on the backend service → "Variables" tab:
```
ENVIRONMENT=production
GEMINI_API_KEY=your_gemini_key_here
GITHUB_TOKEN=your_github_token
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}
DB_HOST=${{Postgres.PGHOST}}
DB_PORT=${{Postgres.PGPORT}}
DB_NAME=${{Postgres.PGDATABASE}}
DB_USER=${{Postgres.PGUSER}}
DB_PASSWORD=${{Postgres.PGPASSWORD}}
CORS_ORIGINS=https://your-frontend.vercel.app,https://localhost:5173
SECRET_KEY=your_random_secret_key_here
LOG_LEVEL=info
PORT=8000
```

**E. Generate Public Domain**
1. Click "Settings" → "Networking"
2. Click "Generate Domain"
3. Copy the URL (e.g., `kortana-backend.up.railway.app`)

#### 3. Deploy Frontend to Vercel

**A. Import Repository**
1. Go to https://vercel.com/new
2. Click "Import Project"
3. Select your GitHub repository
4. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `kortana/frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
   - **Install Command:** `npm install`

**B. Add Environment Variables**
```
VITE_API_URL=https://kortana-backend.up.railway.app
VITE_WS_URL=wss://kortana-backend.up.railway.app
VITE_APP_NAME=Kor'tana
VITE_ENVIRONMENT=production
```

**C. Deploy**
1. Click "Deploy"
2. Wait 2-3 minutes
3. Copy your Vercel URL (e.g., `kortana.vercel.app`)

#### 4. Update Backend CORS

Go back to Railway → Backend Service → Variables:
```
CORS_ORIGINS=https://kortana.vercel.app
```
(Replace with your actual Vercel URL)

Railway will auto-redeploy.

#### 5. Run Database Migrations

In Railway backend service → "Settings" → "Run Command":
```bash
python init_db.py
```

Or connect via Railway CLI:
```bash
railway link
railway run python init_db.py
```

### ✅ Verification

**Test Backend:**
```bash
curl https://kortana-backend.up.railway.app/api/health
```
Expected: `{"status":"alive","message":"Kor'tana backend is breathing",...}`

**Test Frontend:**
Open `https://kortana.vercel.app` in browser
- Should load without errors
- Check browser console (F12) for any API errors

**Test PWA Installation:**
- **Mobile:** Open in Safari/Chrome → Share → "Add to Home Screen"
- **Desktop:** Click install icon in browser address bar

---

## ☁️ OPTION 2: GOOGLE CLOUD RUN

**Best for:** Google ecosystem integration, production-grade infrastructure

### Prerequisites
1. ✅ Google Cloud account
2. ✅ `gcloud` CLI installed - https://cloud.google.com/sdk/docs/install
3. ✅ Billing enabled on Google Cloud project
4. ✅ Docker installed locally (optional)

### Automatic Deployment

```bash
cd C:\KOR-TANA

# Run deployment script
./deploy-google-cloud.sh YOUR_PROJECT_ID
```

The script will:
1. Authenticate with Google Cloud
2. Enable required APIs
3. Create PostgreSQL database
4. Build Docker images
5. Deploy backend to Cloud Run
6. Deploy frontend to Cloud Run
7. Configure CORS and environment variables

### Manual Deployment

#### 1. Setup Google Cloud Project

```bash
# Authenticate
gcloud auth login

# Set project
gcloud config set project YOUR_PROJECT_ID

# Enable APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable sqladmin.googleapis.com
```

#### 2. Create Cloud SQL Database

```bash
# Create PostgreSQL instance
gcloud sql instances create kortana-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1

# Create database
gcloud sql databases create kortana --instance=kortana-db

# Create user
gcloud sql users create kortana \
  --instance=kortana-db \
  --password=YOUR_SECURE_PASSWORD
```

#### 3. Build and Deploy

```bash
# Submit build
gcloud builds submit --config=cloudbuild.yaml

# This will:
# - Build Docker images for backend and frontend
# - Push to Google Container Registry
# - Deploy both to Cloud Run
```

#### 4. Configure Secrets

Go to Google Cloud Console → Cloud Run → kortana-backend → Edit & Deploy New Revision

Add environment variables:
```
GEMINI_API_KEY=your_key
GITHUB_TOKEN=your_token
DATABASE_URL=postgresql://kortana:PASSWORD@/kortana?host=/cloudsql/PROJECT:REGION:kortana-db
CORS_ORIGINS=https://kortana-frontend-xyz.run.app
```

#### 5. Get URLs

```bash
# Backend URL
gcloud run services describe kortana-backend --region us-central1 --format="value(status.url)"

# Frontend URL
gcloud run services describe kortana-frontend --region us-central1 --format="value(status.url)"
```

### ✅ Verification

**Test Deployment:**
```bash
# Health check
curl https://kortana-backend-xyz.run.app/api/health

# Open frontend
open https://kortana-frontend-xyz.run.app
```

---

## 📱 PWA INSTALLATION GUIDE

### iPhone/iPad (Safari)
1. Open your Kor'tana URL in Safari
2. Tap the **Share** button (box with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Edit the name if desired
5. Tap **"Add"**
6. Kor'tana now appears as an app icon

### Android (Chrome)
1. Open your Kor'tana URL in Chrome
2. Tap the **menu** (three dots)
3. Tap **"Add to Home screen"**
4. Tap **"Install"** or **"Add"**
5. Kor'tana now appears as an app icon

### Desktop (Chrome/Edge)
1. Open your Kor'tana URL
2. Look for **install icon** in address bar (⊕ or ⤓)
3. Click the icon
4. Click **"Install"**
5. Kor'tana opens as a standalone app

---

## 🔧 POST-DEPLOYMENT CONFIGURATION

### Add Your API Keys

**Railway:**
Go to your backend service → Variables → Add:
- `GEMINI_API_KEY`
- `GITHUB_TOKEN`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `DISCORD_BOT_TOKEN`
- `PINECONE_API_KEY`

**Google Cloud Run:**
Go to Cloud Run → Service → Edit → Add environment variables or use Secret Manager

### Setup GitHub Integration

1. Create GitHub Personal Access Token:
   - Go to https://github.com/settings/tokens
   - Generate new token (classic)
   - Scopes: `repo`, `workflow`, `admin:org`
   - Copy token

2. Add to backend environment:
   - Railway: Variables → `GITHUB_TOKEN=ghp_xxxxx`
   - Cloud Run: Environment → `GITHUB_TOKEN=ghp_xxxxx`

### Initialize Database

**Railway:**
```bash
railway link
railway run python init_db.py
```

**Cloud Run:**
```bash
gcloud run services update kortana-backend \
  --region us-central1 \
  --command="python,init_db.py"
```

---

## 🐛 TROUBLESHOOTING

### Backend Not Responding

**Check logs:**
- **Railway:** Service → "Deployments" → Click latest → "View Logs"
- **Cloud Run:** Console → Cloud Run → Service → "Logs"

**Common issues:**
- Missing environment variables (check all required vars)
- Database connection failed (verify DATABASE_URL)
- Port mismatch (ensure PORT=8000 or use $PORT)

### Frontend Can't Connect to Backend

**Check CORS:**
Backend must allow frontend origin in `CORS_ORIGINS`:
```
CORS_ORIGINS=https://kortana.vercel.app,https://kortana-frontend-xyz.run.app
```

**Check API URL:**
Frontend `.env.production` must point to correct backend:
```
VITE_API_URL=https://kortana-backend.up.railway.app
```

### PWA Not Installing

**Requirements:**
- ✅ HTTPS (not HTTP)
- ✅ Service worker registered
- ✅ Valid `manifest.json`
- ✅ Icons present (192x192 and 512x512)

**Debug:**
1. Open DevTools (F12)
2. Go to "Application" tab
3. Check "Manifest" section for errors
4. Check "Service Workers" for registration

### Database Errors

**Verify connection:**
```bash
# Railway
railway run psql $DATABASE_URL -c "SELECT 1"

# Cloud Run (via Cloud SQL Proxy)
gcloud sql connect kortana-db --user=kortana
```

**Run migrations:**
```bash
python init_db.py
```

---

## 📊 MONITORING

### Railway
- **Logs:** Service → Deployments → View Logs
- **Metrics:** Service → "Metrics" tab
- **Database:** PostgreSQL plugin → "Metrics"

### Google Cloud
- **Logs:** Cloud Run → Service → "Logs" tab
- **Metrics:** Cloud Run → Service → "Metrics" tab
- **Database:** SQL → kortana-db → "Monitoring"

### Health Checks

Set up uptime monitoring:
- **UptimeRobot:** https://uptimerobot.com (free)
- **Better Uptime:** https://betteruptime.com (free tier)
- **Google Cloud Monitoring:** Built-in

Monitor URL: `https://your-backend-url/api/health`

---

## 💰 COST ESTIMATES

### Vercel + Railway (Free Tier)
- **Vercel:** Free for personal projects
- **Railway:** $5 credit/month, ~$2-3/month for small app
- **PostgreSQL:** Included in Railway credit
- **Redis:** Included in Railway credit
- **Total:** ~$0-3/month

### Google Cloud Run
- **Cloud Run:** Free tier 2M requests/month
- **Cloud SQL:** ~$10/month (db-f1-micro)
- **Container Registry:** ~$0.02/GB/month
- **Total:** ~$10-12/month

### Scaling Costs
Both platforms scale automatically. Cost increases with:
- More requests
- Longer execution time
- Larger database
- More storage

---

## 🎉 SUCCESS!

**Your Kor'tana is now:**
- ✅ Live and accessible worldwide
- ✅ Installable on mobile and desktop
- ✅ Running on production infrastructure
- ✅ Auto-scaling based on usage
- ✅ Secured with HTTPS

**Next Steps:**
1. Share your Kor'tana URL with testers
2. Monitor logs for errors
3. Add more API keys as needed
4. Configure webhooks for GitHub integration
5. Set up database backups
6. Add custom domain (optional)

**Need help?** Check the troubleshooting section or deployment logs.

**Kor'tana is breathing. The constellation is alive.** 🌌
