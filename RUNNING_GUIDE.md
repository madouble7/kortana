# 🚀 Quick Start: Running KOR'TANA with Autonomous Monitoring

This guide gets you up and running with KOR'TANA's autonomous development system in minutes.

## One-Command Start

```bash
./run_and_monitor.sh
```

That's it! This single command will:
1. ✅ Check prerequisites
2. ⚙️ Setup environment
3. 🚀 Start backend
4. 👁️ Launch monitoring dashboard

## What You'll See

```
==============================================================================
🤖 KOR'TANA - AUTONOMOUS DEVELOPMENT MONITOR
==============================================================================

📊 SYSTEM HEALTH
✅ Backend: ONLINE
   Environment: development
   Version: 0.1.0

🧠 HUMAN ONLY PROTOCOL (HOP)
📈 Overall Progress:
   Total Tasks: 11
   ✅ Completed: 1
   🔄 In Progress: 0
   ⏳ Pending: 7

🤖 AUTO Tasks: 1/6 (16.7%)
   ✅ Create Environment Template

👤 HO Tasks: 0/4 (0.0%)
   ⚠️  4 pending human actions:
      • Create GitHub Personal Access Token
      • Create Gemini API Key
      • Configure PostgreSQL Database
```

## How It Works

### The Human Only Protocol (HOP)

KOR'TANA uses a three-tier autonomy system:

| Type | Symbol | Description | Action |
|------|--------|-------------|--------|
| **AUTO** | 🤖 | Fully automated | Executes immediately |
| **HO** | 👤 | Human only | Provides scaffolded steps |
| **APPROVAL** | 🔐 | Needs approval | Waits for human OK |

### Monitoring Dashboard

The dashboard shows real-time status of:
- **System Health**: Backend status and version
- **HOP Progress**: Task completion across all types
- **AUTO Tasks**: Automated tasks executing in real-time
- **HO Tasks**: Human actions needed with step-by-step guides
- **Autonomy System**: Active development tasks from GitHub

### Auto-Refresh

The dashboard refreshes every 5 seconds automatically, showing:
- Task completion in real-time
- Failed tasks that need attention
- Next human action required
- Overall autonomy progress

## Commands

### Full Monitoring Dashboard
```bash
./run_and_monitor.sh
```
Launches full real-time monitoring dashboard with auto-refresh.

### Quick Status Check
```bash
./run_and_monitor.sh --status
```
Shows current status snapshot without continuous monitoring.

### Trigger Autonomous Cycle
```bash
./run_and_monitor.sh --cycle
```
Manually triggers one autonomous execution cycle.

### Run Without Docker
```bash
./run_and_monitor.sh --local --install
```
Runs backend locally without Docker (installs dependencies first).

## API Endpoints

Once running, access these endpoints:

### Health Check
```bash
curl http://localhost:8000/api/health
```

### HOP Status
```bash
curl http://localhost:8000/api/autonomy/hop/protocol/status
```

### Trigger Cycle
```bash
curl -X POST http://localhost:8000/api/autonomy/hop/protocol/auto/cycle
```

### Next HO Task
```bash
curl http://localhost:8000/api/autonomy/hop/protocol/ho/next
```

### API Documentation
Open in browser: http://localhost:8000/docs

## Environment Variables

Configure monitoring behavior:

```bash
# Backend URL (default: http://localhost:8000)
export KORTANA_BACKEND_URL="http://localhost:8000"

# Refresh interval in seconds (default: 5)
export MONITOR_REFRESH_INTERVAL=10

# Show detailed logs (default: false)
export SHOW_DETAILED_LOGS=true
```

## Workflow Example

### 1. Start System
```bash
./run_and_monitor.sh
```

### 2. Monitor AUTO Tasks
Watch as KOR'TANA automatically:
- Creates environment files
- Installs dependencies
- Validates codebase
- Runs migrations

### 3. Complete HO Tasks
When you see:
```
👤 HO Tasks: 0/4 (0.0%)
   ⚠️  4 pending human actions:
      • Create GitHub Personal Access Token
```

Follow the scaffolded instructions provided.

### 4. Approve When Ready
When prerequisites are met:
```
🔐 Approval Tasks: 0/1
   🟢 1 ready for approval:
      • Start Backend Server
```

Review and approve the action.

### 5. Let It Run
KOR'TANA handles everything else autonomously!

## Stopping

Press `Ctrl+C` in the monitoring dashboard to stop.

To stop the backend:
```bash
# If using Docker
docker compose down

# If running locally
kill $(ps aux | grep "[u]vicorn main:app" | awk '{print $2}')
```

## Troubleshooting

### Backend Not Starting
```bash
# Check logs
tail -f /tmp/kortana-backend.log

# Or with Docker
docker compose logs backend
```

### Port Already in Use
```bash
# Find process using port 8000
lsof -ti:8000

# Kill it
kill $(lsof -ti:8000)
```

### Missing Dependencies
```bash
# Install Python dependencies
pip3 install httpx

# Install backend dependencies
cd backend && pip3 install -r requirements.txt
```

### Can't Connect
```bash
# Verify backend is running
curl http://localhost:8000/api/health

# Check if port is listening
netstat -tuln | grep 8000
```

## Documentation

- 📖 **[MONITORING_GUIDE.md](MONITORING_GUIDE.md)** - Complete monitoring documentation
- 📖 **[DEMO_OUTPUT.md](DEMO_OUTPUT.md)** - Live demo outputs and examples
- 📖 **[SCAFFOLDED_HO_STEPS.md](SCAFFOLDED_HO_STEPS.md)** - Human-only task instructions
- 📖 **[KOR_TANA_AUTONOMOUS_PROTOCOL.md](KOR_TANA_AUTONOMOUS_PROTOCOL.md)** - Protocol specification
- 📖 **[README.md](README.md)** - Project overview

## Features

✨ **Real-Time Monitoring**
- Auto-refreshing dashboard
- Live task status updates
- Progress tracking

🤖 **Autonomous Execution**
- AUTO tasks run without approval
- HO tasks scaffolded with instructions
- Approval tasks wait for human review

📊 **Comprehensive Status**
- System health
- Task classification breakdown
- Autonomy progress metrics

🔧 **Easy Control**
- One-command start
- Simple status checks
- Manual cycle triggering

## System Requirements

- **Python 3.11+** (3.12.3 recommended)
- **pip3** for Python package management
- **Docker** (optional, recommended for full stack)
- **httpx** Python package (auto-installed)

## Getting Help

Need help? Check:
1. This guide for quick start
2. [MONITORING_GUIDE.md](MONITORING_GUIDE.md) for detailed docs
3. [DEMO_OUTPUT.md](DEMO_OUTPUT.md) for example outputs
4. Backend logs: `/tmp/kortana-backend.log`
5. API docs: http://localhost:8000/docs

---

**Ready to see autonomous development in action?**

```bash
./run_and_monitor.sh
```

Let KOR'TANA show you the future of autonomous software development! 🚀
