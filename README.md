# 🚀 Kor'tana - AI-Powered GitHub Integration Service

Kor'tana is a Node.js + TypeScript service with a React frontend that connects to GitHub and uses Google's Gemini AI to analyze repositories, issues, and pull requests.

## Features

- 🔐 **GitHub Authentication**: Secure OAuth-based GitHub integration
- 📊 **Repository Analysis**: View issues and pull requests from your repositories
- 🤖 **AI-Powered Insights**: Leverages Google Gemini AI to analyze and provide actionable insights
- 🎨 **Modern UI**: Beautiful React dashboard with real-time data
- 🐳 **Docker Support**: Containerized for easy deployment
- ☁️ **Cloud Run Ready**: CI/CD pipeline for Google Cloud Run

## Architecture

```
kortana/
├── src/                          # Backend (Node.js + TypeScript)
│   ├── services/
│   │   ├── GitHubConnector.ts   # GitHub API integration
│   │   └── KortanaAI.ts         # Gemini AI integration
│   ├── routes/
│   │   └── github.ts            # API routes
│   └── server.ts                # Express server
├── client/                       # Frontend (React + TypeScript)
│   └── src/
│       ├── GitHubDashboard.tsx  # Main dashboard component
│       └── GitHubDashboard.css  # Dashboard styles
├── .github/workflows/
│   └── deploy.yml               # CI/CD pipeline
└── Dockerfile                    # Multi-stage Docker build
```

## Prerequisites

- Node.js 20 or higher
- npm or yarn
- GitHub Personal Access Token
- Google Gemini API Key

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/KOR-TANA/kortana.git
cd kortana
```

### 2. Install Dependencies

Install backend dependencies:
```bash
npm install
```

Install frontend dependencies:
```bash
cd client
npm install
cd ..
```

### 3. Configure Environment Variables

Create a `.env` file in the root directory:

```bash
cp .env.example .env
```

Edit `.env` with your credentials:

```env
# Server Configuration
PORT=3001
NODE_ENV=development

# GitHub Configuration
GITHUB_TOKEN=your_github_token_here

# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Obtain Required API Keys

#### GitHub Personal Access Token

1. Go to https://github.com/settings/tokens/new
2. Give your token a descriptive name (e.g., "Kor'tana Integration")
3. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:user` (Read user profile data)
4. Click "Generate token"
5. Copy the token and add it to your `.env` file

#### Google Gemini API Key

1. Go to https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key and add it to your `.env` file

## Running the Application

### Development Mode

Run both backend and frontend concurrently:
```bash
npm run dev:all
```

Or run them separately:

Backend only:
```bash
npm run dev
```

Frontend only:
```bash
npm run client
```

The backend will run on `http://localhost:3001` and the frontend on `http://localhost:3000`.

### Production Mode

Build the application:
```bash
npm run build:all
```

Start the production server:
```bash
npm start
```

The server will serve both the API and the React frontend on `http://localhost:3001`.

## API Endpoints

### Authentication
All endpoints require a GitHub Personal Access Token in the Authorization header:
```
Authorization: Bearer YOUR_GITHUB_TOKEN
```

### Available Endpoints

- `GET /health` - Health check endpoint
- `GET /api/github/user` - Get authenticated user information
- `GET /api/github/repos` - Get user's repositories
- `GET /api/github/repos/:owner/:repo` - Get specific repository
- `GET /api/github/repos/:owner/:repo/issues` - Get repository issues
- `GET /api/github/repos/:owner/:repo/pulls` - Get repository pull requests
- `POST /api/github/analyze` - Analyze repository with Gemini AI

### Example API Call

```bash
curl -X POST http://localhost:3001/api/github/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -d '{"owner": "KOR-TANA", "repo": "kortana"}'
```

## Docker Deployment

### Build the Docker Image

```bash
docker build -t kortana .
```

### Run the Container

```bash
docker run -p 8080:8080 \
  -e GEMINI_API_KEY=your_gemini_api_key \
  kortana
```

## Google Cloud Run Deployment

### Prerequisites

- Google Cloud Project
- Google Cloud SDK installed
- Service account with Cloud Run Admin permissions

### Setup Secrets

Store your Gemini API key in Google Secret Manager:

```bash
echo -n "your_gemini_api_key" | gcloud secrets create GEMINI_API_KEY --data-file=-
```

### Configure GitHub Secrets

Add the following secrets to your GitHub repository:

- `GCP_PROJECT_ID`: Your Google Cloud Project ID
- `GCP_SA_KEY`: Service account JSON key

### Deploy

The deployment happens automatically via GitHub Actions when you push to the `main` branch. You can also deploy manually:

```bash
# Build and push Docker image
gcloud builds submit --tag gcr.io/PROJECT_ID/kortana

# Deploy to Cloud Run
gcloud run deploy kortana \
  --image gcr.io/PROJECT_ID/kortana \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-secrets "GEMINI_API_KEY=GEMINI_API_KEY:latest"
```

## Usage

1. **Open the Application**: Navigate to `http://localhost:3000` (or your deployed URL)
2. **Authenticate**: Enter your GitHub Personal Access Token
3. **Select Repository**: Choose a repository from the dropdown
4. **View Data**: See issues and pull requests
5. **Analyze**: Click "Analyze with Kor'tana AI" to get AI-powered insights

## Security Considerations

⚠️ **Important Security Notes:**

- Never commit your `.env` file or expose API keys
- Use environment variables for all sensitive configuration
- Rotate API keys regularly
- Use minimal required scopes for GitHub tokens
- Enable 2FA on your GitHub account
- Review Cloud Run IAM permissions regularly

## Secrets Configuration

### Required Secrets

| Secret Name | Description | Where to Get |
|-------------|-------------|--------------|
| `GITHUB_TOKEN` | GitHub Personal Access Token | https://github.com/settings/tokens/new |
| `GEMINI_API_KEY` | Google Gemini API Key | https://makersuite.google.com/app/apikey |
| `GCP_PROJECT_ID` | Google Cloud Project ID | Your GCP Console |
| `GCP_SA_KEY` | Service Account JSON Key | GCP IAM & Admin |

### Local Development
Store secrets in `.env` file (never commit this file).

### Cloud Run Deployment
Store secrets in Google Secret Manager and reference them in the deployment.

### GitHub Actions
Store secrets in GitHub repository settings under Settings → Secrets and variables → Actions.

## Troubleshooting

### Common Issues

**Port already in use:**
```bash
# Change PORT in .env file or kill the process
lsof -ti:3001 | xargs kill -9
```

**Authentication failed:**
- Verify your GitHub token has the correct scopes
- Check if the token has expired
- Ensure the token is correctly set in the Authorization header

**Gemini API errors:**
- Verify your API key is correct
- Check API quota limits
- Ensure the API is enabled in your Google Cloud project

**Docker build fails:**
- Ensure all dependencies are installed
- Check Docker daemon is running
- Verify sufficient disk space

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check existing documentation
- Review error logs in the console

---

Built with ❤️ using Node.js, TypeScript, React, and Google Gemini AI

