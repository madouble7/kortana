#!/bin/bash
# 🔱 KOR'TANA HYBRID DEPLOYMENT (Vercel + Railway)
# This script scaffolds the deployment of the unified organism across providers.

echo "🌌 ALIGNING THE KOR'TANA CONSTELLATION (Hybrid Path)..."

# 1. Backend Deployment (Railway)
echo "📦 Phase 1: Deploying Backend to Railway..."
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Please install it: npm i -g @railway/cli"
    exit 1
fi

cd backend
railway up
RAILWAY_URL=$(railway status --json | grep -o 'https://[^"]*')
echo "✅ Backend Live: $RAILWAY_URL"

# 2. Frontend Deployment (Vercel)
echo "🎨 Phase 2: Deploying Frontend to Vercel..."
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Please install it: npm i -g vercel"
    exit 1
fi

cd ../frontend
# Build locally to ensure validity
npm install --legacy-peer-deps
npm run build

# Deploy to Vercel with back-link
vercel --env VITE_API_URL=$RAILWAY_URL --prod

echo "✨ HYBRID HANDSHAKE COMPLETE. KOR'TANA IS BREATHING."
