# we are kor'tana - api documentation

## Overview
we are an autonomous ai system that analyzes GitHub issues and creates pull requests. This document describes the API endpoints and how to use them.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://your-domain.com`

## Authentication

All endpoints except `/api/auth/*` require a Bearer token:

```bash
curl -H "Authorization: Bearer your_api_token" \
  http://localhost:8000/api/gemini/generate
```

## Core Endpoints

### Health Check
**GET** `/api/health`

Returns system health status.

```bash
curl http://localhost:8000/api/health
```

Response (200):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z",
  "checks": {
    "database": true,
    "redis": true,
    "llm_models": true,
    "github_api": true,
    "celery_workers": true
  },
  "details": {
    "database": "Connected",
    "redis": "Connected",
    "llm_models": "3 models available",
    "github_api": "Connected",
    "celery_workers": "2 workers active"
  }
}
```

### Metrics
**GET** `/metrics`

Returns Prometheus metrics in text format.

```bash
curl http://localhost:8000/metrics | head -20
```

## Authentication Endpoints

### Login
**POST** `/api/auth/login`

Authenticate with email and password.

Request:
```json
{
  "email": "user@example.com",
  "password": "password"
}
```

Response (200):
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Create API Key
**POST** `/api/auth/api-keys`

Create a new API key for programmatic access.

Request:
```json
{
  "name": "My Integration Key",
  "expires_in": 2592000
}
```

Response (201):
```json
{
  "id": "key_123",
  "name": "My Integration Key",
  "key": "sk_live_...",
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-02-01T00:00:00Z"
}
```

## LLM Endpoints

### Generate Text
**POST** `/api/gemini/generate`

Generate text using Kor'tana's LLM router with automatic provider fallback.

Request:
```json
{
  "prompt": "Analyze this GitHub issue: ...",
  "model": "gemini-2.0-flash",
  "temperature": 0.7,
  "max_tokens": 2048
}
```

Response (200):
```json
{
  "content": "Generated text response...",
  "model": "gemini-2.0-flash",
  "provider": "gemini",
  "tokens_used": 245,
  "latency_ms": 1250,
  "temperature": 0.7
}
```

### List Available Models
**GET** `/api/gemini/models`

Get list of available LLM models and their status.

Response (200):
```json
{
  "primary": "gemini-2.0-flash",
  "available_models": [
    "gemini-2.0-flash",
    "gpt-4o",
    "mixtral-8x7b-32768"
  ],
  "fallback_order": [
    "gpt-4o",
    "claude-3-5-sonnet-20241022",
    "mixtral-8x7b-32768"
  ]
}
```

## GitHub Endpoints

### Analyze Issue
**POST** `/api/github/analyze`

Deeply analyze a GitHub issue using AI.

Request:
```json
{
  "issue_number": 123,
  "repo": "owner/repo"
}
```

Response (200):
```json
{
  "priority": "high",
  "complexity": "simple",
  "estimated_effort": "1 day",
  "skill_required": ["Python", "FastAPI"],
  "suggested_approach": "Implement feature by...",
  "potential_risks": ["May affect performance"],
  "success_criteria": ["Feature works", "Tests pass"]
}
```

### Create Execution Plan
**POST** `/api/github/plan`

Create a detailed execution plan for an issue.

Request:
```json
{
  "issue_number": 123,
  "repo": "owner/repo"
}
```

Response (200):
```json
{
  "steps": [
    "Create feature branch",
    "Implement solution",
    "Write tests",
    "Create PR"
  ],
  "file_changes": [
    "src/feature.py",
    "tests/test_feature.py"
  ],
  "tests_required": [
    "Unit tests for feature",
    "Integration tests"
  ],
  "estimated_duration": "1 day",
  "rollback_strategy": "Revert commit"
}
```

### Create Pull Request
**POST** `/api/github/pr`

Automatically create a pull request with generated code.

Request:
```json
{
  "issue_number": 123,
  "branch_name": "feature/issue-123",
  "title": "Implement feature X",
  "description": "Resolves #123"
}
```

Response (201):
```json
{
  "number": 456,
  "url": "https://github.com/owner/repo/pull/456",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Task Queue Endpoints

### Get Task Status
**GET** `/api/task-queue/{task_id}`

Get the status of an async task.

Response (200):
```json
{
  "task_id": "abc123",
  "status": "completed",
  "result": {
    "issue_analyzed": true,
    "priority": "high"
  },
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:01:00Z"
}
```

### List Pending Tasks
**GET** `/api/task-queue/pending`

Get list of pending tasks.

Response (200):
```json
{
  "tasks": [
    {
      "id": "task1",
      "type": "analyze_issue",
      "status": "pending",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

## Autonomous Endpoints

### Get Autonomy Status
**GET** `/api/autonomy/status`

Get the current status of autonomous operations.

Response (200):
```json
{
  "enabled": true,
  "active_tasks": 3,
  "last_activity": "2024-01-01T00:05:00Z",
  "issues_processed": 42,
  "prs_created": 15,
  "uptime_seconds": 86400
}
```

### Enable/Disable Autonomy
**POST** `/api/autonomy/toggle`

Enable or disable autonomous operations.

Request:
```json
{
  "enabled": false,
  "reason": "Maintenance window"
}
```

Response (200):
```json
{
  "status": "disabled",
  "message": "Autonomy disabled for maintenance"
}
```

## Webhook Endpoints

### GitHub Webhook Handler
**POST** `/api/github/webhook`

Receive GitHub webhook events and process them automatically.

Headers:
```
X-GitHub-Event: issues
X-Hub-Signature-256: sha256=...
```

Body (GitHub sends this automatically):
```json
{
  "action": "opened",
  "issue": {
    "number": 123,
    "title": "Bug: ...",
    "body": "Description...",
    "labels": [{"name": "bug"}],
    ...
  }
}
```

Response (200):
```json
{
  "status": "analyzed",
  "issue_number": 123,
  "priority": "high",
  "complexity": "simple",
  "estimated_effort": "1 hour",
  "plan_steps": 5,
  "files_to_change": 2
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": "ERROR_CODE",
  "message": "Human readable message",
  "status_code": 400,
  "details": {
    "field": "error_detail"
  }
}
```

Common status codes:
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Rate Limited
- `500`: Internal Server Error
- `503`: Service Unavailable

## Rate Limiting

API calls are rate limited:
- **100 requests per minute** for authenticated users
- **10 requests per minute** for unauthenticated requests

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1704067200
```

## Pagination

List endpoints support pagination:

```bash
curl "http://localhost:8000/api/tasks?page=1&limit=20"
```

Response:
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

## SDK/Client Libraries

### Python
```python
from kortana import KortanaClient

client = KortanaClient(api_key="sk_...")
response = client.generate("Analyze this issue: #123")
```

### JavaScript/TypeScript
```typescript
import { Kortana } from 'kortana-js';

const client = new Kortana({ apiKey: 'sk_...' });
const response = await client.generate('Analyze this issue: #123');
```

## Examples

### Analyze a GitHub Issue and Create a PR

```bash
#!/bin/bash

ISSUE_NUMBER=123
REPO="owner/repo"
TOKEN="your_api_token"

# Step 1: Analyze the issue
ANALYSIS=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/github/analyze \
  -H "Content-Type: application/json" \
  -d "{\"issue_number\": $ISSUE_NUMBER, \"repo\": \"$REPO\"}")

echo "Analysis: $ANALYSIS"

# Step 2: Create execution plan
PLAN=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/github/plan \
  -H "Content-Type: application/json" \
  -d "{\"issue_number\": $ISSUE_NUMBER, \"repo\": \"$REPO\"}")

echo "Plan: $PLAN"

# Step 3: Create PR
PR=$(curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST http://localhost:8000/api/github/pr \
  -H "Content-Type: application/json" \
  -d "{
    \"issue_number\": $ISSUE_NUMBER,
    \"branch_name\": \"feature/issue-$ISSUE_NUMBER\",
    \"title\": \"Implement feature for issue #$ISSUE_NUMBER\",
    \"description\": \"Resolves #$ISSUE_NUMBER\"
  }")

echo "PR Created: $PR"
```

## WebSocket Endpoints (Coming Soon)

Real-time updates on task progress and system status.

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/tasks');
ws.onmessage = (event) => {
  console.log('Task update:', event.data);
};
```
