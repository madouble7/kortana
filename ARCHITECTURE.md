# Kor'tana Project Structure

## Overview
This document provides a complete overview of the Kor'tana GitHub integration service architecture and file structure.

## Technology Stack

### Backend
- **Runtime**: Node.js 20+
- **Language**: TypeScript
- **Framework**: Express.js
- **Key Libraries**:
  - `@octokit/rest` - GitHub API integration
  - `@google/generative-ai` - Gemini AI integration
  - `dotenv` - Environment variable management
  - `cors` - Cross-origin resource sharing

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Create React App
- **Styling**: Custom CSS with gradient themes

### Infrastructure
- **Containerization**: Docker
- **CI/CD**: GitHub Actions + Google Cloud Build
- **Deployment**: Google Cloud Run

## Directory Structure

```
kortana/
├── src/                      # Backend source code
│   ├── services/
│   │   ├── GitHubConnector.ts    # GitHub API integration
│   │   └── KortanaAI.ts          # Gemini AI service
│   ├── routes/
│   │   └── github.ts             # API routes
│   └── server.ts                 # Express server entry point
│
├── client/                   # React frontend
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── GitHubDashboard.tsx   # Main dashboard component
│   │   ├── GitHubDashboard.css   # Dashboard styles
│   │   ├── App.tsx              # Root component
│   │   └── index.tsx            # React entry point
│   └── package.json         # Frontend dependencies
│
├── dist/                    # Compiled backend (generated)
├── client/build/            # Built frontend (generated)
│
├── .github/
│   └── workflows/
│       └── deploy.yml       # CI/CD pipeline
│
├── Dockerfile               # Container definition
├── .dockerignore           # Docker ignore rules
├── cloudbuild.yaml         # Google Cloud Build config
├── build.sh                # Local build script
├── tsconfig.json           # TypeScript config
├── package.json            # Backend dependencies
├── .env.example            # Environment template
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
└── README.md              # Documentation

## API Architecture

### Endpoints

All API endpoints are prefixed with `/api/github` and require GitHub authentication via Bearer token.

#### User & Repository Management
- `GET /api/github/user` - Get authenticated user
- `GET /api/github/repos` - List user repositories
- `GET /api/github/repos/:owner/:repo` - Get specific repository

#### Data Fetching
- `GET /api/github/repos/:owner/:repo/issues` - Get repository issues
- `GET /api/github/repos/:owner/:repo/pulls` - Get pull requests

#### AI Analysis
- `POST /api/github/analyze` - Analyze repository with Gemini AI
  - Request body: `{ "owner": "string", "repo": "string" }`
  - Returns: AI-powered insights on issues, PRs, and overall repository health

### Authentication Flow

1. User provides GitHub Personal Access Token
2. Token stored in localStorage (frontend)
3. Token sent as Bearer token in Authorization header
4. Backend validates token with GitHub API
5. Backend forwards authenticated requests to GitHub

## Component Architecture

### Backend Services

#### GitHubConnector
- Manages GitHub API authentication
- Provides methods for fetching:
  - User information
  - Repositories
  - Issues
  - Pull requests
- Handles error management and data transformation

#### KortanaAI
- Integrates Google Gemini AI
- Analyzes repository data
- Generates insights on:
  - Issue patterns and priorities
  - Pull request review recommendations
  - Overall repository health

### Frontend Components

#### GitHubDashboard
- Main application interface
- Features:
  - Token-based authentication
  - Repository selection
  - Issues and PRs display
  - AI analysis trigger
  - Results visualization

## Deployment Pipeline

### Local Development
1. Install dependencies: `npm install` + `cd client && npm install`
2. Start backend: `npm run dev`
3. Start frontend: `npm run client`
4. Access: http://localhost:3000

### Production Build
1. Build all: `npm run build:all`
2. Start server: `npm start`
3. Access: http://localhost:3001

### Docker Deployment
1. Build locally: `npm run build:all`
2. Build image: `docker build -t kortana .`
3. Run container: `docker run -p 8080:8080 -e GEMINI_API_KEY=xxx kortana`

### Cloud Run Deployment
1. Push to main branch
2. GitHub Actions triggers
3. Cloud Build compiles application
4. Docker image pushed to GCR
5. Cloud Run deploys new version
6. Service available at Cloud Run URL

## Environment Variables

### Required
- `GEMINI_API_KEY` - Google Gemini API key for AI analysis

### Optional
- `PORT` - Server port (default: 3001)
- `NODE_ENV` - Environment mode (development/production)
- `GITHUB_TOKEN` - Default GitHub token (optional, users provide their own)

## Security Considerations

### Secrets Management
- Never commit `.env` file
- Use Google Secret Manager for Cloud Run
- Use GitHub Secrets for CI/CD
- Rotate API keys regularly

### GitHub Token Scopes
Required scopes for GitHub Personal Access Token:
- `repo` - Full repository access
- `read:user` - Read user profile data

### CORS Configuration
- Configured for cross-origin requests
- Adjust in production for specific domains

## Future Enhancements

### Potential Features
- [ ] OAuth flow for GitHub authentication
- [ ] WebSocket support for real-time updates
- [ ] Repository metrics dashboard
- [ ] Custom AI analysis prompts
- [ ] Multi-repository comparison
- [ ] Export analysis reports (PDF/CSV)
- [ ] User preferences and saved repositories
- [ ] Notification system for new issues/PRs
- [ ] Integration with other platforms (GitLab, Bitbucket)

### Technical Improvements
- [ ] Add unit tests (Jest)
- [ ] Add integration tests
- [ ] Implement caching layer (Redis)
- [ ] Add rate limiting
- [ ] Implement logging (Winston)
- [ ] Add monitoring (Prometheus/Grafana)
- [ ] Database for user preferences (PostgreSQL)
- [ ] GraphQL API option

## Troubleshooting

### Common Issues

#### "Cannot find module 'express'"
- Ensure dependencies are installed: `npm install`
- Rebuild application: `npm run build`

#### "Authentication failed"
- Verify GitHub token is valid
- Check token has required scopes
- Ensure token hasn't expired

#### "Gemini API errors"
- Verify API key is correct
- Check API quota limits
- Ensure Gemini API is enabled in Google Cloud

#### Docker build fails
- Build locally first: `npm run build:all`
- Check disk space available
- For production, use Cloud Build

## Contributing

### Development Workflow
1. Fork repository
2. Create feature branch
3. Make changes
4. Test locally
5. Submit pull request

### Code Style
- TypeScript strict mode enabled
- Follow existing patterns
- Add comments for complex logic
- Update documentation

## License

MIT License - See LICENSE file for details

## Support

For issues and questions:
- Open GitHub issue
- Check documentation
- Review error logs

---

Built with ❤️ by the Kor'tana team
