# Kor'tana Integration Guide - Making It All Work Together

## Quick Start Integration

This guide shows how to integrate all the new components into your existing Kor'tana installation.

## Step 1: Update Dependencies

```bash
# Pull latest requirements
pip install -r backend/requirements.txt

# Install optional development dependencies
pip install -r backend/requirements.txt[dev]
```

## Step 2: Update Main Application

Update `backend/main.py` to include new routers and systems:

```python
# Add these imports after existing imports
from llm_router import get_llm_router
from github_automation import get_github_engine
from resilience import get_resilient_executor
from monitoring import HealthChecker, MetricsCollector, get_metrics_data, get_metrics_content_type

# Add metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(content=get_metrics_data(), media_type=get_metrics_content_type())

# Add enhanced health check
@app.get("/api/health/full")
async def full_health_check():
    """Comprehensive system health check"""
    health = await HealthChecker.full_health_check()
    status_code = 200 if health.status == "healthy" else 503
    return health
```

## Step 3: Enable Celery Task Queue

Create `backend/celery_worker.py`:

```python
from celery_config import app
from celery.bin import worker

if __name__ == '__main__':
    w = worker.worker(app=app)
    w.start(
        queues=['default', 'high_priority', 'low_priority'],
        concurrency=4,
        loglevel='info',
    )
```

Run workers:
```bash
# Terminal 1: Celery Worker
python backend/celery_worker.py

# Terminal 2: Celery Beat (Scheduler)
celery -A backend.celery_config beat --loglevel=info
```

## Step 4: Configure Environment Variables

Add to `.env`:

```env
# LLM Configuration
GEMINI_API_KEY=your_key
OPENAI_API_KEY=your_key
GROQ_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# GitHub Integration
GITHUB_TOKEN=your_token
GITHUB_OWNER=KOR-TANA
GITHUB_REPO=kortana

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=optional_sentry_url
LOG_LEVEL=INFO
```

## Step 5: Update Docker Compose

Add these services to `docker-compose.yml`:

```yaml
# Celery Worker
celery_worker:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: kortana-celery-worker
  command: celery -A backend.celery_config worker --loglevel=info --queues=default,high_priority,low_priority
  depends_on:
    - redis
    - postgres
    - backend
  environment:
    - DATABASE_URL=postgresql://kortana:kortana_dev@postgres:5432/kortana_db
    - REDIS_URL=redis://redis:6379/0
    - ENVIRONMENT=development
  volumes:
    - ./backend/src:/app/src
  networks:
    - kortana-network

# Celery Beat (Scheduler)
celery_beat:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: kortana-celery-beat
  command: celery -A backend.celery_config beat --loglevel=info
  depends_on:
    - redis
    - postgres
  environment:
    - DATABASE_URL=postgresql://kortana:kortana_dev@postgres:5432/kortana_db
    - REDIS_URL=redis://redis:6379/0
    - ENVIRONMENT=development
  networks:
    - kortana-network

# Prometheus (Optional - for monitoring)
prometheus:
  image: prom/prometheus:latest
  container_name: kortana-prometheus
  ports:
    - "9090:9090"
  volumes:
    - ./prometheus.yml:/etc/prometheus/prometheus.yml
    - prometheus_data:/prometheus
  command:
    - '--config.file=/etc/prometheus/prometheus.yml'
  networks:
    - kortana-network

volumes:
  prometheus_data:
```

## Step 6: Configure Prometheus (Optional)

Create `prometheus.yml`:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'kortana'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
```

## Step 7: Setup GitHub Webhook

1. Go to repository Settings → Webhooks
2. Add webhook with:
   - **Payload URL**: `https://your-domain.com/api/github/webhook`
   - **Content type**: `application/json`
   - **Events**: Issues, Pull requests
   - **Secret**: Generate and add to `.env` as `GITHUB_WEBHOOK_SECRET`

## Step 8: Run Integration Tests

```bash
# Run all tests
pytest backend/tests -v

# Run with coverage
pytest backend/tests --cov=backend --cov-report=html

# Run specific test file
pytest backend/tests/test_llm_router.py -v
```

## Step 9: Verify Integration

```bash
# Check LLM router
curl -X POST http://localhost:8000/api/gemini/models

# Check GitHub integration
curl -X POST http://localhost:8000/api/github/analyze \
  -H "Content-Type: application/json" \
  -d '{"issue_number": 1, "repo": "owner/repo"}'

# Check task queue
curl http://localhost:8000/api/task-queue/pending

# Check health
curl http://localhost:8000/api/health/full

# Check metrics
curl http://localhost:8000/metrics | grep http_requests_total
```

## Step 10: Monitor Operations

### Real-time Logs
```bash
# Backend logs
docker compose logs -f backend

# Celery worker logs
docker compose logs -f celery_worker

# Celery beat logs
docker compose logs -f celery_beat

# All logs
docker compose logs -f
```

### Task Queue Status
```bash
# List pending tasks
celery -A backend.celery_config inspect pending

# List active tasks
celery -A backend.celery_config inspect active

# List scheduled tasks
celery -A backend.celery_config inspect scheduled

# Purge queue
celery -A backend.celery_config purge
```

### Database Status
```bash
# Connect to database
docker compose exec postgres psql -U kortana -d kortana_db

# Check tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

# Check records
SELECT COUNT(*) FROM agent_executions;
```

## Common Issues and Solutions

### LLM Router Returns 404
- Check if new endpoint is registered in `main.py`
- Verify `llm_router.py` is in backend directory
- Restart backend service

### Celery Tasks Not Processing
- Check Redis connection: `redis-cli ping`
- Check worker is running: `docker compose ps`
- Check queues: `celery -A backend.celery_config inspect active_queues`

### GitHub Webhook Not Triggering
- Verify webhook in repository settings
- Check webhook secret matches `.env`
- Test webhook manually in GitHub UI
- Check backend logs for webhook errors

### Metrics Not Appearing
- Verify Prometheus scrape endpoint: `curl http://localhost:8000/metrics`
- Check Prometheus config points to correct host:port
- Verify `PROMETHEUS_ENABLED=true` in `.env`

### High Memory Usage
- Check active tasks: `docker compose exec celery_worker ps aux`
- Limit worker concurrency in `celery_config.py`
- Increase Docker memory limit in docker-compose.yml

## Advanced Configuration

### Custom LLM Model Priority
Edit `llm_router.py` `_get_primary_model()`:
```python
def _get_primary_model(self) -> Optional[ModelConfig]:
    # Change model priority
    return self.models.get("gpt-4o")  # Use GPT-4 as primary
```

### Adjust Task Queue Settings
Edit `celery_config.py`:
```python
app.conf.task_soft_time_limit = 60 * 60  # 1 hour timeout
app.conf.worker_prefetch_multiplier = 4  # Process 4 tasks at once
```

### Custom Health Check
Add to `monitoring.py`:
```python
@staticmethod
async def check_custom_service() -> tuple[bool, str]:
    # Your custom check here
    return True, "Status OK"
```

## Performance Tuning

### For High Load
1. Increase Celery workers: Add more worker containers
2. Increase Redis connections: Edit Redis maxclients
3. Increase PostgreSQL connections: Edit max_connections
4. Enable response caching: Set `ResponseCacheMiddleware` in main.py

### For Low Latency
1. Reduce task timeout in celery_config.py
2. Use Groq models (faster) in LLM router
3. Enable Redis connection pooling
4. Add circuit breaker timeouts

## Next Steps

1. **Deploy to Production**: Follow DEPLOYMENT_GUIDE.md
2. **Setup Monitoring**: Configure Prometheus + Grafana
3. **Enable Alerting**: Configure email/Slack alerts
4. **Automate Backups**: Setup PostgreSQL backups
5. **Performance Testing**: Run load tests with k6 or JMeter

## Support

For issues or questions:
1. Check logs: `docker compose logs`
2. Check health: `curl http://localhost:8000/api/health/full`
3. Review API docs: `http://localhost:8000/docs`
4. Check GitHub issues: https://github.com/KOR-TANA/kortana/issues
