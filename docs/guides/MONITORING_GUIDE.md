# Running and Monitoring KOR'TANA Autonomous Development

This guide explains how to run KOR'TANA and monitor its autonomous development capabilities in real-time.

## Quick Start

### Option 1: One-Command Start (Recommended)

```bash
# Start KOR'TANA with Docker and begin monitoring
./run_and_monitor.sh
```

This will:
1. ✅ Check all prerequisites
2. ⚙️ Set up environment files
3. 🚀 Start backend services with Docker
4. 👁️ Launch real-time monitoring dashboard

### Option 2: Manual Start

```bash
# Start services with Docker Compose
docker compose up -d

# Wait for services to be ready (about 10 seconds)
sleep 10

# Start monitoring
python3 monitor_autonomous_dev.py
```

### Option 3: Local Development (No Docker)

```bash
# Install dependencies and run locally
./run_and_monitor.sh --local --install
```

## Monitoring Commands

The monitoring system provides several modes of operation:

### Real-Time Dashboard

```bash
# Continuous real-time monitoring (default)
./run_and_monitor.sh

# Or directly:
python3 monitor_autonomous_dev.py
```

**Dashboard shows:**
- 📊 System health status
- 🧠 Human Only Protocol (HOP) progress
- 🤖 AUTO tasks execution
- 👤 Pending HO (Human Only) tasks
- 🔐 Approval tasks waiting for review
- ⚙️ Active autonomy system tasks

**Controls:**
- `Ctrl+C` - Stop monitoring

### Quick Status Check

```bash
# Get a snapshot of current status
./run_and_monitor.sh --status

# Or directly:
python3 monitor_autonomous_dev.py status
```

### Trigger Autonomous Cycle

```bash
# Manually trigger one HOP cycle
./run_and_monitor.sh --cycle

# Or directly:
python3 monitor_autonomous_dev.py cycle
```

## Configuration

### Environment Variables

Configure the monitoring system with these environment variables:

```bash
# Backend URL (default: http://localhost:8000)
export KORTANA_BACKEND_URL="http://localhost:8000"

# Monitoring refresh interval in seconds (default: 5)
export MONITOR_REFRESH_INTERVAL=5

# Show detailed logs (default: false)
export SHOW_DETAILED_LOGS=true

# Backend port (default: 8000)
export BACKEND_PORT=8000
```

### Backend Configuration

Before running, ensure your backend environment is configured:

1. **Create environment file:**
   ```bash
   cp backend/.env.example backend/.env
   ```

2. **Edit `backend/.env` with your credentials:**
   ```env
   # GitHub Integration
   GITHUB_TOKEN=ghp_your_token_here
   
   # Gemini AI
   GEMINI_API_KEY=AIza_your_key_here
   
   # Database (optional for Docker, uses PostgreSQL container)
   DATABASE_URL=postgresql://kortana:kortana_dev@postgres:5432/kortana_db
   ```

3. **See `SCAFFOLDED_HO_STEPS.md` for detailed credential setup instructions**

## Understanding the Monitoring Dashboard

### System Health Section

```
📊 SYSTEM HEALTH
--------------------------------------------------------------------------------
✅ Backend: ONLINE
   Environment: development
   Version: 1.0.0
```

Shows the backend API status and basic configuration.

### Human Only Protocol Section

```
🧠 HUMAN ONLY PROTOCOL (HOP)
--------------------------------------------------------------------------------
📈 Overall Progress:
   Total Tasks: 8
   ✅ Completed: 4
   🔄 In Progress: 0
   ⏳ Pending: 2
   ❌ Failed: 0
   ⏸️  Waiting for HO: 2

🤖 AUTO Tasks: 4/4 (100.0%)
👤 HO Tasks: 2/4 (50.0%)
   ⚠️  2 pending human actions:
      • Create GitHub Personal Access Token
      • Configure Environment Variables

🔐 Approval Tasks: 0/1
```

**Task Classifications:**

- **🤖 AUTO**: Fully automated tasks that KOR'TANA executes without human approval
- **👤 HO (Human Only)**: Tasks requiring human action (e.g., creating API keys)
- **🔐 APPROVAL**: Tasks that need explicit human approval before execution

### Autonomy System Section

```
⚙️  AUTONOMY SYSTEM
--------------------------------------------------------------------------------
✅ Autonomy Engine: ACTIVE
   📋 Active Tasks: 3
      • Implement user authentication
      • Add database migrations
      • Update API documentation
```

Shows actively running autonomous development tasks from GitHub issues.

## API Endpoints

The backend exposes these monitoring endpoints:

### Health Check
```bash
curl http://localhost:8000/api/health
```

### HOP Status
```bash
# Full protocol status
curl http://localhost:8000/api/autonomy/hop/protocol/status

# Get AUTO tasks ready for execution
curl http://localhost:8000/api/autonomy/hop/protocol/auto/tasks

# Get next HO task
curl http://localhost:8000/api/autonomy/hop/protocol/ho/next

# Get all HO tasks
curl http://localhost:8000/api/autonomy/hop/protocol/ho/all
```

### Trigger Autonomous Execution
```bash
# Run one autonomous cycle
curl -X POST http://localhost:8000/api/autonomy/hop/protocol/auto/cycle

# Execute specific AUTO task
curl -X POST http://localhost:8000/api/autonomy/hop/protocol/auto/execute/task_id

# Mark HO task as completed
curl -X POST http://localhost:8000/api/autonomy/hop/protocol/ho/complete/task_id
```

### Autonomy Status
```bash
# Get autonomy system status
curl http://localhost:8000/api/autonomy/status

# Queue tasks from GitHub issues
curl -X POST http://localhost:8000/api/autonomy/queue

# Get task queue status
curl http://localhost:8000/api/autonomy/queue/status
```

## Troubleshooting

### Backend Won't Start

**Issue:** `Cannot connect to backend`

**Solutions:**
1. Check if Docker is running: `docker ps`
2. Check if port 8000 is available: `lsof -i :8000`
3. View backend logs: `docker compose logs backend`
4. Try restarting: `docker compose restart backend`

### Missing Dependencies

**Issue:** `ModuleNotFoundError: No module named 'httpx'`

**Solution:**
```bash
pip3 install httpx
```

### Docker Compose Not Found

**Issue:** `docker-compose: command not found`

**Solution:**
```bash
# Use docker compose (without hyphen) instead
docker compose up -d
```

### Environment Variables Not Set

**Issue:** `GITHUB_TOKEN not configured`

**Solution:**
1. Copy the example file: `cp backend/.env.example backend/.env`
2. Edit `backend/.env` with your actual credentials
3. See `SCAFFOLDED_HO_STEPS.md` for credential creation instructions

### Database Connection Errors

**Issue:** `Could not connect to database`

**Solutions:**
1. If using Docker: Ensure PostgreSQL container is running
   ```bash
   docker compose ps postgres
   docker compose up -d postgres
   ```

2. If using local PostgreSQL: Check DATABASE_URL in `.env`
   ```env
   DATABASE_URL=postgresql://user:pass@localhost:5432/kortana
   ```

## Advanced Usage

### Custom Refresh Interval

```bash
# Refresh every 10 seconds instead of default 5
MONITOR_REFRESH_INTERVAL=10 python3 monitor_autonomous_dev.py
```

### Detailed Logging Mode

```bash
# Show detailed task logs
SHOW_DETAILED_LOGS=true python3 monitor_autonomous_dev.py
```

### Remote Backend Monitoring

```bash
# Monitor a remote backend
KORTANA_BACKEND_URL="https://kortana-api.example.com" python3 monitor_autonomous_dev.py
```

### Automated Monitoring with systemd

Create a systemd service for continuous monitoring:

```ini
# /etc/systemd/system/kortana-monitor.service
[Unit]
Description=KOR'TANA Autonomous Development Monitor
After=network.target

[Service]
Type=simple
User=kortana
WorkingDirectory=/path/to/kortana
Environment="KORTANA_BACKEND_URL=http://localhost:8000"
ExecStart=/usr/bin/python3 /path/to/kortana/monitor_autonomous_dev.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable kortana-monitor
sudo systemctl start kortana-monitor
sudo systemctl status kortana-monitor
```

## Understanding Autonomous Development

### The Human Only Protocol (HOP)

KOR'TANA uses a three-tier classification system:

1. **AUTO Tasks** - Fully automated, zero human intervention
   - Environment setup
   - Dependency installation
   - Database migrations
   - Code validation
   - Health checks

2. **HO (Human Only) Tasks** - Require human action
   - API key creation
   - Database configuration
   - Security credential setup
   - External service integration

3. **APPROVAL Tasks** - Need explicit approval
   - Server startup
   - Production deployments
   - Security policy changes
   - Major architectural changes

### Monitoring Autonomous Cycles

The monitor tracks autonomous execution cycles:

1. **Fetch**: Pull new issues from GitHub
2. **Analyze**: AI analyzes task requirements
3. **Plan**: Generate implementation plan
4. **Classify**: HOP determines autonomy level
5. **Execute**: AUTO tasks run immediately, HO tasks scaffolded

### Human Intervention Points

When KOR'TANA requires human action:

1. Monitor shows: `⚠️ 2 pending human actions`
2. View details: `python3 monitor_autonomous_dev.py status`
3. See scaffolded instructions in the HO section
4. Complete the human task (e.g., create API key)
5. Mark as complete via API or restart monitoring

## Integration with CI/CD

### GitHub Actions Monitoring

Add monitoring to your CI pipeline:

```yaml
# .github/workflows/monitor-autonomy.yml
name: Monitor Autonomous Development

on:
  schedule:
    - cron: '0 * * * *'  # Every hour
  workflow_dispatch:

jobs:
  monitor:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install httpx
      
      - name: Check Autonomous Status
        env:
          KORTANA_BACKEND_URL: ${{ secrets.BACKEND_URL }}
        run: python3 monitor_autonomous_dev.py status
```

## Next Steps

1. ✅ Start monitoring: `./run_and_monitor.sh`
2. 📊 Watch autonomous execution in real-time
3. 👤 Complete any pending HO tasks when prompted
4. 🚀 Let KOR'TANA handle the rest autonomously

For more information:
- 📖 [SCAFFOLDED_HO_STEPS.md](SCAFFOLDED_HO_STEPS.md) - Setup instructions for HO tasks
- 📖 [KOR_TANA_AUTONOMOUS_PROTOCOL.md](KOR_TANA_AUTONOMOUS_PROTOCOL.md) - Deep dive into HOP
- 📖 [README.md](README.md) - Project overview
- 📖 [DEVELOPMENT_GUIDE.md](DEVELOPMENT_GUIDE.md) - Development documentation
