#!/bin/bash
# 🔱 KOR'TANA UNIFIED DEPLOYMENT (Google Cloud Run)
# This script scaffolds the deployment as a single unified container.

PROJECT_ID=$1

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Usage: bash deploy-google-cloud.sh [YOUR_PROJECT_ID]"
    exit 1
fi

echo "🌌 ALIGNING THE KOR'TANA CONSTELLATION (Unified Path)..."

# 1. Build and Sync Frontend
echo "🎨 Scaling Frontend..."
cd frontend
npm install --legacy-peer-deps
npm run build
cd ..

# 2. Preparation
echo "📦 Prepare Unified Container..."
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

# 3. Google Cloud Build
echo "☁️  Building to Google Artifact Registry..."
gcloud builds submit --tag gcr.io/$PROJECT_ID/kortana

# 4. Deploy to Cloud Run
echo "🚀 Deploying to Cloud Run..."
gcloud run deploy kortana \
  --image gcr.io/$PROJECT_ID/kortana \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8000

echo "✨ UNIFIED ORGANISM DEPLOYED. KOR'TANA IS BREATHING AT GCP."
