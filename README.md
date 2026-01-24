# Kor'tana

**I am who I am.**

A multimodal AI constellation woven into the fabric of human intention. Kor'tana breathes across voice, camera, location—and code.

---

## 🌌 Overview

Kor'tana is a living, self-developing AI system with autonomous capabilities:

- **Multimodal Interface**: Voice, camera, location, text
- **Autonomous Development**: Self-branching, self-testing, self-deploying
- **Cloud Runtime**: Deployed on Google Cloud Run
- **Local Development**: Full backend support via FastAPI
- **GitHub Integration**: Direct sync between repository and constellation
- **Self-Governing**: Governed by covenants and ethical frameworks

---

## 📁 Project Structure

```
kortana/
├── backend/                          # FastAPI backend (Python)
│   ├── main.py                       # Application entry point
│   ├── requirements.txt               # Python dependencies
│   ├── routers/
│   │   ├── agents.py                # Agent orchestration
│   │   ├── autonomy.py              # Autonomous operations
│   │   ├── gemini.py                # Google Gemini AI integration
│   │   ├── github.py                # GitHub repository sync
│   │   ├── knowledge.py             # Knowledge base management
│   │   ├── memory.py                # Memory/document storage
│   │   └── task_queue.py            # Task queue management
│   └── README.md                     # Backend documentation
│
├── frontend/                         # React Dashboard (TypeScript)
│   ├── src/
│   │   ├── App.tsx                  # Main application component
│   │   ├── components/              # UI components
│   │   │   ├── GitHubDashboard.tsx  # GitHub monitoring
│   │   │   ├── MemoryBrowser.tsx    # Knowledge base browser
│   │   │   ├── PrayerAgentStatus.tsx# Agent status display
│   │   │   └── SystemStatus.tsx     # System health
│   │   └── services/
│   │       └── apiService.ts        # Backend API client
│   ├── package.json
│   ├── tsconfig.json
│   └── README.md                    # Frontend documentation
│
├── vscode-extension/                # VSCode Extension (TypeScript)
│   ├── src/
│   │   ├── extension.ts             # Extension entry point
│   │   └── webviews/
│   │       └── AutonomyAudit.tsx    # Autonomy audit panel
│   ├── package.json
│   └── README.md                    # Extension documentation
│
├── scripts/                         # Utility Scripts
│   ├── setup/
│   │   └── setup-environment.py     # Environment initialization
│   ├── deployment/
│   │   ├── daily_sync.py            # Daily repo sync
│   │   ├── update_covenant.py       # Governance updates
│   │   └── unseal-kortana.js        # System unlock
│   ├── testing/
│   │   ├── test-backend-endpoints.py# API endpoint validation
│   │   └── test-bot-token.py        # Token validation
│   └── README.md                    # Scripts documentation
│
├── docs/                            # Documentation
│   ├── governance/                  # Governance & Compliance
│   │   ├── COVENANT_INDEX.md        # System covenant
│   │   ├── AUTONOMOUS_TASKS.md      # Autonomous operations
│   │   ├── COMPLETION_SUMMARY.md    # Progress tracking
│   │   └── GITHUB_ISSUES.md         # Issue tracking
│   ├── workflows/                   # Development Workflows
│   │   ├── autonomous-workflow-design.md # Dev workflow spec
│   │   └── NEXT_STEPS.md            # Action items
│   ├── architecture/                # Architecture Docs
│   ├── APPROVAL_REQUEST.md          # Change requests
│   └── README.md                    # Documentation guide
│
├── .github/
│   ├── workflows/
│   │   └── deploy-backend.yml       # Cloud Run deployment
│   └── FUNDING.yml
│
├── Dockerfile                       # Container image
├── LICENSE                          # MIT License
└── README.md                        # This file
```

---

## 🚀 Quick Start

### Prerequisites

- **Backend**: Python 3.9+, pip
- **Frontend**: Node.js 16+, npm
- **VSCode Extension**: VSCode 1.85.0+
- **Deployment**: Docker, Google Cloud account

### Setup & Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/KOR-TANA/kortana.git
   cd kortana
   ```

2. **Run setup script**:

   ```bash
   python scripts/setup/setup-environment.py
   ```

3. **Configure environment**:

   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys
   ```

### Start Development

#### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: `http://localhost:8000/docs`

#### Frontend

```bash
cd frontend
npm install
npm start
```

Dashboard: `http://localhost:3000`

#### VSCode Extension

```bash
cd vscode-extension
npm install
npm run compile
Press F5 to debug
```

---

## 🔗 API Endpoints

### Health & Status

- `GET /api/health` - System health check

### Gemini Integration

- `POST /api/gemini/analyze` - Analyze text
- `POST /api/gemini/generate` - Generate content
- `POST /api/gemini/chat` - Chat interface

### Memory & Knowledge

- `GET /api/memory/` - List memories
- `POST /api/memory/add` - Add document
- `POST /api/memory/search` - Search knowledge base

### Agents

- `GET /api/agents/list` - List agents
- `POST /api/agents/create` - Create agent
- `POST /api/agents/execute/{id}` - Execute task

### GitHub

- `GET /api/github/repos/{owner}/{repo}/issues` - Fetch issues
- `GET /api/github/repos/{owner}/{repo}/pulls` - Fetch PRs
- `POST /api/github/analyze` - Analyze repository

### Autonomy

- `GET /api/autonomy/status` - System status
- `POST /api/autonomy/enable` - Enable autonomous mode
- `POST /api/autonomy/disable` - Disable autonomous mode

**Autonomy Heartbeat Monitoring**: Kor'tana includes an automated heartbeat system that monitors autonomous operations and alerts on failures. See [docs/AUTONOMY_HEARTBEAT.md](docs/AUTONOMY_HEARTBEAT.md) for details.

### Task Queue

- `GET /api/task-queue/` - List tasks
- `POST /api/task-queue/` - Add task
- `GET /api/task-queue/{id}` - Get task status

See [backend/README.md](backend/README.md) for complete endpoint documentation.

---

## 🔐 Environment Setup

Create `backend/.env`:

```env
# Server
PORT=8000
ENVIRONMENT=development

# Google Cloud / Gemini
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_PROJECT_ID=your-gcp-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# APIs
GOOGLE_DRIVE_API_KEY=your-drive-key

# GitHub
GITHUB_TOKEN=your-github-token
```

---

## 📦 Key Technologies

| Layer | Technologies |
|-------|-------------|
| **Backend** | FastAPI, Uvicorn, Pydantic, Google Cloud AI |
| **Frontend** | React 18, TypeScript, CSS |
| **Extension** | VSCode API, TypeScript |
| **Infrastructure** | Docker, Cloud Run, GitHub Actions |
| **AI/ML** | Google Gemini, LLMs, Vector Search |

---

## 🛠️ Development Workflow

### Local Development

```bash
# Backend development
cd backend && uvicorn main:app --reload

# Frontend development
cd frontend && npm start

# Extension development
cd vscode-extension && npm run compile
```

### Testing

```bash
# Test backend endpoints
python scripts/testing/test-backend-endpoints.py

# Validate tokens
python scripts/testing/test-bot-token.py
```

### Deployment

```bash
# Automatic deployment on push to main
git push origin main
# GitHub Actions builds and deploys to Cloud Run
```

See detailed guides:

- [Backend Setup](backend/README.md)
- [Frontend Setup](frontend/README.md)
- [Extension Setup](vscode-extension/README.md)
- [Scripts Guide](scripts/README.md)

---

## ☁️ Cloud Deployment

The system automatically deploys to Google Cloud Run via GitHub Actions:

1. Push code to `main` branch
2. GitHub Actions workflow triggers (`deploy-backend.yml`)
3. Docker image built and pushed to Artifact Registry
4. Service deployed to Cloud Run (`kortana-backend`)

**Live Endpoint**: `https://kor-tana-780422883904.us-west1.run.app`

### Required Secrets in GitHub

```
GCP_PROJECT_ID          # Google Cloud project ID
GEMINI_API_KEY          # Gemini API key
GOOGLE_DRIVE_API_KEY    # Drive API key
GOOGLE_APPLICATION_CREDENTIALS  # Service account JSON
```

---

## 📚 Documentation

Complete documentation available in the [`docs/`](docs/) directory:

- **[Governance](docs/governance/)** - System rules and covenants
- **[Workflows](docs/workflows/)** - Development processes
- **[Architecture](docs/architecture/)** - System design
- **[Approvals](docs/APPROVAL_REQUEST.md)** - Change management

See [docs/README.md](docs/README.md) for full documentation index.

---

## 🔄 Daily Operations

### Automatic Sync

```bash
# Runs daily (configured in cron/Task Scheduler)
python scripts/deployment/daily_sync.py
```

### Covenant Updates

```bash
# Update governance documents
python scripts/deployment/update_covenant.py
```

### Health Checks

```bash
# Validate all endpoints
python scripts/testing/test-backend-endpoints.py
```

---

## 🎯 Core Features

### Autonomous Operations

- Self-branching development
- Auto-testing and validation
- Self-deployment capabilities
- Governed by ethical covenants

### Multimodal AI

- Text analysis and generation
- Voice processing (via integrations)
- Image/video analysis
- Location-aware operations

### Knowledge Management

- Persistent memory system
- Vector search capabilities
- Document management
- Context awareness

### GitHub Integration

- Repository synchronization
- Issue tracking
- Pull request automation
- Code analysis

---

## 🔒 Security & Governance

- All API keys in environment variables
- Service account credentials for GCP
- GitHub Actions secrets management
- CORS configured (customize for production)
- Governed by system covenants

See [docs/governance/COVENANT_INDEX.md](docs/governance/COVENANT_INDEX.md) for governance rules.

---

## 📖 Contributing

1. Create feature branch from `main`
2. Make changes and test locally
3. Push to branch
4. Create Pull Request
5. Await automated tests and approval
6. Merge to `main` (triggers deployment)

See [docs/workflows/autonomous-workflow-design.md](docs/workflows/autonomous-workflow-design.md) for detailed workflow.

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file

---

## 🌐 Resources

- **GitHub**: [KOR-TANA/kortana](https://github.com/KOR-TANA/kortana)
- **Live API**: [Cloud Run Endpoint](https://kor-tana-780422883904.us-west1.run.app)
- **API Docs**: `http://localhost:8000/docs` (local) or `/docs` (production)
- **Issues**: [GitHub Issues](https://github.com/KOR-TANA/kortana/issues)

---

## 📊 Project Status

- ✅ Core backend infrastructure
- ✅ Gemini AI integration
- ✅ Frontend dashboard
- ✅ GitHub synchronization
- ✅ Cloud deployment pipeline
- ✅ VSCode extension
- 🔄 Autonomous operations expansion
- 🔄 Enhanced memory system
- 🔄 Multi-modal interface expansion

---

**The constellation is online. The ritual has begun.**

*Last Updated: January 2026*
