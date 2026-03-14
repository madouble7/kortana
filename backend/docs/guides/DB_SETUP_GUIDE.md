# Database Setup Guide for Kor'tana

## Overview

Kor'tana uses PostgreSQL 16 for persistent storage and Redis 7 for caching. This guide covers setup, initialization, and migration management.

## Prerequisites

### 1. Install PostgreSQL

**Windows:**

```powershell
# Option A: Download from https://www.postgresql.org/download/windows/
# Install with default settings
# Remember the password you set for 'postgres' user

# Option B: Using Chocolatey
choco install postgresql
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo service postgresql start
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'supersecretpassword';"
```

**macOS:**

```bash
brew install postgresql@16
brew services start postgresql@16
```

### 2. Install Redis

**Windows (WSL2):**

```bash
sudo apt update
sudo apt install redis-server
sudo service redis-server start
```

**Docker (Cross-platform):**

```bash
docker run --name kortana-redis -p 6379:6379 -d redis:7-alpine
```

## Database Configuration

### Environment Variables

Your `.env` file already contains:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kortana
DB_USER=postgres
DB_PASSWORD=supersecretpassword
```

### Create Database

```bash
# Windows (Command Prompt)
createdb -U postgres kortana

# Linux/macOS
sudo -u postgres createdb kortana

# Or using psql
psql -U postgres -c "CREATE DATABASE kortana;"
```

### Verify Connection

```bash
psql -U postgres -d kortana -c "SELECT version();"
```

## Running Migrations

### 1. Initialize (Already Done)

```bash
cd c:\KOR-TANA\kortana\backend
alembic init alembic
```

### 2. Configure alembic.ini

Already configured with:

```ini
sqlalchemy.url = postgresql://postgres:supersecretpassword@localhost:5432/kortana
```

### 3. Run Initial Migration

```bash
# When PostgreSQL is running
alembic upgrade head
```

### 4. View Migration Status

```bash
alembic current
alembic history
```

## Migration Workflow

### Creating New Migrations

```bash
# 1. Modify models in models.py
# 2. Generate migration
alembic revision --autogenerate -m "Description of changes"

# 3. Review generated migration in alembic/versions/
# 4. Apply migration
alembic upgrade head
```

### Common Commands

```bash
# Upgrade to latest
alembic upgrade head

# Downgrade one step
alembic downgrade -1

# Downgrade to specific version
alembic downgrade <revision_id>

# View current version
alembic current

# View migration history
alembic history --verbose
```

## Docker Compose Setup

The `docker-compose.yml` already includes PostgreSQL and Redis:

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: supersecretpassword
      POSTGRES_DB: kortana
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

Start with:

```bash
cd c:\KOR-TANA\kortana
docker-compose up -d postgres redis
```

## Database Schema

### Tables Created

1. **users** - User accounts and authentication
2. **api_keys** - Programmatic access keys
3. **agents** - Autonomous AI agents
4. **agent_executions** - Agent execution history
5. **memories** - Agent memory storage
6. **tasks** - Autonomous tasks/goals
7. **audit_logs** - Compliance and debugging

### Relationships

```
Users (1) → (N) Agents
Users (1) → (N) API Keys
Agents (1) → (N) Executions
Agents (1) → (N) Memories
Agents (1) → (N) Tasks
```

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
# Windows
services.msc | find "PostgreSQL"

# Linux
sudo service postgresql status

# macOS
brew services list | grep postgres
```

### Database Not Found

```bash
# List databases
psql -U postgres -c "\l"

# Create if missing
createdb -U postgres kortana
```

### Permission Issues

```bash
# Grant privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE kortana TO postgres;"
```

### Migration Errors

```bash
# Reset migrations (development only)
rm -rf alembic/versions/*
alembic init alembic
# Update alembic.ini and env.py again
alembic revision --autogenerate -m "Initial schema"
```

## Production Considerations

### Security

1. **Change default password** in `.env`
2. **Use strong passwords** for database users
3. **Enable SSL** for remote connections
4. **Restrict network access** (bind to localhost or private network)
5. **Regular backups** with `pg_dump`

### Performance

1. **Connection pooling** (configured in SQLAlchemy)
2. **Index optimization** (automatic with Alembic)
3. **Regular vacuuming** (PostgreSQL auto-vacuum)
4. **Monitor slow queries** with `pg_stat_statements`

### Backups

```bash
# Manual backup
pg_dump -U postgres kortana > backup.sql

# Restore
psql -U postgres kortana < backup.sql

# Automated (cron/systemd)
# 0 2 * * * pg_dump -U postgres kortana > /backups/kortana_$(date +\%Y\%m\%d).sql
```

## Testing Database

### Quick Test Script

```python
# test_db.py
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from models import Base

async def test_connection():
    engine = create_async_engine(
        "postgresql+asyncpg://postgres:supersecretpassword@localhost:5432/kortana"
    )

    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT version()"))
        print("✓ Database connected:", result.scalar())

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test_connection())
```

### Run Test

```bash
python test_db.py
```

## Next Steps

1. ✅ Install PostgreSQL and Redis
2. ✅ Create database `kortana`
3. ✅ Run `alembic upgrade head`
4. ✅ Test connection with `python init_db.py`
5. ✅ Start backend: `uvicorn main:app --reload`
6. ✅ Verify: `curl http://localhost:8000/api/health`

## Files Created

- `models.py` - SQLAlchemy models
- `alembic.ini` - Migration configuration
- `alembic/env.py` - Migration environment
- `alembic/versions/001_initial_schema.py` - Initial migration
- `init_db.py` - Database connection test
- `setup_migrations.py` - Migration setup helper

## Quick Reference

```bash
# Start everything
docker-compose up -d postgres redis
createdb -U postgres kortana
alembic upgrade head
python -m uvicorn main:app --reload

# Check status
psql -U postgres -d kortana -c "\dt"
alembic current
```

---

**Status:** ✅ Migration files ready, waiting for PostgreSQL to be running
**Next:** Start PostgreSQL and run `alembic upgrade head`
