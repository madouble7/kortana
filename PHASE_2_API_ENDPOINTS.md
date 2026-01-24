# Phase 2 API Endpoints Reference

**Version:** 2.0
**Status:** ✅ COMPLETE
**Base URL:** `http://localhost:8000`

---

## Table of Contents

- [PR Creation Endpoints](#pr-creation-endpoints)
- [Code Review Endpoints](#code-review-endpoints)
- [Test Orchestration Endpoints](#test-orchestration-endpoints)
- [Health Check Endpoints](#health-check-endpoints)
- [Error Handling](#error-handling)
- [Authentication](#authentication)
- [Rate Limiting](#rate-limiting)

---

## PR Creation Endpoints

### Create PR for Task

**Endpoint:** `POST /pr/create/{task_id}`

**Description:** Create a GitHub pull request for a specific task

**Parameters:**

- `task_id` (path): Integer - Task ID
- `repo` (query): String - Repository in format "owner/repo"

**Request Body:**

```json
{
    "code_changes": "string (optional)",
    "force": "boolean (default: false)",
    "dry_run": "boolean (default: false)"
}
```

**Response (201):**

```json
{
    "success": true,
    "pr_number": 123,
    "url": "https://github.com/owner/repo/pull/123",
    "task_id": 42,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

**Error Response (400):**

```json
{
    "error": "Task not found",
    "task_id": 99999,
    "status_code": 404
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/pr/create/42?repo=myorg/myrepo" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code_changes": "def new_feature(): pass"
  }'
```

---

### Create PR from Issue

**Endpoint:** `POST /pr/create/from-issue/{issue_number}`

**Description:** Create a GitHub pull request from an issue number

**Parameters:**

- `issue_number` (path): Integer - Issue number
- `repo` (query): String - Repository in format "owner/repo"

**Request Body:**

```json
{
    "branch": "string (optional)",
    "dry_run": "boolean (default: false)"
}
```

**Response (201):**

```json
{
    "success": true,
    "pr_number": 124,
    "url": "https://github.com/owner/repo/pull/124",
    "issue_number": 42,
    "linked": true
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/pr/create/from-issue/42?repo=myorg/myrepo" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json"
```

---

### Get PR Status

**Endpoint:** `GET /pr/status/{task_id}`

**Description:** Get the status of a pull request associated with a task

**Parameters:**

- `task_id` (path): Integer - Task ID
- `repo` (query): String - Repository in format "owner/repo"

**Response (200):**

```json
{
    "pr_number": 123,
    "state": "open",
    "merged": false,
    "url": "https://github.com/owner/repo/pull/123",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T12:00:00Z",
    "review_comments": 2,
    "commits": 1,
    "changed_files": 3,
    "additions": 150,
    "deletions": 20
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/pr/status/42?repo=myorg/myrepo" \
  -H "Authorization: Bearer $GITHUB_TOKEN"
```

---

### List PRs for Repository

**Endpoint:** `GET /pr/list/{repo}`

**Description:** List all pull requests for a repository

**Parameters:**

- `repo` (path): String - Repository in format "owner/repo"
- `state` (query): String - Filter by "open", "closed", or "all" (default: "open")
- `limit` (query): Integer - Max results (default: 30)

**Response (200):**

```json
[
    {
        "number": 123,
        "title": "Add user authentication",
        "state": "open",
        "url": "https://github.com/owner/repo/pull/123",
        "created_at": "2024-01-15T10:30:00Z",
        "author": "kor-tana-bot"
    },
    {
        "number": 122,
        "title": "Fix database connection",
        "state": "closed",
        "url": "https://github.com/owner/repo/pull/122",
        "merged_at": "2024-01-14T15:20:00Z",
        "author": "kor-tana-bot"
    }
]
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/pr/list/myorg/myrepo?state=open&limit=10" \
  -H "Authorization: Bearer $GITHUB_TOKEN"
```

---

### Auto-Create PRs for All Completed Tasks

**Endpoint:** `POST /pr/auto-create-all`

**Description:** Automatically create PRs for all completed tasks that don't have PRs yet

**Parameters:**

- `repo` (query): String - Repository in format "owner/repo"

**Request Body:**

```json
{
    "dry_run": "boolean (default: false)",
    "batch_size": "integer (default: 10)"
}
```

**Response (200):**

```json
{
    "success": true,
    "created": 5,
    "failed": 0,
    "skipped": 2,
    "prs": [
        {
            "task_id": 10,
            "pr_number": 100,
            "status": "created"
        },
        {
            "task_id": 11,
            "pr_number": 101,
            "status": "created"
        }
    ]
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/pr/auto-create-all?repo=myorg/myrepo" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

---

## Code Review Endpoints

### Scan for Security Issues

**Endpoint:** `POST /review/scan-security`

**Description:** Scan code for security vulnerabilities

**Request Body:**

```json
{
    "code": "string (required)"
}
```

**Response (200):**

```json
{
    "issues": [
        {
            "type": "sql_injection",
            "line": 15,
            "severity": "critical",
            "message": "Dynamic SQL query detected"
        },
        {
            "type": "hardcoded_credential",
            "line": 42,
            "severity": "critical",
            "message": "API key detected in code"
        }
    ],
    "total_issues": 2,
    "critical": 2,
    "high": 0
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/review/scan-security" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "query = f\"SELECT * FROM users WHERE id = {id}\""
  }'
```

---

### Check Code Quality

**Endpoint:** `POST /review/check-quality`

**Description:** Analyze code quality metrics

**Request Body:**

```json
{
    "code": "string (required)"
}
```

**Response (200):**

```json
{
    "line_count": 45,
    "empty_lines": 5,
    "comment_ratio": 0.22,
    "avg_line_length": 48,
    "long_lines": 2,
    "max_line_length": 125,
    "issues": [
        {
            "type": "long_line",
            "line": 23,
            "message": "Line exceeds 100 characters (125 chars)"
        }
    ],
    "score": 7.5
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/review/check-quality" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "def add(a, b):\n    \"\"\"Add two numbers\"\"\"\n    return a + b"
  }'
```

---

### Generate AI Review

**Endpoint:** `POST /review/generate-review`

**Description:** Generate AI-powered code review using Gemini API

**Request Body:**

```json
{
    "code": "string (required)",
    "plan": "string (optional)",
    "context": "string (optional)"
}
```

**Response (200):**

```json
{
    "score": 8.5,
    "summary": "Well-structured code with good security practices",
    "strengths": [
        "Clear function naming",
        "Proper error handling",
        "Good test coverage"
    ],
    "improvements": [
        "Add type hints for better IDE support",
        "Consider adding docstrings"
    ],
    "recommendation": "approve",
    "confidence": 0.92
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/review/generate-review" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GEMINI_API_KEY" \
  -d '{
    "code": "def authenticate(user, pwd):\n    return verify_password(user, pwd)",
    "plan": "Add user authentication"
  }'
```

---

### Post Review to PR

**Endpoint:** `POST /review/post-review`

**Description:** Post a code review as a comment on a GitHub PR

**Request Body:**

```json
{
    "owner": "string (required)",
    "repo": "string (required)",
    "pr_number": "integer (required)",
    "review": {
        "score": "number",
        "summary": "string",
        "strengths": ["string"],
        "improvements": ["string"],
        "recommendation": "string"
    },
    "dry_run": "boolean (default: false)"
}
```

**Response (201):**

```json
{
    "success": true,
    "comment_id": 987654321,
    "url": "https://github.com/owner/repo/pull/123#issuecomment-987654321",
    "posted_at": "2024-01-15T12:00:00Z"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/review/post-review" \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "myorg",
    "repo": "myrepo",
    "pr_number": 123,
    "review": {
        "score": 8.5,
        "summary": "Good work",
        "recommendation": "approve"
    }
  }'
```

---

### Check Auto-Approval

**Endpoint:** `POST /review/auto-approve`

**Description:** Check if a review should be auto-approved

**Request Body:**

```json
{
    "score": "number (required)",
    "recommendation": "string (required)",
    "has_security_issues": "boolean (optional)"
}
```

**Response (200):**

```json
{
    "should_approve": true,
    "score": 9.0,
    "recommendation": "approve",
    "meets_criteria": true,
    "reason": "Score >= 8.0 and no security issues detected"
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/review/auto-approve" \
  -H "Content-Type: application/json" \
  -d '{
    "score": 9.0,
    "recommendation": "approve",
    "has_security_issues": false
  }'
```

---

## Test Orchestration Endpoints

### Discover Tests

**Endpoint:** `GET /tests/discover`

**Description:** Discover all test files in the repository

**Parameters:**

- `test_dir` (query): String - Test directory path (default: "tests")

**Response (200):**

```json
{
    "tests": [
        "tests/test_auth.py",
        "tests/test_database.py",
        "tests/test_security.py"
    ],
    "count": 3
}
```

**Example Request:**

```bash
curl -X GET "http://localhost:8000/tests/discover?test_dir=tests"
```

---

### Run Tests

**Endpoint:** `POST /tests/run`

**Description:** Run tests with optional coverage analysis

**Request Body:**

```json
{
    "test_path": "string (default: 'tests')",
    "verbose": "boolean (default: true)",
    "coverage": "boolean (default: true)",
    "markers": "string (optional)",
    "dry_run": "boolean (default: false)"
}
```

**Response (200):**

```json
{
    "success": true,
    "return_code": 0,
    "stdout": "45 passed in 12.5s",
    "tests_passed": 45,
    "tests_failed": 0,
    "coverage": {
        "percent_covered": 87.5,
        "num_statements": 400,
        "num_missing": 50
    }
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/tests/run" \
  -H "Content-Type: application/json" \
  -d '{
    "test_path": "tests",
    "coverage": true,
    "verbose": true
  }'
```

---

### Check Coverage

**Endpoint:** `POST /tests/coverage`

**Description:** Check if code coverage meets threshold

**Request Body:**

```json
{
    "threshold": "number (default: 80.0)",
    "coverage_json": "string (default: 'coverage.json')"
}
```

**Response (200):**

```json
{
    "meets_threshold": true,
    "percent_covered": 87.5,
    "threshold": 80.0,
    "num_statements": 400,
    "num_missing": 50,
    "files": 15
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/tests/coverage" \
  -H "Content-Type: application/json" \
  -d '{"threshold": 85.0}'
```

---

### Run Full Pipeline

**Endpoint:** `POST /tests/pipeline`

**Description:** Run complete test pipeline: lint → type check → tests → coverage

**Request Body:**

```json
{
    "dry_run": "boolean (default: false)"
}
```

**Response (200):**

```json
{
    "success": true,
    "steps": [
        {
            "name": "linting",
            "success": true,
            "return_code": 0
        },
        {
            "name": "type_checking",
            "success": true,
            "return_code": 0
        },
        {
            "name": "tests",
            "success": true,
            "return_code": 0,
            "coverage": 87.5
        }
    ]
}
```

**Example Request:**

```bash
curl -X POST "http://localhost:8000/tests/pipeline" \
  -H "Content-Type: application/json" \
  -d '{"dry_run": false}'
```

---

## Health Check Endpoints

### PR Creation Health

**Endpoint:** `GET /pr/health`

**Response (200):**

```json
{
    "status": "healthy",
    "service": "PR Creation",
    "version": "2.0",
    "github_token_configured": true
}
```

---

### Code Review Health

**Endpoint:** `GET /review/health`

**Response (200):**

```json
{
    "status": "healthy",
    "service": "Code Review",
    "version": "2.0",
    "gemini_api_configured": true
}
```

---

### Test Orchestration Health

**Endpoint:** `GET /tests/health`

**Response (200):**

```json
{
    "status": "healthy",
    "service": "Test Orchestration",
    "version": "2.0",
    "pytest_available": true
}
```

---

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
    "error": "Error description",
    "error_code": "ERROR_CODE",
    "status_code": 400,
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_abc123xyz"
}
```

### Common HTTP Status Codes

| Code | Meaning | Example |
|------|---------|---------|
| 200 | Success | Request completed |
| 201 | Created | PR successfully created |
| 400 | Bad Request | Invalid parameters |
| 401 | Unauthorized | Missing or invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Task/PR not found |
| 429 | Rate Limited | Too many requests |
| 500 | Server Error | Internal error |

---

## Authentication

### Token Configuration

All endpoints require proper token configuration:

```bash
# GitHub Token (required for PR/review endpoints)
export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Gemini API Key (required for review generation)
export GEMINI_API_KEY="AIzaxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Authorization Header

Include authorization in requests:

```bash
curl -H "Authorization: Bearer $GITHUB_TOKEN" \
     -H "X-API-Key: $GEMINI_API_KEY" \
     http://localhost:8000/api/endpoint
```

---

## Rate Limiting

### Default Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| PR Creation | 60 req/min | 60 seconds |
| Code Review | 30 req/min | 60 seconds |
| Test Orchestration | 10 req/min | 60 seconds |
| All Other | 100 req/min | 60 seconds |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1705317600
```

### Retry Logic

When rate limited (429):

```json
{
    "error": "Too many requests",
    "status_code": 429,
    "retry_after": 30
}
```

Recommended retry strategy:

- Wait for `retry_after` seconds
- Use exponential backoff
- Max 3 retries

---

**Phase 2 API Reference - Complete** ✅
