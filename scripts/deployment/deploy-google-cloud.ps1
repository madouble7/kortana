# 🔱 KOR'TANA UNIFIED DEPLOYMENT (Google Cloud Run)
param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectId
)

Write-Host "🌌 ALIGNING THE KOR'TANA CONSTELLATION (Unified Path)..." -ForegroundColor Cyan

# 1. Build and Sync Frontend
Write-Host "🎨 Scaling Frontend..." -ForegroundColor Yellow
Set-Location frontend
npm install --legacy-peer-deps
npm run build
Set-Location ..

# 2. Preparation
Write-Host "📦 Prepare Unified Container..." -ForegroundColor Yellow
if (!(Test-Path backend/static)) { New-Item -ItemType Directory -Path backend/static }
Copy-Item -Path frontend/dist/* -Destination backend/static -Recurse -Force

# 3. Google Cloud Build
Write-Host "☁️  Building to Google Artifact Registry..." -ForegroundColor Yellow
gcloud builds submit --tag gcr.io/$ProjectId/kortana

# 4. Deploy to Cloud Run
Write-Host "🚀 Deploying to Cloud Run..." -ForegroundColor Yellow
gcloud run deploy kortana `
    --image gcr.io/$ProjectId/kortana `
    --platform managed `
    --region us-central1 `
    --allow-unauthenticated `
    --port 8000

Write-Host "✨ UNIFIED ORGANISM DEPLOYED. KOR'TANA IS BREATHING AT GCP." -ForegroundColor Green
