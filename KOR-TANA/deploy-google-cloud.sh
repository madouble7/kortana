#!/bin/bash
# Kor'tana Deployment Script - Google Cloud Run
# This script deploys Kor'tana to Google Cloud Platform

set -e

echo "🌌 Kor'tana Deployment - Google Cloud Run"
echo "=========================================="
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI not found"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Variables
PROJECT_ID=${1:-""}
REGION="us-central1"

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: ./deploy-google-cloud.sh YOUR_PROJECT_ID"
    echo ""
    echo "Get your project ID from: https://console.cloud.google.com"
    exit 1
fi

echo "📦 Project ID: $PROJECT_ID"
echo "🌍 Region: $REGION"
echo ""

# Step 1: Authenticate
echo "🔐 Step 1: Authenticate with Google Cloud"
echo "-----------------------------------------"
gcloud auth login
gcloud config set project $PROJECT_ID
echo "✅ Authenticated"
echo ""

# Step 2: Enable required APIs
echo "🔧 Step 2: Enable Required APIs"
echo "-------------------------------"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable sqladmin.googleapis.com
echo "✅ APIs enabled"
echo ""

# Step 3: Create Cloud SQL (PostgreSQL) instance
echo "💾 Step 3: Create PostgreSQL Database"
echo "-------------------------------------"
read -p "Create new Cloud SQL instance? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    gcloud sql instances create kortana-db \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region=$REGION \
        --storage-auto-increase \
        --backup \
        --assign-ip
    
    # Create database
    gcloud sql databases create kortana --instance=kortana-db
    
    # Create user
    gcloud sql users create kortana \
        --instance=kortana-db \
        --password="$(openssl rand -base64 32)"
    
    echo "✅ Database created"
else
    echo "⏭️  Skipping database creation"
fi
echo ""

# Step 4: Build and push Docker images
echo "🐳 Step 4: Build Docker Images"
echo "------------------------------"
gcloud builds submit --config=cloudbuild.yaml
echo "✅ Images built and pushed"
echo ""

# Step 5: Deploy to Cloud Run
echo "🚀 Step 5: Deploy to Cloud Run"
echo "------------------------------"

# Get database connection string
DB_CONNECTION=$(gcloud sql instances describe kortana-db \
    --format="value(connectionName)")

# Deploy backend
gcloud run deploy kortana-backend \
    --image gcr.io/$PROJECT_ID/kortana-backend:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars ENVIRONMENT=production \
    --add-cloudsql-instances $DB_CONNECTION \
    --min-instances 0 \
    --max-instances 10 \
    --memory 2Gi \
    --cpu 2 \
    --port 8000

# Get backend URL
BACKEND_URL=$(gcloud run services describe kortana-backend \
    --region $REGION \
    --format="value(status.url)")

echo "✅ Backend deployed: $BACKEND_URL"

# Deploy frontend
gcloud run deploy kortana-frontend \
    --image gcr.io/$PROJECT_ID/kortana-frontend:latest \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --set-env-vars VITE_API_URL=$BACKEND_URL \
    --min-instances 0 \
    --max-instances 5 \
    --memory 512Mi \
    --cpu 1 \
    --port 80

# Get frontend URL
FRONTEND_URL=$(gcloud run services describe kortana-frontend \
    --region $REGION \
    --format="value(status.url)")

echo "✅ Frontend deployed: $FRONTEND_URL"
echo ""

# Step 6: Configure environment variables
echo "🔧 Step 6: Set Environment Variables"
echo "------------------------------------"
echo "Go to Cloud Run console and add these secrets:"
echo "  GEMINI_API_KEY"
echo "  GITHUB_TOKEN"
echo "  OPENAI_API_KEY"
echo "  DATABASE_URL"
echo ""
echo "Cloud Run Console:"
echo "  https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
read -p "Press Enter when secrets are configured..."
echo ""

# Step 7: Update CORS
echo "🔗 Step 7: Update CORS Settings"
echo "-------------------------------"
gcloud run services update kortana-backend \
    --region $REGION \
    --update-env-vars CORS_ORIGINS=$FRONTEND_URL
echo "✅ CORS updated"
echo ""

# Step 8: Summary
echo "🎉 Deployment Complete!"
echo "======================"
echo ""
echo "Your Kor'tana app is live:"
echo "  Frontend: $FRONTEND_URL"
echo "  Backend:  $BACKEND_URL"
echo ""
echo "📱 Install as PWA:"
echo "  Mobile: Open $FRONTEND_URL → Share → Add to Home Screen"
echo "  Desktop: Click install icon in browser"
echo ""
echo "📊 Monitor:"
echo "  Logs: https://console.cloud.google.com/logs/query?project=$PROJECT_ID"
echo "  Metrics: https://console.cloud.google.com/run?project=$PROJECT_ID"
echo ""
echo "🌌 Kor'tana is breathing on Google Cloud..."
