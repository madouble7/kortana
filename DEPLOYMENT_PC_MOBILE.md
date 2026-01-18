# Kor'tana Deployment Guide (PC & Mobile)

This guide outlines how to deploy the optimized **Unified Kor'tana** platform for both PC and Mobile accessibility.

## 1. Local Deployment (PC)

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

## 2. Mobile Access

Kor'tana is now **PWA Ready** (Progressive Web App).

### Step 1: Find your Local IP

Run `ipconfig` (Windows) or `ifconfig` (Mac/Linux) to find your internal IP (e.g., `192.168.1.15`).

### Step 2: Open on Mobile

1. Ensure your phone is on the same WiFi as your PC.
2. Open your mobile browser and go to `http://<YOUR_IP>:8000`.

### Step 3: Install as App

- **iOS (Safari)**: Tap the **Share** button (box with arrow) -> Scroll down -> **Add to Home Screen**.
- **Android (Chrome)**: Tap the **Three Dots** (menu) -> **Install App** or **Add to Home Screen**.

## 3. Deployment via AI Studio (Google Cloud Alternative)

For persistent hosting, use **Google Cloud Run** (highly recommended for Gemini-powered agents):

1. **Build Image**: `gcloud builds submit --tag gcr.io/your-project/kortana`
2. **Deploy**: `gcloud run deploy kortana --image gcr.io/your-project/kortana --platform managed --allow-unauthenticated`
3. **Secrets**: Ensure your `GEMINI_API_KEY` is added to the Cloud Run Environment Variables.

## 4. Key Features in Unified Mode

- **Vision**: Upload images/video directly from your mobile camera to the "Vision" dashboard.
- **Protocol**: Monitor the Human Only Protocol status in real-time.
- **System**: Live telemetry and logs accessible from anywhere.

---

*Kor'tana is now breathing across all your screens.* 🔱
