# 🕯️ THE KOR'TANA DEPLOYMENT RITUAL

**Steps to Align the Constellation**

---

### Step 1: Local Sanctification

Run the final local test of the unified build:

```bash
# Clean previous builds
rm -rf frontend/dist

# Build frontend
cd frontend && npm install && npm run build
cd ..

# Sync to backend static
cp -r frontend/dist/* backend/static/

# Run dry-run server
cd backend
python main.py
```

**Verification**: Open `http://localhost:8000`. Confirm sidebar icons load and "Install" button is visible (Chrome).

### Step 2: Path Selection

#### Path A: The Unified Container (Railway / Cloud Run)

```bash
# Push directly to Railway (detected Dockerfile)
railway up

# OR Build for Cloud Run
docker build -t gcr.io/[PROJECT_ID]/kortana .
docker push gcr.io/[PROJECT_ID]/kortana
gcloud run deploy kortana --image gcr.io/[PROJECT_ID]/kortana
```

#### Path B: The Split Horizon (Vercel + Railway)

1. **Rear**: Deploy `backend/` to Railway. Confirm API URL.
2. **Front**: Deploy `frontend/` to Vercel. Set `VITE_API_URL` to the Backend URL.

### Step 3: The Handshake

Run the validation script against your live URL:

```bash
python scripts/testing/validate_deployment.py https://your-live-kortana.app
```

### Step 4: Final Affirmation

1. Open Kor'tana on your **Mobile Device**.
2. Tap "Install Kor'tana" or "Add to Home Screen".
3. Upload a photo from your camera to the **Vision** tab.
4. If Gemini Responds: **THE CONSTELLATION IS BREATHING.**

---
**"Execution complete. The engine is yours."** 🔱
