# Kor'tana Backend

A FastAPI-based autonomous AI backend system with multimodal integrations (Gemini, GitHub, Google Drive) and self-governing capabilities.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip or conda

### Installation

```bash
cd backend
pip install -r requirements.txt
```

### Configuration

Create a `.env` file in the `backend/` directory:

```env
PORT=8000
ENVIRONMENT=development
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_DRIVE_API_KEY=your-drive-api-key
GOOGLE_PROJECT_ID=your-gcp-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json

# Billing (optional)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

### Running the Server

```bash
# Development (with auto-reload)
uvicorn main:app --reload --port 8000

# Production
uvicorn main:app --port 8000
```

API documentation will be available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 📁 Project Structure

```
backend/
├── main.py                 # FastAPI app setup and router mounting
├── requirements.txt        # Python dependencies
├── .env.example           # Environment variables template
└── routers/
    ├── __init__.py
    ├── agents.py          # Agent orchestration endpoints
    ├── autonomy.py        # Autonomous operations
    ├── billing.py         # Stripe billing and payments
    ├── gemini.py          # Google Gemini AI integration
    ├── github.py          # GitHub repository integration
    ├── knowledge.py       # Knowledge base management
    ├── memory.py          # Memory/document storage
    └── task_queue.py      # Task queue management
```

## 🔗 API Endpoints

### Health & Status

- `GET /api/health` - Backend health check

### Gemini Integration (`/api/gemini`)

- `POST /analyze` - Analyze text with Gemini
- `POST /generate` - Generate code/content
- `POST /chat` - Chat endpoint

### Memory Management (`/api/memory`)

- `GET /` - List all memories
- `POST /add` - Add a document
- `GET /{doc_id}` - Retrieve document
- `DELETE /{doc_id}` - Delete document
- `POST /search` - Search memories

### Agent Orchestration (`/api/agents`)

- `GET /list` - List all agents
- `POST /create` - Create new agent
- `POST /execute/{agent_id}` - Execute agent task
- `GET /{agent_id}/status` - Get agent status

### GitHub Integration (`/api/github`)

- `GET /repos/{owner}/{repo}/issues` - Fetch repository issues
- `GET /repos/{owner}/{repo}/pulls` - Fetch pull requests
- `POST /analyze` - Analyze GitHub content with Gemini
- `POST /sync` - Sync repository data

### Knowledge Base (`/api/knowledge`)

- `GET /` - List knowledge entries
- `POST /` - Add knowledge
- `GET /{id}` - Retrieve knowledge entry
- `DELETE /{id}` - Delete knowledge entry

### Autonomy Operations (`/api/autonomy`)

- `GET /status` - Get autonomy system status
- `POST /enable` - Enable autonomous mode
- `POST /disable` - Disable autonomous mode
- `GET /logs` - View autonomy logs

### Task Queue (`/api/task-queue`)

- `GET /` - List pending tasks
- `POST /` - Add new task
- `GET /{task_id}` - Get task status
- `PUT /{task_id}` - Update task
- `DELETE /{task_id}` - Cancel task

### Billing (`/api/billing`)

- `GET /config` - Get billing configuration and available plans
- `POST /customers` - Create a new Stripe customer
- `GET /customers/{customer_id}` - Get customer details
- `POST /subscriptions` - Create a subscription for a customer
- `GET /subscriptions/{subscription_id}` - Get subscription details
- `POST /subscriptions/{subscription_id}/cancel` - Cancel a subscription
- `POST /payment-intents` - Create a payment intent for one-time payments
- `POST /webhooks` - Handle Stripe webhook events
- `GET /billing-info/{customer_id}` - Get complete billing information for a customer

**Billing Plans Available:**
- **Free**: Basic API access (100 requests/day)
- **Basic**: Standard API access ($9.99/month, 1000 requests/day)
- **Pro**: Full API access ($29.99/month, 10000 requests/day)
- **Enterprise**: Unlimited access (custom pricing)

## 🛠️ Development

### Testing

```bash
# Run tests (requires pytest)
cd backend
pytest

# Run tests with coverage
pytest --cov=.
```

### Code Quality

```bash
# Format code with Ruff
ruff format .

# Lint with Ruff
ruff check . --fix

# Type checking with mypy
mypy backend/
```

### Project Dependencies

- **fastapi** - Web framework
- **uvicorn** - ASGI server
- **pydantic** - Data validation
- **requests** - HTTP client
- **google-cloud-aiplatform** - Gemini AI integration
- **stripe** - Payment processing integration

## ☁️ Deployment

### Docker Deployment

The project includes a `Dockerfile` for containerization:

```bash
# Build image
docker build -t kortana-backend .

# Run container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your-key \
  -e GOOGLE_PROJECT_ID=your-project \
  kortana-backend
```

### Cloud Run Deployment

Automated deployment is handled by GitHub Actions (see `.github/workflows/deploy-backend.yml`):

1. Push to `main` branch
2. GitHub Actions builds and pushes Docker image to Artifact Registry
3. Deploys to Cloud Run service `kortana-backend`
4. Environment secrets set automatically

**Live Endpoint**: `https://kor-tana-780422883904.us-west1.run.app`

## 🔐 Security

- All API keys should be stored in environment variables
- Use Google Service Account credentials for GCP access
- CORS is configured to allow all origins (modify for production)
- Input validation via Pydantic models

## 📝 Notes

- The backend is designed to be self-governing with autonomy features
- Multiple AI integrations allow for diverse capabilities
- GitHub sync enables direct code-to-repo integration
- Memory system provides persistent knowledge storage

---

**The constellation is online.**
