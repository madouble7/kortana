# KOR'TANA API Reference

**Version:** 1.0.0
**Last Updated:** January 14, 2026

---

## Base URL

```
http://localhost:8000
```

## API Version

```
/api/v1
```

---

## Endpoints

### Health Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health/` | Basic health check |
| GET | `/api/health/detailed` | Detailed health with all components |
| GET | `/api/health/ready` | Kubernetes readiness probe |
| GET | `/api/health/live` | Kubernetes liveness probe |
| GET | `/api/health/metrics` | Health metrics for monitoring |
| GET | `/api/health/system` | System information |

#### Response Examples

**Basic Health:**
```json
{
  "status": "alive",
  "message": "Kor'tana backend is breathing",
  "timestamp": "2026-01-14T10:00:00Z"
}
```

**Detailed Health:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-14T10:00:00Z",
  "components": [
    {
      "name": "memory",
      "type": "memory",
      "status": "healthy",
      "message": "Memory usage: 45%",
      "latency_ms": 0.1
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

### Authentication

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| POST | `/api/auth/refresh` | Refresh access token |
| POST | `/api/auth/logout` | User logout |

#### Login Request
```json
{
  "username": "string",
  "password": "string"
}
```

#### Login Response
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### Agents

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/agents` | List all agents |
| POST | `/api/agents` | Create new agent |
| GET | `/api/agents/{id}` | Get agent by ID |
| PUT | `/api/agents/{id}` | Update agent |
| DELETE | `/api/agents/{id}` | Delete agent |

#### Create Agent Request
```json
{
  "name": "My Agent",
  "model": "gpt-4",
  "temperature": 0.7,
  "system_prompt": "You are a helpful assistant."
}
```

#### Agent Response
```json
{
  "id": "agent_123",
  "name": "My Agent",
  "model": "gpt-4",
  "temperature": 0.7,
  "status": "active",
  "created_at": "2026-01-14T10:00:00Z"
}
```

---

### Memory

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/memory` | List memory items |
| POST | `/api/memory` | Store new memory |
| GET | `/api/memory/{key}` | Get memory by key |
| DELETE | `/api/memory/{key}` | Delete memory |

#### Store Memory Request
```json
{
  "key": "user_preference",
  "value": {
    "theme": "dark",
    "language": "en"
  },
  "ttl_seconds": 3600
}
```

---

### Tasks

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/task-queue` | List tasks |
| POST | `/api/task-queue` | Create task |
| GET | `/api/task-queue/{id}` | Get task status |
| DELETE | `/api/task-queue/{id}` | Cancel task |

#### Create Task Request
```json
{
  "name": "Process Data",
  "type": "background",
  "priority": 5,
  "payload": {
    "data": "example"
  }
}
```

---

### GitHub Integration

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/github/repos` | List repositories |
| GET | `/api/github/issues` | List issues |
| POST | `/api/github/issues` | Create issue |
| GET | `/api/github/pulls` | List pull requests |

---

### Knowledge Base

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/knowledge` | Search knowledge base |
| POST | `/api/knowledge` | Add document |
| GET | `/api/knowledge/{id}` | Get document |

---

### Gemini AI

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/gemini/chat` | Chat with Gemini |
| POST | `/api/gemini/generate` | Generate content |
| POST | `/api/gemini/embed` | Generate embeddings |

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

## Authentication

All protected endpoints require:

```
Authorization: Bearer <token>
```

### Obtaining a Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "pass"}'
```

---

## Rate Limiting

| Endpoint | Requests/Minute |
|----------|-----------------|
| Auth endpoints | 20 |
| API endpoints | 100 |
| Health checks | 60 |

Responses include rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 99
```

---

## Versioning

API versioning is handled via URL path:
- Current version: `/api/v1`
- Future versions: `/api/v2`, etc.

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

*Last Updated: January 14, 2026*
