# Kor'tana Backend Security Documentation

**Date:** January 14, 2026
**Status:** Phase 2 - Security Implementation in Progress

---

## Overview

This document describes the security architecture and features implemented in the Kor'tana backend.

## Authentication System

### JWT-Based Authentication

Kor'tana uses JSON Web Tokens (JWT) for API authentication.

**Token Types:**
- **Access Token:** Short-lived (30 minutes) token for API access
- **Refresh Token:** Longer-lived (7 days) token for obtaining new access tokens

**Token Structure:**
```python
{
    "sub": user_id,           # User ID
    "email": "user@example.com",
    "role": "user",           # user | admin | service
    "exp": 1705276800,        # Expiration timestamp
    "type": "access"          # Token type
}
```

### Authentication Endpoints

| Endpoint | Method | Auth Required | Description |
|----------|--------|---------------|-------------|
| `/api/auth/register` | POST | No | Register new user |
| `/api/auth/login` | POST | No | Login and get tokens |
| `/api/auth/refresh` | POST | No | Refresh access token |
| `/api/auth/me` | GET | Yes | Get current user info |
| `/api/auth/logout` | POST | Yes | Logout (client-side) |
| `/api/auth/change-password` | POST | Yes | Change password |
| `/api/auth/deactivate` | POST | Yes | Deactivate account |

### Protected Routes

All API routes except authentication and health require valid JWT tokens:

- `/api/gemini/*` - Protected (AI service calls)
- `/api/memory/*` - Protected (User memory)
- `/api/agents/*` - Protected (Agent management)
- `/api/github/*` - Protected (GitHub integration)
- `/api/autonomy/*` - Protected (Autonomous tasks)
- `/api/knowledge/*` - Protected (Knowledge base)
- `/api/task-queue/*` - Protected (Task management)

### Using Authentication

**Login:**
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=yourPassword"
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Making Authenticated Requests:**
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Refreshing Tokens:**
```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

## Rate Limiting

### Tier-Based Limits

| Tier | Requests | Window | Use Case |
|------|----------|--------|----------|
| Anonymous | 20 | 60s | Unauthenticated users |
| User | 100 | 60s | Standard users |
| Admin | 500 | 60s | Administrative users |
| Service | 1000 | 60s | API services |

### Rate Limit Headers

All API responses include rate limit headers:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705276800
```

### Rate Limit Response

When rate limit is exceeded:
```json
{
  "error": "RATE_LIMIT_EXCEEDED",
  "message": "Rate limit exceeded. Maximum 100 requests per 60 seconds.",
  "limit": 100,
  "remaining": 0,
  "reset_after": 30
}
```

---

## Password Security

### Requirements

- Minimum 8 characters
- No maximum length limit
- bcrypt hashing with cost factor 12

### Password Hashing

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Hash password
hashed = pwd_context.hash(password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

---

## Role-Based Access Control (RBAC)

### User Roles

| Role | Permissions |
|------|-------------|
| `user` | Standard API access |
| `admin` | Full access + admin endpoints |
| `service` | High rate limit + service endpoints |

### Authorization Dependencies

```python
from routers.auth import get_current_user, get_admin_user

# Require authentication
@router.get("/protected")
async def protected_endpoint(user: TokenData = Depends(get_current_user)):
    return {"user": user.email}

# Require admin role
@router.get("/admin-only")
async def admin_endpoint(user: TokenData = Depends(get_admin_user)):
    return {"message": "Admin access granted"}
```

---

## Security Best Practices

### API Key Management

1. **Never expose API keys in client-side code**
2. **Use environment variables for secrets**
3. **Rotate keys regularly**
4. **Monitor key usage**

### Environment Variables

```bash
# Required for production
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=postgresql://user:pass@host:5432/db

# Optional overrides
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### CORS Configuration

The API is configured with strict CORS settings:

```python
# Only allow specific origins in production
CORS_ORIGINS = [
    "https://yourdomain.com",
    "http://localhost:3000",  # Development only
]
```

**Never use `["*"]` in production!**

---

## Production Deployment Checklist

### Before Going Live

- [ ] Change `SECRET_KEY` to a strong random value (32+ characters)
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure proper CORS origins
- [ ] Set up HTTPS/TLS
- [ ] Configure database with SSL
- [ ] Set up Redis for session storage
- [ ] Enable rate limiting with appropriate tiers
- [ ] Configure logging to production level
- [ ] Set up monitoring and alerting
- [ ] Create backup procedures
- [ ] Document incident response plan

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | Yes | JWT signing key (keep secret!) |
| `ENVIRONMENT` | Yes | Set to "production" |
| `DATABASE_URL` | Yes | Database connection string |
| `REDIS_URL` | No | Redis connection for sessions |
| `CORS_ORIGINS` | Yes | Comma-separated allowed origins |

---

## Security Headers

The API includes security-related headers:

```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

---

## Monitoring & Logging

### Security Events Logged

- Failed login attempts
- Token validation failures
- Rate limit exceeded
- Unauthorized access attempts
- Password changes
- Account deactivations

### Log Format

```json
{
  "timestamp": "2026-01-14T21:00:00Z",
  "level": "WARNING",
  "event": "AUTH_FAILURE",
  "message": "Invalid login attempt for user@example.com",
  "details": {
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
}
```

---

## Compliance Notes

### GDPR Considerations

- User data is stored with encryption at rest
- Users can export their data via `/api/auth/me`
- Users can deactivate their account via `/api/auth/deactivate`
- Data retention policies should be configured

### Data Protection

- Passwords are never stored in plain text
- JWT tokens are stateless and expire automatically
- PII is minimized in logs
- Encryption in transit (HTTPS) is required

---

## API Rate Limits by Endpoint

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/api/auth/*` | 20 | 60s |
| `/api/gemini/*` | 50 | 60s |
| `/api/memory/*` | 100 | 60s |
| `/api/agents/*` | 100 | 60s |
| `/api/github/*` | 30 | 60s |
| `/api/autonomy/*` | 20 | 60s |
| `/api/knowledge/*` | 100 | 60s |
| `/api/task-queue/*` | 100 | 60s |

---

## Incident Response

### If Security Breach Detected

1. **Immediately revoke all active tokens**
2. **Notify affected users**
3. **Investigate the attack vector**
4. **Patch vulnerabilities**
5. **Review and strengthen security measures**
6. **Document incident for compliance**

### Contact

For security issues, contact: [Your Security Contact]

---

## References

- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Specification](https://jwt.io/)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [BCrypt Documentation](https://passlib.readthedocs.io/)

---

**Last Updated:** January 14, 2026
**Next Review:** February 14, 2026
**Owner:** Kor'tana Security Team
