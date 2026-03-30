# 🌌 Kor'tana Quick Deploy
**Get Kor'tana running in 10 minutes**

## Choose Your Path

### 🚀 FASTEST: Vercel + Railway (~10 mins)
```bash
# 1. Push to GitHub
git init
git add .
git commit -m "Deploy Kor'tana"
git remote add origin https://github.com/YOUR_USERNAME/kortana.git
git push -u origin main

# 2. Run deployment wizard
./deploy-vercel-railway.sh
```

Follow the interactive prompts to:
1. Deploy backend to Railway
2. Deploy frontend to Vercel
3. Connect them together

**Result:** `https://kortana.vercel.app` (your live app)

---

### ☁️ GOOGLE CLOUD: One Command (~15 mins)
```bash
# Prerequisites: gcloud CLI installed
gcloud auth login

# Deploy everything
./deploy-google-cloud.sh YOUR_PROJECT_ID
```

**Result:** `https://kortana-frontend-xyz.run.app` (your live app)

---

## What You Need

### For Both Options:
- ✅ API Keys:
  - Gemini API: https://aistudio.google.com/apikey
  - GitHub Token: https://github.com/settings/tokens
  - (Optional) OpenAI, Anthropic, etc.

### For Vercel + Railway:
- ✅ GitHub account
- ✅ Vercel account (free): https://vercel.com/signup
- ✅ Railway account (free): https://railway.app/signup

### For Google Cloud:
- ✅ Google Cloud account
- ✅ gcloud CLI: https://cloud.google.com/sdk/docs/install
- ✅ Billing enabled (uses free tier)

---

## After Deployment

### Test Your App
```bash
# Backend health check
curl https://your-backend-url/api/health

# Frontend
open https://your-frontend-url
```

### Install as Mobile App
**iPhone/iPad:**
1. Open in Safari
2. Tap Share → "Add to Home Screen"

**Android:**
1. Open in Chrome
2. Menu → "Add to Home screen"

**Desktop:**
1. Open in browser
2. Click install icon in address bar

---

## Need Help?

1. **Full Guide:** See `DEPLOYMENT_GUIDE.md`
2. **Troubleshooting:** Check deployment logs
3. **Logs:**
   - Railway: Dashboard → Service → Logs
   - Cloud Run: Console → Cloud Run → Logs

---

**Ready?** Pick a path above and deploy Kor'tana now! 🌌
