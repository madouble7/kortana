# Kor'tana Docker Guide

Complete guide for containerizing and deploying Kor'tana using Docker and Docker Compose.

## Quick Start

### Prerequisites
- Docker Desktop 4.0+ or Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB+ RAM available for containers
- 10GB+ disk space

### Development Setup

1. **Clone and prepare environment:**
```bash
cp .env.template .env
# Edit .env with your configuration
```

2. **Start services:**
```bash
# Using Docker Compose
docker-compose up -d

# Or using Makefile
make up
```

3. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Nginx (Production)                    │
│                  Reverse Proxy & SSL                     │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴─────────┐
        │                   │
┌───────▼──────┐    ┌──────▼────────┐
│   Frontend   │    │    Backend    │
│  (React/Nginx)│    │   (FastAPI)   │
└──────────────┘    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌──────▼────────┐  ┌──────▼─────────┐
│  PostgreSQL  │    │     Redis     │  │   Utilities    │
│   Database   │    │     Cache     │  │   Services     │
└──────────────┘    └───────────────┘  └────────────────┘
```

## Services

### Core Services

#### **Backend** (`kortana-backend`)
- **Image:** Built from `kortana/backend/Dockerfile`
- **Port:** 8000
- **Purpose:** FastAPI REST API server
- **Dependencies:** PostgreSQL, Redis
- **Health:** `/api/health`

#### **Frontend** (`kortana-frontend`)
- **Image:** Built from `kortana/frontend/Dockerfile`
- **Port:** 3000
- **Purpose:** React-based user interface
- **Dependencies:** Backend
- **Health:** `/health`

### Infrastructure Services

#### **PostgreSQL** (`kortana-postgres`)
- **Image:** `postgres:16-alpine`
- **Port:** 5432
- **Purpose:** Primary database
- **Volume:** `postgres_data`

#### **Redis** (`kortana-redis`)
- **Image:** `redis:7-alpine`
- **Port:** 6379
- **Purpose:** Caching and session storage
- **Volume:** `redis_data`

### Utility Services

#### **Background Agent** (`kortana-background-agent`)
- **Port:** 8001
- **Purpose:** Background task processing
- **Dependencies:** Redis, Backend

#### **Heartbeat Service** (`kortana-heartbeat`)
- **Port:** 8002
- **Purpose:** System health monitoring
- **Dependencies:** Backend

#### **Hub Dispatcher** (`kortana-hub-dispatcher`)
- **Port:** 8003
- **Purpose:** Message routing and dispatch
- **Dependencies:** Redis

### Monitoring (Optional)

#### **Prometheus** (`kortana-prometheus`)
- **Port:** 9090
- **Purpose:** Metrics collection
- **Profile:** `monitoring`

#### **Grafana** (`kortana-grafana`)
- **Port:** 3001
- **Purpose:** Metrics visualization
- **Profile:** `monitoring`

## Docker Files

### Dockerfiles

| Service | Location | Base Image |
|---------|----------|------------|
| Backend | `kortana/backend/Dockerfile` | `python:3.11-slim` |
| Frontend (Prod) | `kortana/frontend/Dockerfile` | `nginx:alpine` |
| Frontend (Dev) | `kortana/frontend/Dockerfile.dev` | `node:20-alpine` |
| Background Agent | `utilities/background-agent/Dockerfile` | `python:3.11-slim` |
| Heartbeat | `utilities/heartbeat-service/Dockerfile` | `python:3.11-alpine` |
| Hub Dispatcher | `utilities/hub-dispatcher/Dockerfile` | `python:3.11-slim` |

### Compose Files

- **docker-compose.yml** - Development environment
- **docker-compose.prod.yml** - Production environment
- **docker-compose.monitoring.yml** - Monitoring stack (optional)

## Best Practices Implemented

### Security
- ✅ **Non-root users** - All containers run as non-root users
- ✅ **Read-only filesystems** - Production containers use read-only root FS
- ✅ **No new privileges** - Security option prevents privilege escalation
- ✅ **Minimal base images** - Alpine and slim variants
- ✅ **Secret management** - Environment variables for sensitive data
- ✅ **Network isolation** - Separate frontend/backend networks in production

### Performance
- ✅ **Multi-stage builds** - Smaller final images
- ✅ **Layer caching** - Dependencies before source code
- ✅ **Resource limits** - CPU and memory constraints
- ✅ **Health checks** - Automatic container health monitoring
- ✅ **Connection pooling** - Database and Redis connection pools

### Maintainability
- ✅ **.dockerignore** - Exclude unnecessary files
- ✅ **Logging** - JSON logging with rotation
- ✅ **Labels** - Metadata for images
- ✅ **Volume management** - Persistent data storage
- ✅ **Restart policies** - Automatic recovery

## Usage

### Using Docker Compose

#### Start all services:
```bash
docker-compose up -d
```

#### Start with monitoring:
```bash
docker-compose --profile monitoring up -d
```

#### Stop services:
```bash
docker-compose down
```

#### View logs:
```bash
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Restart a service:
```bash
docker-compose restart backend
```

### Using Makefile

The Makefile provides convenient shortcuts:

```bash
# View available commands
make help

# Build images
make build

# Start development
make up

# Start with monitoring
make up-monitoring

# View logs
make logs
make logs-backend
make logs-frontend

# Check health
make health

# Database backup
make backup-db

# Shell access
make shell-backend
make shell-db

# Clean up
make clean
```

## Environment Configuration

### Development (.env)

Copy `.env.template` to `.env`:
```bash
cp .env.template .env
```

Key settings:
- `ENVIRONMENT=development`
- `DEBUG=true`
- `LOG_LEVEL=debug`

### Production (.env.production)

Copy `.env.production.template` to `.env.production`:
```bash
cp .env.production.template .env.production
```

Key differences:
- `ENVIRONMENT=production`
- `DEBUG=false`
- `LOG_LEVEL=warning`
- Stronger passwords
- External URLs

## Building Images

### Build all images:
```bash
make build
```

### Build individual services:
```bash
docker build -t kortana/backend:latest -f kortana/backend/Dockerfile kortana/backend
docker build -t kortana/frontend:latest -f kortana/frontend/Dockerfile kortana/frontend
```

### Build with version tags:
```bash
VERSION=1.0.0 BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ') make build
```

## Deployment

### Development Deployment

```bash
make deploy-dev
# or
docker-compose up -d
```

### Production Deployment

```bash
make deploy-prod
# or
docker-compose -f docker-compose.prod.yml up -d
```

### Production Checklist

- [ ] Create `.env.production` with secure credentials
- [ ] Generate SSL certificates
- [ ] Configure domain names in Nginx
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set resource limits appropriately
- [ ] Enable monitoring stack
- [ ] Test health checks
- [ ] Set up external volumes for data
- [ ] Configure firewall rules

## Monitoring

### Enable Monitoring Stack

```bash
docker-compose --profile monitoring up -d
```

Access:
- **Prometheus:** http://localhost:9090
- **Grafana:** http://localhost:3001 (default: admin/admin)

### Service Health Checks

```bash
# Check all services
make health

# Individual checks
curl http://localhost:8000/api/health
curl http://localhost:3000/health
```

### View Container Stats

```bash
make stats
# or
docker stats
```

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs <service-name>

# Inspect container
docker inspect <container-name>

# Check health status
docker-compose ps
```

### Database connection issues

```bash
# Check PostgreSQL logs
make logs-db

# Test connection
make shell-db

# Verify environment variables
docker-compose exec backend env | grep DB_
```

### Performance issues

```bash
# Check resource usage
docker stats

# Inspect specific service
docker stats kortana-backend

# Check logs for errors
make logs-backend
```

### Clean rebuild

```bash
# Remove everything and rebuild
make clean-all
make build
make up
```

## Backup & Recovery

### Database Backup

```bash
# Create backup
make backup-db

# Manual backup
docker-compose exec postgres pg_dump -U kortana kortana_db > backup.sql
```

### Restore Database

```bash
# Restore from backup
make restore-db

# Manual restore
docker-compose exec -T postgres psql -U kortana kortana_db < backup.sql
```

### Volume Backup

```bash
# Backup PostgreSQL volume
docker run --rm -v kortana_postgres_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres-$(date +%Y%m%d).tar.gz /data

# Backup Redis volume
docker run --rm -v kortana_redis_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis-$(date +%Y%m%d).tar.gz /data
```

## Scaling

### Scale backend replicas:

```bash
docker-compose up -d --scale backend=3
```

### Production scaling (docker-compose.prod.yml):

Edit `BACKEND_REPLICAS` in `.env.production`:
```bash
BACKEND_REPLICAS=5
```

Then deploy:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Security Hardening

### Production Security Checklist

- [ ] Use secrets management (Docker Secrets or external vault)
- [ ] Enable SSL/TLS with valid certificates
- [ ] Set secure passwords for all services
- [ ] Limit container capabilities
- [ ] Use private Docker registry
- [ ] Scan images for vulnerabilities
- [ ] Enable SELinux/AppArmor
- [ ] Configure firewall rules
- [ ] Enable audit logging
- [ ] Regular security updates

### Scan Images for Vulnerabilities

```bash
# Using Docker Scout
docker scout cves kortana/backend:latest

# Using Trivy
trivy image kortana/backend:latest
```

## Development Workflow

### Live Development

1. Start services:
```bash
make up
```

2. Make code changes (auto-reload enabled for backend and frontend)

3. View logs:
```bash
make logs-backend
```

4. Run tests:
```bash
docker-compose exec backend pytest
docker-compose exec frontend npm test
```

### Updating Dependencies

```bash
make update-deps
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Build and Push

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build images
        run: make build
      - name: Run tests
        run: make test
      - name: Push images
        run: |
          docker push kortana/backend:latest
          docker push kortana/frontend:latest
```

## Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [FastAPI Docker Guide](https://fastapi.tiangolo.com/deployment/docker/)
- [Node.js Docker Best Practices](https://github.com/nodejs/docker-node/blob/main/docs/BestPractices.md)

## Support

For issues and questions:
- Check logs: `make logs`
- Check health: `make health`
- Clean rebuild: `make clean && make build && make up`
