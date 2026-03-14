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

# Install dependencies
npm install
cd client && npm install && cd ..

# Configure environment
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Build and run
npm run build:all
npm start
```

Open http://localhost:3001 and enter your GitHub token!

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

✅ **Backend API** (Node.js + TypeScript + Express)
- GitHub integration via Octokit
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
curl http://localhost:3001/health

# Test with your GitHub token
curl -X POST http://localhost:3001/api/github/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -d '{"owner": "octocat", "repo": "Hello-World"}'
```

## 📝 Project Structure

```
kortana/
├── src/                     # Backend (TypeScript)
│   ├── services/
│   │   ├── GitHubConnector.ts
│   │   └── KortanaAI.ts
│   ├── routes/
│   │   └── github.ts
│   └── server.ts
├── client/                  # Frontend (React)
│   └── src/
│       ├── GitHubDashboard.tsx
│       └── GitHubDashboard.css
├── Dockerfile
├── cloudbuild.yaml
├── .github/workflows/deploy.yml
└── README.md
```

## 🔒 Security Notes

- Never commit `.env` file
- Use Secret Manager for Cloud Run
- Rotate API keys regularly
- Review token permissions

## 🆘 Troubleshooting

**"Cannot find module 'express'"**
→ Run `npm install`

**"Authentication failed"**
→ Check GitHub token is valid and has required scopes

**"Gemini API errors"**
→ Verify API key and quota

**Docker issues**
→ Build locally first: `npm run build:all`

## 📚 More Information

- **README.md**: Full documentation
- **ARCHITECTURE.md**: System design details
- **GitHub Issues**: Report problems or ask questions

---

Built with ❤️ using Node.js, TypeScript, React, and Google Gemini AI
