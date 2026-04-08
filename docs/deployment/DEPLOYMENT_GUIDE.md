# Kor'tana Deployment Guide

## Table of Contents
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Development Setup](#development-setup)
- [Production Deployment](#production-deployment)
- [Monitoring and Alerting](#monitoring-and-alerting)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

Kor'tana is a multi-component autonomous AI system with the following services:

### Backend (Python/FastAPI)
- **LLM Router**: Multi-model LLM provider with fallback strategy
- **GitHub Automation**: Autonomous issue analysis and PR creation
- **Task Scheduler**: Celery + Beat for periodic tasks
- **Database**: PostgreSQL for persistent storage
- **Cache**: Redis for caching and task queue

### Frontend (React/Vite)
- User dashboard for managing issues and PRs
- Real-time monitoring of autonomous tasks
- API documentation viewer

### Monitoring
- Prometheus metrics exported on `/metrics`
- Health checks on `/api/health`
- Structured JSON logging to stdout

## Prerequisites

### Local Development
- Docker & Docker Compose 20.10+
- Python 3.11+
- Node.js 20+
- Git

### Production
- Docker Engine 20.10+
- Docker Compose 2.0+
- A VPS or cloud VM (2+ GB RAM, 2+ CPU cores)
- Static IP for security group rules
- DNS domain for HTTPS

## Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/KOR-TANA/kortana.git
cd kortana
```

### 2. Create Environment Files
```bash
cp .env.example .env
```

Edit `.env`:
```env
ENVIRONMENT=development
GEMINI_API_KEY=your_key_here
GITHUB_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here
DISCORD_BOT_TOKEN=your_token_here
```

### 3. Start Development Stack
```bash
docker compose up -d

# Verify all services are running
docker compose ps

# View logs
docker compose logs -f
```

### 4. Access Services
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **PostgreSQL**: localhost:5432 (user: kortana, password: kortana_dev)
- **Redis**: localhost:6379

### 5. Run Tests
```bash
docker compose exec backend pytest -v
```

## Production Deployment

### 1. Prepare Production Environment

Create `.env.prod`:
```bash
cp .env.prod.example .env.prod
```

Edit `.env.prod` with production secrets:
```env
ENVIRONMENT=production
GEMINI_API_KEY=production_key
GITHUB_TOKEN=production_token
DB_PASSWORD=strong_random_password
REDIS_PASSWORD=strong_random_password
SECRET_KEY=generate_with_secrets_module
```

### 2. Build Production Image
```bash
docker build -t kortana-backend:latest -f Dockerfile.prod .
```

### 3. Deploy Using Docker Compose

On production server:
```bash
cd /opt/kortana
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

### 4. Initialize Database
```bash
docker compose -f docker-compose.prod.yml exec backend \
  alembic upgrade head
```

### 5. Verify Deployment
```bash
curl http://localhost:8000/api/health

# Expected response:
# {"status": "alive", "message": "Kor'tana backend is breathing", "environment": "production"}
```

### 6. Configure HTTPS (Let's Encrypt)
```bash
docker run --rm \
  -v /opt/kortana/certs:/etc/letsencrypt \
  -p 80:80 -p 443:443 \
  certbot/certbot certonly --standalone \
  -d your-domain.com
```

### 7. Setup Nginx Reverse Proxy
```nginx
upstream kortana_backend {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /opt/kortana/certs/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /opt/kortana/certs/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://kortana_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Monitoring and Alerting

### Prometheus Metrics
Kor'tana exports Prometheus metrics on `/metrics`:

```bash
curl http://localhost:8000/metrics
```

Key metrics:
- `http_requests_total`: Total HTTP requests by endpoint
- `llm_request_duration_seconds`: LLM API latency
- `task_duration_seconds`: Task execution time
- `errors_total`: Total errors by type

### Health Checks
```bash
curl http://localhost:8000/api/health

# Response:
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
    ...
  }
}
```

### Setup Prometheus + Grafana

1. **Add to docker-compose.prod.yml**:
```yaml
prometheus:
  image: prom/prometheus:latest
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  ports:
    - "9090:9090"

grafana:
  image: grafana/grafana:latest
  ports:
    - "3000:3000"
  environment:
    - GF_SECURITY_ADMIN_PASSWORD=admin
  volumes:
    - grafana_data:/var/lib/grafana
```

2. **prometheus.yml**:
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'kortana'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
docker compose logs backend

# Common issues:
# - Database connection: Check DB_HOST, DB_PORT in .env
# - Redis connection: Check REDIS_URL
# - API keys missing: Check GEMINI_API_KEY, GITHUB_TOKEN
```

### High Memory Usage
```bash
# Check which service is using memory
docker stats

# Restart the service
docker compose restart backend

# Scale down workers if needed
# Edit celery configuration to reduce worker count
```

### Database Migrations Failed
```bash
# Check migration status
docker compose exec backend alembic current

# Rollback
docker compose exec backend alembic downgrade -1

# Rerun
docker compose exec backend alembic upgrade head
```

### GitHub API Rate Limiting
- Check GitHub API limits: https://api.github.com/rate_limit
- Use GitHub App instead of Personal Access Token for higher limits
- Implement exponential backoff (already included in resilience.py)

### Tasks Not Processing
```bash
# Check Celery worker status
docker compose exec backend celery -A celery_config inspect active

# Check Celery Beat schedule
docker compose exec backend celery -A celery_config inspect scheduled

# Restart workers
docker compose restart celery_worker celery_beat
```

### Logs Not Appearing
```bash
# Check log level in .env
LOG_LEVEL=DEBUG

# Restart backend
docker compose restart backend

# View logs
docker compose logs -f backend
```
