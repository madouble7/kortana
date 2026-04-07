# Google Cloud Run Deployment Setup Guide

## Overview
Deploy the Kor'tana FastAPI backend to Google Cloud Run for production operation. This enables:
- Live API endpoints for autonomous workflows
- Elevation rituals to access Cloud Run deployment
- Scalable backend for GitHub issue analysis
- Secure OIDC authentication with GitHub Actions

## Prerequisites

### 1. Google Cloud Project
1. **Create GCP Project**: `kor-tana-project` (or update PROJECT_ID in workflow)
2. **Enable APIs**:
   - Cloud Run API
   - Container Registry API
   - IAM Service Account Credentials API
   - Cloud Build API

### 2. Service Account Setup
1. **Create Service Account**:
   - Name: `kortana-deployer`
   - Description: Service account for Cloud Run deployments

2. **Grant Roles**:
   - `Cloud Run Admin`
   - `Storage Admin` (for Container Registry)
   - `Service Account User`
   - `IAM Workload Identity User`

3. **Create JSON Key** (for initial setup):
   - Download the JSON key file
   - Add as GitHub secret: `GCP_SA_KEY`

### 3. Workload Identity Federation (OIDC)
1. **Create Workload Identity Pool**:
   - Name: `github-actions-pool`
   - Provider: `github-actions-provider`

2. **Configure Provider**:
   - Issuer: `https://token.actions.githubusercontent.com`
   - Audience: `https://github.com/KOR-TANA`

3. **Grant Access**:
   - Connect service account to workload identity
   - Attribute mapping: `google.subject=assertion.sub`

## GitHub Secrets Configuration

Add these secrets to your repository:

### Required Secrets
```bash
# GCP Service Account (for OIDC auth)
GCP_WORKLOAD_IDENTITY_PROVIDER=projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/providers/github-actions-provider
GCP_SERVICE_ACCOUNT=kortana-deployer@kor-tana-project.iam.gserviceaccount.com

# API Keys (stored in GCP Secret Manager)
GEMINI_API_KEY=your_gemini_api_key_here
GITHUB_TOKEN=your_github_token_here
```

### Optional Secrets
```bash
# For enhanced security
CORS_ORIGINS=https://kortana.ai,https://vscode.dev
ENVIRONMENT=production
```

## Step-by-Step Setup

### Step 1: Configure GCP Project
```bash
# Set project
gcloud config set project kor-tana-project

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable iamcredentials.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 2: Create Secrets in GCP
```bash
# Create secrets for API keys
echo -n "your-gemini-api-key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your-github-token" | gcloud secrets create GITHUB_TOKEN --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:kortana-deployer@kor-tana-project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

gcloud secrets add-iam-policy-binding GITHUB_TOKEN \
    --member="serviceAccount:kortana-deployer@kor-tana-project.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### Step 3: Set Up Workload Identity
```bash
# Create workload identity pool
gcloud iam workload-identity-pools create github-actions-pool \
    --project=kor-tana-project \
    --location=global \
    --display-name="GitHub Actions Pool"

# Create OIDC provider
gcloud iam workload-identity-pools providers create-oidc github-actions-provider \
    --project=kor-tana-project \
    --location=global \
    --workload-identity-pool=github-actions-pool \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
    --issuer-uri="https://token.actions.githubusercontent.com"

# Allow service account to be impersonated
gcloud iam service-accounts add-iam-policy-binding kortana-deployer@kor-tana-project.iam.gserviceaccount.com \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-actions-pool/attribute.repository/KOR-TANA/kortana"
```

### Step 4: Update GitHub Secrets
1. **Get Workload Identity Provider ID**:
   ```bash
   gcloud iam workload-identity-pools providers describe github-actions-provider \
       --project=kor-tana-project \
       --location=global \
       --workload-identity-pool=github-actions-pool \
       --format="value(name)"
   ```

2. **Add to GitHub Secrets**:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`: The provider ID from above
   - `GCP_SERVICE_ACCOUNT`: `kortana-deployer@kor-tana-project.iam.gserviceaccount.com`

### Step 5: Initial Deployment
Push any change to `backend/` or the workflow file to trigger deployment:
```bash
git add .
git commit -m "feat: update backend for Cloud Run deployment"
git push origin main
```

## Verification

### Check Deployment Status
```bash
# List Cloud Run services
gcloud run services list --region=us-west1

# Get service details
gcloud run services describe kortana-backend --region=us-west1

# Check logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=kortana-backend" --limit=10
```

### Test API Endpoints
```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe kortana-backend --region=us-west1 --format="value(status.url)")

# Test health endpoint
curl -X GET "$SERVICE_URL/api/health"

# Test GitHub analysis
curl -X POST "$SERVICE_URL/api/github/analyze" \
  -H "Content-Type: application/json" \
  -d '{"type": "issue", "title": "Test Issue", "body": "Test analysis", "url": "https://github.com/test/repo/issues/1"}'
```

## Troubleshooting

### Deployment Fails
- **Check service account permissions**: Ensure all required roles are granted
- **Verify OIDC setup**: Test workload identity federation
- **Check secrets**: Ensure GCP secrets exist and are accessible

### API Returns Errors
- **Check logs**: `gcloud logging read "resource.type=cloud_run_revision"`
- **Verify environment variables**: Check secret mounting in Cloud Run
- **Test locally**: Run `docker build . && docker run -p 8000:8000 <image>`

### Authentication Issues
- **OIDC token**: Verify GitHub Actions has correct permissions
- **Service account**: Check IAM policies and workload identity binding
- **Secrets access**: Confirm service account can access GCP Secret Manager

## Security Best Practices

- **Rotate secrets regularly** (every 90 days)
- **Use least privilege** for service accounts
- **Monitor access logs** for suspicious activity
- **Enable VPC networking** if required
- **Set up alerts** for deployment failures

---

*Once Cloud Run is configured, the backend will be accessible at:*
`https://kortana-backend-[hash]-uc.a.run.app`
