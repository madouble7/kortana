# KOR'TANA API Reference

**Version:** 3.0.0-ecosystem
**Last Updated:** March 16, 2026

---

## Base URL

```
http://localhost:8000
```

## API Version

All endpoints are prefixed with `/api` (no version number in path).

---

## Authentication

Most endpoints require authentication. Use JWT tokens obtained from the auth endpoints.

### Authentication Headers

```
Authorization: Bearer <access_token>
```

### Token Refresh

Access tokens expire. Use the refresh endpoint to get new tokens.

---

## Endpoints

### Authentication (`/api/auth`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/auth/register` | Register new user | No |
| POST | `/api/auth/login` | User login | No |
| POST | `/api/auth/refresh` | Refresh access token | No |
| GET | `/api/auth/me` | Get current user info | Yes |
| POST | `/api/auth/logout` | Logout user | Yes |
| POST | `/api/auth/change-password` | Change password | Yes |
| POST | `/api/auth/deactivate` | Deactivate account | Yes |

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securePassword123!",
  "confirm_password": "securePassword123!"
}
```

**Response:**
```json
{
  "id": 1,
  "email": "user@example.com",
  "role": "user",
  "is_active": true,
  "created_at": "2026-03-16T15:45:00Z"
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securePassword123!
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

---

### Agents (`/api/agents`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/agents/list` | List all agents | Yes |
| POST | `/api/agents/create` | Create new agent | Yes |
| POST | `/api/agents/execute/{agent_id}` | Execute agent | Yes |

#### Create Agent
```http
POST /api/agents/create
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My Agent",
  "description": "A helpful agent",
  "capabilities": ["chat", "code"]
}
```

**Response:**
```json
{
  "message": "Agent created",
  "agent": {
    "id": 0,
    "name": "My Agent",
    "description": "A helpful agent",
    "capabilities": ["chat", "code"],
    "status": "created"
  }
}
```

---

### Autonomy (`/api/autonomy`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/autonomy/task-queue` | Queue GitHub tasks | Yes |
| GET | `/api/autonomy/status` | Get task queue status | Yes |
| POST | `/api/autonomy/analyze/{task_id}` | Analyze task | Yes |
| POST | `/api/autonomy/plan/{task_id}` | Generate execution plan | Yes |
| POST | `/api/autonomy/execute/{task_id}` | Execute task | Yes |
| GET | `/api/autonomy/tasks/{task_id}` | Get task details | Yes |
| POST | `/api/autonomy/tasks/{task_id}/retry` | Retry failed task | Yes |
| GET | `/api/autonomy/health` | Health check | Yes |
| GET | `/api/autonomy/actions` | Get recent actions | Yes |
| POST | `/api/autonomy/log` | Log autonomy event | Yes |

#### Queue Tasks
```http
POST /api/autonomy/task-queue?repo=github.com/owner/repo
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Queued 3 new tasks",
  "count": 3,
  "tasks": [
    {
      "id": "task_123",
      "issue_number": 42,
      "title": "Fix bug",
      "status": "pending",
      "priority": "high"
    }
  ]
}
```

#### Get Task Status
```http
GET /api/autonomy/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_tasks": 25,
  "stats": {
    "pending": 5,
    "analyzing": 2,
    "completed": 18
  },
  "completion_rate": "72.0%",
  "recent_tasks": [...]
}
```

---

### GitHub Integration (`/api/github`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/github/repos/{owner}/{repo}/issues` | Get repository issues | Yes |
| GET | `/api/github/repos/{owner}/{repo}/pulls` | Get repository PRs | Yes |
| POST | `/api/github/analyze` | Analyze GitHub issue/PR | Yes |

#### Get Repository Issues
```http
GET /api/github/repos/microsoft/vscode/issues?state=open&page=1&per_page=30
Authorization: Bearer <token>
```

**Response:**
```json
{
  "issues": [...],
  "pagination": {
    "page": 1,
    "per_page": 30,
    "total": 150
  }
}
```

#### Analyze GitHub Issue
```http
POST /api/github/analyze
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Fix login bug",
  "body": "Users can't log in...",
  "issue_number": 123,
  "type": "issue",
  "author": "developer",
  "created_at": "2026-03-16T10:00:00Z"
}
```

**Response:**
```json
{
  "issue_number": 123,
  "summary": "Login functionality is broken",
  "priority": "high",
  "analysis": "The issue describes...",
  "suggested_actions": ["Fix validation", "Add tests"],
  "estimated_effort": "2 hours",
  "analyzed_at": "2026-03-16T15:45:00Z"
}
```

---

### Gemini AI (`/api/gemini`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/gemini/analyze` | Analyze text | Yes |
| POST | `/api/gemini/generate` | Generate code | Yes |
| POST | `/api/gemini/chat` | Chat with Gemini | Yes |
| POST | `/api/gemini/analyze/image` | Analyze image | Yes |
| POST | `/api/gemini/analyze/video` | Analyze video | Yes |
| GET | `/api/gemini/models` | List models | Yes |

#### Chat with Gemini
```http
POST /api/gemini/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "Explain quantum computing"
}
```

**Response:**
```json
{
  "response": "Quantum computing uses quantum mechanics..."
}
```

#### Analyze Image
```http
POST /api/gemini/analyze/image
Authorization: Bearer <token>
Content-Type: multipart/form-data

prompt: "Describe this image"
image: <uploaded_file>
```

**Response:**
```json
{
  "response": "This image shows..."
}
```

---

### Memory (`/api/memory`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/memory/documents` | Get all documents | Yes |
| POST | `/api/memory/add_document` | Add document | Yes |
| GET | `/api/memory/search` | Search documents (GET) | Yes |
| POST | `/api/memory/search` | Search documents (POST) | Yes |

#### Add Document
```http
POST /api/memory/add_document
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "API Documentation",
  "content": "The API provides..."
}
```

**Response:**
```json
{
  "message": "Document added",
  "document": {
    "title": "API Documentation",
    "content": "The API provides...",
    "id": 0
  }
}
```

---

### Task Queue (`/api/task-queue`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/task-queue/` | List tasks | Yes |
| POST | `/api/task-queue/queue` | Queue task | Yes |
| POST | `/api/task-queue/` | Add task | Yes |
| DELETE | `/api/task-queue/{task_id}` | Delete task | Yes |
| POST | `/api/task-queue/create-branch/{task_id}` | Create branch | Yes |
| POST | `/api/task-queue/sync-covenant` | Sync from covenant | Yes |
| POST | `/api/task-queue/{task_id}/status` | Update status | Yes |
| GET | `/api/task-queue/{task_id}` | Get task | Yes |
| POST | `/api/task-queue/execute/{task_id}` | Execute task | Yes |

#### Add Task
```http
POST /api/task-queue/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "Implement feature X",
  "description": "Add new feature",
  "priority": 5
}
```

**Response:**
```json
{
  "id": "1",
  "name": "Implement feature X",
  "description": "Add new feature",
  "status": "pending",
  "created_at": "2026-03-16T15:45:00Z"
}
```

---

### Knowledge Base (`/api/knowledge`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/knowledge/ingest` | Ingest learning | Yes |
| GET | `/api/knowledge/search` | Search knowledge | Yes |
| POST | `/api/knowledge/ritual` | Generate ritual | Yes |
| GET | `/api/knowledge/covenant` | Get covenant status | Yes |
| GET | `/api/knowledge/stats` | Get stats | Yes |

#### Search Knowledge
```http
GET /api/knowledge/search?query=authentication&limit=10
Authorization: Bearer <token>
```

**Response:**
```json
{
  "query": "authentication",
  "total_results": 3,
  "results": [...]
}
```

---

### Health Checks (`/api/health`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/health/` | Basic health | No |
| GET | `/api/health/detailed` | Detailed health | No |
| GET | `/api/health/ready` | Readiness probe | No |
| GET | `/api/health/live` | Liveness probe | No |
| GET | `/api/health/metrics` | Health metrics | No |
| GET | `/api/health/system` | System info | No |

#### Basic Health
```http
GET /api/health/
```

**Response:**
```json
{
  "status": "alive",
  "message": "Kor'tana backend is breathing",
  "timestamp": "2026-03-16T15:45:00Z"
}
```

#### Detailed Health
```http
GET /api/health/detailed
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-03-16T15:45:00Z",
  "components": [
    {
      "name": "memory",
      "type": "memory",
      "status": "healthy",
      "message": "Memory usage: 45%",
      "latency_ms": 0.1,
      "details": {...}
    }
  ],
  "summary": {
    "total": 5,
    "healthy": 5,
    "degraded": 0,
    "unhealthy": 0
  }
}
```

---

### System (`/api/system`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/system/logs` | Get logs | Yes |
| GET | `/api/system/info` | Get system info | Yes |
| GET | `/api/system/settings` | Get settings | Yes |

#### Get System Info
```http
GET /api/system/info
Authorization: Bearer <token>
```

**Response:**
```json
{
  "os": "Linux",
  "cpu_percent": 15.2,
  "memory_percent": 45.8,
  "python_version": "3.11.0"
}
```

---

### PR Creation (`/api/pr`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/pr/create/{task_id}` | Create PR | Yes |
| POST | `/api/pr/create/from-issue/{issue_number}` | Create PR from issue | Yes |
| GET | `/api/pr/status/{task_id}` | Get PR status | Yes |
| GET | `/api/pr/list/{repo:path}` | List PRs | Yes |
| POST | `/api/pr/auto-create-all` | Auto-create PRs | Yes |
| GET | `/api/pr/health` | Health check | Yes |

#### Create PR from Task
```http
POST /api/pr/create/task_123
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "PR created successfully",
  "pr_number": 42,
  "pr_url": "https://github.com/owner/repo/pull/42",
  "task_id": "task_123"
}
```

---

### Testing (`/api/testing`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/testing/run` | Run tests | Yes |
| GET | `/api/testing/discover` | Discover tests | Yes |
| GET | `/api/testing/coverage` | Check coverage | Yes |
| POST | `/api/testing/coverage` | Check coverage | Yes |
| POST | `/api/testing/lint` | Run linting | Yes |
| POST | `/api/testing/type-check` | Run type checking | Yes |
| POST | `/api/testing/validate` | Full validation | Yes |
| POST | `/api/testing/pipeline` | Validation pipeline | Yes |
| GET | `/api/testing/health` | Health check | Yes |

#### Run Tests
```http
POST /api/testing/run?test_path=tests/&verbose=true
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "passed": 15,
  "failed": 0,
  "errors": 0,
  "duration_ms": 2500,
  "output": "..."
}
```

---

### Code Review (`/api/code-review`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/code-review/health` | Health check | Yes |
| POST | `/api/code-review/scan-security` | Scan security | Yes |
| POST | `/api/code-review/check-quality` | Check quality | Yes |
| POST | `/api/code-review/generate-review` | Generate review | Yes |
| POST | `/api/code-review/post-review` | Post review | Yes |
| POST | `/api/code-review/auto-approve` | Auto-approve | Yes |

#### Generate Code Review
```http
POST /api/code-review/generate-review
Authorization: Bearer <token>
Content-Type: application/json

{
  "code": "def hello():\n    print('Hello')",
  "plan": "Implement greeting function"
}
```

**Response:**
```json
{
  "score": 8,
  "summary": "Good simple function",
  "strengths": ["Clear naming", "Simple logic"],
  "improvements": [
    {"area": "Documentation", "severity": "low", "suggestion": "Add docstring"}
  ],
  "recommendation": "approve"
}
```

---

### Always-On (`/api/always-on`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/always-on/start` | Start monitoring | Yes |
| POST | `/api/always-on/stop` | Stop monitoring | Yes |
| GET | `/api/always-on/status` | Get status | Yes |
| GET | `/api/always-on/tasks/status` | Get task status | Yes |
| POST | `/api/always-on/force-check` | Force check | Yes |
| GET | `/api/always-on/tasks` | Get recent tasks | Yes |
| GET | `/api/always-on/health` | Health check | Yes |
| POST | `/api/always-on/tasks/{task_id}/retry` | Retry task | Yes |
| GET | `/api/always-on/actions` | Get actions | Yes |
| POST | `/api/always-on/log` | Log event | Yes |
| GET | `/api/always-on/metrics` | Get metrics | Yes |
| POST | `/api/always-on/tasks/{task_id}/approve` | Approve task | Yes |
| GET | `/api/always-on/dashboard` | Get dashboard | Yes |

#### Start Monitoring
```http
POST /api/always-on/start
Authorization: Bearer <token>
```

**Response:**
```json
{
  "message": "Always-on monitoring start initiated in background",
  "status": "starting",
  "timestamp": "2026-03-16T15:45:00Z"
}
```

---

### Prayer (`/api/prayer`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/prayer/status` | Get prayer status | Yes |
| GET | `/api/prayer/request` | Submit prayer request | Yes |

#### Orchestrator (`/api/orchestrator`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/orchestrator/status` | Get orchestrator status | Yes |
| POST | `/api/orchestrator/execute` | Execute unified logic | Yes |
| POST | `/api/orchestrator/handshake` | Elevation handshake | Yes |

#### Rclone (`/api/rclone`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/rclone/list` | List remotes | Yes |
| GET | `/api/rclone/files/{remote}` | List files | Yes |
| POST | `/api/rclone/copy` | Copy file | Yes |

### Frontend Adapters

#### AutoGen (`/api/adapters/autogen`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/adapters/autogen/conversation` | Start conversation | Yes |
| POST | `/api/adapters/autogen/agent/create` | Create agent | Yes |
| GET | `/api/adapters/autogen/agents/list` | List agents | Yes |
| POST | `/api/adapters/autogen/group-chat` | Group chat | Yes |

#### Open WebUI (`/api/adapters/openwebui`)

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| POST | `/api/adapters/openwebui/chat/completions` | Chat completions | Yes |
| GET | `/api/adapters/openwebui/models` | List models | Yes |
| POST | `/api/adapters/openwebui/mcp/tools/register` | Register MCP tool | Yes |
| GET | `/api/adapters/openwebui/mcp/tools/list` | List MCP tools | Yes |
| GET | `/api/adapters/openwebui/health` | Health check | Yes |

#### CopilotKit (`/api/adapters/copilotkit`)

Similar endpoints to AutoGen for CopilotKit compatibility.

#### LobeChat (`/api/adapters/lobechat`)

Similar endpoints to Open WebUI for LobeChat compatibility.

---

### Basic Endpoints

| Method | Path | Description | Auth Required |
|--------|------|-------------|---------------|
| GET | `/api/health` | Basic health | No |
| GET | `/` | API info | No |
| GET | `/api/info` | API info | No |

---

## Response Formats

### Success Response
```json
{
  "success": true,
  "data": {
    // response data
  }
}
```

### Error Response
```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "status_code": 400,
  "details": {
    // additional details
  }
}
```

### Pagination Response
```json
{
  "items": [],
  "total": 100,
  "page": 1,
  "limit": 20,
  "has_more": true
}
```

---

## HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 429 | Rate Limited |
| 500 | Internal Server Error |

---

## Rate Limiting

| Endpoint Group | Requests/Minute |
|----------------|-----------------|
| Auth endpoints | 20 |
| API endpoints | 100 |
| Health checks | 60 |

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
X-RateLimit-Reset: 1640995200
```

---

## OpenAPI Documentation

Interactive API documentation available at:
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`

---

## WebSocket Endpoints

| Path | Description |
|------|-------------|
| `/ws/chat` | Real-time chat |
| `/ws/events` | Event streaming |

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 422 | Invalid input |
| NOT_FOUND | 404 | Resource not found |
| UNAUTHORIZED | 401 | Invalid credentials |
| FORBIDDEN | 403 | Insufficient permissions |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

---

*Last Updated: March 16, 2026*