# 🤖 Kor'tana Control Panel

Welcome to the Kor'tana Autonomous Development System! Here's how to interact with it:

## ✨ Quick Start

### 1. Check Kor'tana Status

```bash
curl http://localhost:8000/api/always-on/status
```

### 2. Start Always-On Monitoring

```bash
curl -X POST http://localhost:8000/api/always-on/start
```

### 3. Get Dashboard

```bash
curl http://localhost:8000/api/always-on/dashboard
```

### 4. View Recent Tasks

```bash
curl http://localhost:8000/api/always-on/tasks
```

---

## 📡 API Endpoints

### **Monitoring Control**

- `POST /api/always-on/start` - Start autonomous monitoring
- `POST /api/always-on/stop` - Stop monitoring
- `GET /api/always-on/status` - Get current status
- `GET /api/always-on/health` - Health check
- `POST /api/always-on/force-check` - Force immediate cycle

### **Task Management**

- `GET /api/always-on/tasks` - List recent tasks
- `GET /api/always-on/tasks/status` - Task status summary
- `POST /api/always-on/tasks/{task_id}/approve` - Approve/reject task
- `POST /api/always-on/tasks/{task_id}/retry` - Retry failed task

### **Monitoring Data**

- `GET /api/always-on/dashboard` - Full dashboard
- `GET /api/always-on/metrics` - System metrics
- `GET /api/always-on/actions` - Recent actions
- `POST /api/always-on/log` - Log event

---

## 🖥️ Interactive Interface

Run the Python interface for easy menu-driven control:

```bash
python kor_tana_interface.py
```

This provides an interactive menu where you can:

- View system status
- Start/stop monitoring
- Manage tasks
- View dashboards and metrics
- Force monitoring cycles
- Approve/reject tasks
- Export reports

---

## 📊 Example Workflows

### View Current Status

```bash
curl http://localhost:8000/api/always-on/status | jq .
```

### Monitor a Full Cycle

```bash
# 1. Check status
curl http://localhost:8000/api/always-on/status

# 2. Force immediate check
curl -X POST http://localhost:8000/api/always-on/force-check

# 3. View results
curl http://localhost:8000/api/always-on/dashboard
```

### Approve Pending Task

```bash
curl -X POST http://localhost:8000/api/always-on/tasks/{task_id}/approve \
  -H "Content-Type: application/json" \
  -d '{"approved": true, "notes": "Approved by Matt"}'
```

### Get Task Summary

```bash
curl http://localhost:8000/api/always-on/tasks/status | jq .
```

### Start Monitoring in Background

```bash
curl -X POST http://localhost:8000/api/always-on/start
echo "✅ Always-On Monitoring Started"
```

---

## 🎯 System Architecture

Kor'tana operates on the **Human Only Protocol (HOP)**:

- **AUTO Tasks**: Fully autonomous - executed immediately
- **HO Tasks**: Require human scaffolding and guidance
- **APPROVAL Tasks**: Need explicit human approval

The system continuously:

1. 🔍 **Monitors** GitHub for new issues
2. 🎯 **Analyzes** using Gemini AI
3. 📋 **Plans** implementation steps
4. 👤 **Routes** to human when needed
5. 🤖 **Executes** autonomously where safe
6. ✅ **Completes** and reports results

---

## 💡 Tips

- **Monitor is persistent**: Starts in background, runs continuously
- **Human oversight**: Critical decisions escalate to you automatically
- **Task logging**: All actions logged for audit trail
- **Retry capability**: Failed tasks can be retried
- **Dashboard**: Real-time view of all system activity

---

## 🔗 Connection Info

- **Base URL**: <http://localhost:8000>
- **API Prefix**: /api/always-on
- **Port**: 8000
- **Protocol**: HTTP REST with JSON

---

## ⚙️ Configuration

Key environment variables:

- `ALWAYS_ON_MONITORING` - Enable/disable monitoring (true/false)
- `MONITOR_CHECK_INTERVAL` - Check interval in seconds (default: 60)
- `MAX_CONCURRENT_TASKS` - Max tasks to process per cycle (default: 5)

---

**Kor'tana is now online and ready for autonomous development operations! 🚀**
