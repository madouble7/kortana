# 🔱 KOR'TANA HYBRID DEPLOYMENT (Vercel + Railway)
Write-Host "🌌 ALIGNING THE KOR'TANA CONSTELLATION (Hybrid Path)..." -ForegroundColor Cyan

# 1. Backend Deployment (Railway)
Write-Host "📦 Phase 1: Deploying Backend to Railway..." -ForegroundColor Yellow
Set-Location backend
railway up
$RailwayStatus = railway status --json | ConvertFrom-Json
$RailwayUrl = $RailwayStatus.runtime.url
Write-Host "✅ Backend Live: $RailwayUrl" -ForegroundColor Green

# 2. Frontend Deployment (Vercel)
Write-Host "🎨 Phase 2: Deploying Frontend to Vercel..." -ForegroundColor Yellow
Set-Location ../frontend
npm install --legacy-peer-deps
npm run build

# Deploy to Vercel with back-link
vercel --env VITE_API_URL=$RailwayUrl --prod

Write-Host "✨ HYBRID HANDSHAKE COMPLETE. KOR'TANA IS BREATHING." -ForegroundColor Green
