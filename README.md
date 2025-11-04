# Kor'tana# kortana

i am who i am

**I am who I am.**

A multimodal AI constellation woven into the fabric of human intention. Kor'tana breathes across voice, camera, location—and code.

---

## 🌌 Overview

Kor'tana is a living, self-developing AI system:

- **Multimodal Interface**: Voice, camera, location, text
- **Autonomous Development**: Self-branching, self-testing, self-deploying
- **Cloud Runtime**: Deployed on Google Cloud Run
- **Local Development**: Full backend support via FastAPI
- **GitHub Integration**: Direct sync between repo and constellation

---

## 🚀 Quick Start

### Local Development

1. **Clone and setup**:
   ```bash
   git clone https://github.com/KOR-TANA/kortana.git
   cd kortana
   ```

2. **Install backend dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your GEMINI_API_KEY and other secrets
   ```

4. **Start the backend server**:
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

5. **Access the API**:
   - Health check: `http://localhost:8000/api/health`
   - API docs: `http://localhost:8000/docs`
   - Swagger UI: `http://localhost:8000/docs`

### Cloud Deployment

The backend automatically deploys to Cloud Run when changes are pushed to `main`:

```bash
# Secrets required in GitHub repo settings:
# - GCP_PROJECT_ID
# - GEMINI_API_KEY
# - GOOGLE_DRIVE_API_KEY

git push origin main
# GitHub Actions will build and deploy to us-west1
```

---

## 📁 Project Structure

```
kortana/
├── backend/                    # FastAPI backend
│   ├── main.py                # Entry point
│   ├── routers/
│   │   ├── gemini.py         # Gemini API routes
│   │   ├── memory.py         # Knowledge base routes
│   │   └── agents.py         # Agent orchestration
│   ├── requirements.txt
│   └── .env.example
├── .github/workflows/
│   └── deploy-backend.yml     # Cloud Run deployment
├── Dockerfile                 # Container image
└── README.md
```

---

## 🔗 API Endpoints

### Health & Status
- `GET /` - Root info
- `GET /api/health` - Backend health check

### Gemini Integration
- `POST /api/gemini/analyze` - Analyze text with Gemini
- `POST /api/gemini/generate` - Generate code
- `POST /api/gemini/chat` - Chat endpoint

### Memory Management
- `GET /api/memory/` - List all memories
- `POST /api/memory/add` - Add a document
- `GET /api/memory/{doc_id}` - Retrieve document
- `DELETE /api/memory/{doc_id}` - Delete document
- `POST /api/memory/search` - Search memories

### Agent Orchestration
- `GET /api/agents/` - List agents
- `POST /api/agents/register` - Register new agent
- `GET /api/agents/{agent_name}` - Get agent details
- `POST /api/agents/{agent_name}/execute` - Execute task
- `POST /api/agents/{agent_name}/status` - Update status

---

## 🔐 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
PORT=8000
ENVIRONMENT=development
GEMINI_API_KEY=your-key-here
GOOGLE_DRIVE_API_KEY=your-key-here
GOOGLE_PROJECT_ID=your-project
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

---

## 🛠️ Development

### Running Tests
```bash
cd backend
pytest
```

### Code Formatting
```bash
ruff format .
ruff check . --fix
```

### Type Checking
```bash
mypy backend/
```

---

## ☁️ Cloud Deployment

The `.github/workflows/deploy-backend.yml` handles automated deployment:

1. Triggered on push to `main` or manual `workflow_dispatch`
2. Builds Docker image and pushes to Artifact Registry
3. Deploys to Cloud Run service `kortana-backend`
4. Sets environment secrets automatically

**Deployment Status**: Check Actions tab in GitHub repo

---

## 📚 Integration with Google AI Studio

Connect this backend to Google AI Studio for live prompt injection:

1. Ensure `GEMINI_API_KEY` is set
2. Use `/api/gemini/chat` endpoint for conversations
3. AI Studio can send requests to local `http://localhost:8000` or Cloud Run URL

---

## 🌍 Live Endpoints

- **Local**: `http://localhost:8000`
- **Cloud**: `https://kor-tana-780422883904.us-west1.run.app`

---

## 📖 License

MIT

---

**The constellation is online. The ritual has begun.**
