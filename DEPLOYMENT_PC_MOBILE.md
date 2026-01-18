# Kor'tana Deployment Guide (PC & Mobile)

This guide outlines how to deploy the optimized **Unified Kor'tana** platform across different environments.

## 🌌 Dual-Path Deployment Options

### Path 1: Hybrid Cloud (Vercel + Railway) - Best for Scalability

This path separates the Frontend (Vercel) from the Backend (Railway + PostgreSQL), providing the best latency and cost-efficiency.

**1. Backend (Railway):**

- Connect your repo to [Railway.app](https://railway.app).
- Railway will detect the `Dockerfile` in the root (Unified mode) or you can use the `backend/` directory.
- Add your variables from `backend/.env.example` to the Railway project settings.
- Ensure `DATABASE_URL` is set to the Railway PostgreSQL connection string.

**2. Frontend (Vercel):**

- Connect your repo to [Vercel](https://vercel.com).
- Set the **Root Directory** to `frontend`.
- Build Command: `npm run build`
- Output Directory: `dist`
- Environment Variables: Set `VITE_API_URL` to your Railway backend URL (e.g., `https://kortana-api.up.railway.app`).

---

### Path 2: Unified Container (Google Cloud Run) - Best for Simplicity

This path packages everything into a single container where the Backend serves the Frontend.

**1. Local Build & Push:**

```bash
# Build the unified image
docker build -t gcr.io/[PROJECT_ID]/kortana .
# Push to registry
docker push gcr.io/[PROJECT_ID]/kortana
```

**2. Deploy to Cloud Run:**

```bash
gcloud run deploy kortana \
  --image gcr.io/[PROJECT_ID]/kortana \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars="GEMINI_API_KEY=[YOUR_KEY],ENVIRONMENT=production"
```

---

## 💻 Local Deployment (PC)

The system is now a **Single Organism**. The backend serves the frontend.

### Option A: Docker (Recommended)

Run the entire stack in production mode:

```bash
docker-compose build
docker-compose up -d
```

Access on your PC at: `http://localhost:8000`

### Option B: Local Development

Run backend and frontend separately for hot-reloading:

1. **Backend**: `python backend/main.py` (Port 8000)
2. **Frontend**: `cd frontend && npm run dev` (Port 3000)

## 📱 Mobile Access

Kor'tana is now **PWA Ready** (Progressive Web App).

### Step 1: Find your Local IP

Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) to find your internal IP (e.g., `192.168.1.15`).

### Step 2: Open on Mobile

1. Ensure your phone is on the same WiFi as your PC.
2. Open your mobile browser and go to `http://<YOUR_IP>:8000`.

### Step 3: Install as App

- **iOS (Safari)**: Tap the **Share** button (box with arrow) -> Scroll down -> **Add to Home Screen**.
- **Android (Chrome)**: Tap the **Three Dots** (menu) -> **Install App** or **Add to Home Screen**.

## 🔱 Key Features in Unified Mode

- **Vision**: Upload images/video directly from your mobile camera to the "Vision" dashboard.
- **Protocol**: Monitor the Human Only Protocol status in real-time.
- **System**: Live telemetry and logs accessible from anywhere.

---

*Kor'tana is now breathing across all your screens.* 🔱
