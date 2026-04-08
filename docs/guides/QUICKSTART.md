# Kor'tana Setup Guide - Quick Start

## 🚀 Quick Setup (5 minutes)

### 1. Get API Keys

#### GitHub Personal Access Token
1. Visit: https://github.com/settings/tokens/new
2. Name: "Kortana Integration"
3. Scopes: ✅ `repo`, ✅ `read:user`
4. Generate and copy token

#### Google Gemini API Key
1. Visit: https://makersuite.google.com/app/apikey
2. Create API key
3. Copy key

### 2. Local Setup

```bash
# Clone repository
git clone https://github.com/KOR-TANA/kortana.git
cd kortana

# Install Python dependencies
cd backend
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY and GITHUB_TOKEN

# Start the backend
uvicorn main:app --reload --port 8000
```

Open http://localhost:8000/docs and enter your GitHub token!

### 3. Cloud Run Deployment

#### Prerequisites
- Google Cloud Project
- Service account with Cloud Run Admin permissions

#### Setup
```bash
# Store Gemini API key in Secret Manager
echo -n "your_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-

# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

#### GitHub Actions (Automatic)
1. Add GitHub Secrets:
   - `GCP_PROJECT_ID`: Your project ID
   - `GCP_SA_KEY`: Service account JSON key
2. Push to main branch → automatic deployment!

## 📖 What's Included

✅ **Backend API** (FastAPI + Python + Uvicorn)
- GitHub integration via PyGitHub
- Gemini AI analysis
- RESTful API endpoints

✅ **Frontend Dashboard** (React + TypeScript)
- Beautiful gradient UI
- Real-time data display
- AI-powered insights

✅ **DevOps**
- Docker containerization
- GitHub Actions CI/CD
- Cloud Build configuration
- Automated deployments

✅ **Documentation**
- Comprehensive README
- Architecture guide
- Setup instructions
- API documentation

## 🎯 Quick Test

```bash
# Test backend
curl http://localhost:8000/api/health

# Test with your GitHub token
curl -X POST http://localhost:8000/api/github/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -d '{"owner": "octocat", "repo": "Hello-World"}'
```

## 📝 Project Structure

```
kortana/
├── backend/                     # Backend (Python/FastAPI)
│   ├── main.py                  # Application entry point
│   ├── requirements.txt         # Python dependencies
│   ├── routers/                 # API route handlers
│   │   ├── github.py            # GitHub integration
│   │   ├── gemini.py            # AI analysis
│   │   └── agents.py            # Agent management
│   └── config.py                # Configuration
├── frontend/                    # Frontend (React)
│   └── src/
│       ├── App.tsx              # Main application
│       └── components/          # UI components
├── Dockerfile                   # Container build
├── cloudbuild.yaml              # Cloud deployment
├── .github/workflows/deploy.yml # CI/CD pipeline
└── README.md                    # Documentation
```

## 🔒 Security Notes

- Never commit `.env` file
- Use Secret Manager for Cloud Run
- Rotate API keys regularly
- Review token permissions

## 🆘 Troubleshooting

**"Module not found"**
→ Run `pip install -r requirements.txt`

**"Authentication failed"**
→ Check GitHub token is valid and has required scopes

**"Gemini API errors"**
→ Verify API key and quota

**Docker issues**
→ Build locally first: `docker build -t kortana .`

## 📚 More Information

- **README.md**: Full documentation
- **ARCHITECTURE.md**: System design details
- **GitHub Issues**: Report problems or ask questions

---

Built with ❤️ using FastAPI, Python, React, and Google Gemini AI