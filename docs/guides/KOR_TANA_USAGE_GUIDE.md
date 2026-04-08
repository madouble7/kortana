# 🌟 **KOR'TANA - How to Interact & Watch Her Work**

**Date:** January 14, 2026
**Purpose:** User guide for interacting with the Kor'tana Constellation

---

## 🚀 **Starting KOR'TANA**

### Option 1: Terminal Commands

```bash
# Terminal 1: Start the Backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start the Frontend (when ready)
cd frontend
npm start
```

### Option 2: Using the API Directly

```bash
# Check if KOR'TANA is alive
curl http://localhost:8000/api/health

# View all available endpoints
curl http://localhost:8000/
```

---

## 🌐 **Access Points**

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | <http://localhost:3000> | React UI for interaction |
| **API Docs** | <http://localhost:8000/docs> | Interactive API documentation |
| **Health Check** | <http://localhost:8000/api/health> | System status |
| **Metrics** | <http://localhost:8000/api/metrics> | Performance metrics |
| **ReDoc** | <http://localhost:8000/redoc> | Alternative API docs |

---

## 🤖 **How to Interact with KOR'TANA**

### 1. **Using the Dashboard (Recommended)**

1. Open <http://localhost:3000>
2. You'll see the dashboard with:
   - System status (online/offline)
   - Active agents
   - Task queue
   - Performance metrics

3. **Navigate sections:**
   - **Overview** - System health and stats
   - **Agents** - Create and manage AI agents
   - **Tasks** - Queue and monitor tasks
   - **Memory** - Knowledge base browser
   - **GitHub** - Repository integration
   - **Settings** - Configuration

---

### 2. **Using API Commands**

#### Health Check

```bash
curl http://localhost:8000/api/health
```

Response:

```json
{
  "status": "alive",
  "message": "Kor'tana backend is breathing",
  "environment": "development",
  "version": "1.0.0"
}
```

#### Create an Agent

```bash
curl -X POST http://localhost:8000/api/agents/create \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Assistant",
    "description": "Helps research topics",
    "model": "gemini-pro",
    "temperature": 0.7
  }'
```

#### List Agents

```bash
curl http://localhost:8000/api/agents/list
```

#### Create a Task

```bash
curl -X POST http://localhost:8000/api/task-queue \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research AI Trends",
    "description": "Research latest AI developments",
    "priority": 5
  }'
```

#### Check Task Status

```bash
curl http://localhost:8000/api/task-queue
```

#### Store in Memory

```bash
curl -X POST http://localhost:8000/api/memory/add_document \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Project Notes",
    "content": "KOR'TANA is an autonomous AI constellation"
  }'
```

#### Search Memory

```bash
curl "http://localhost:8000/api/memory/search?query=AI"
```

---

### 3. **Using Python Scripts**

```python
# examples/interact.py
import requests

API_URL = "http://localhost:8000"

def check_health():
    """Check if KOR'TANA is online"""
    response = requests.get(f"{API_URL}/api/health")
    print(f"Status: {response.json()['status']}")

def list_agents():
    """List all active agents"""
    response = requests.get(f"{API_URL}/api/agents/list")
    agents = response.json().get('agents', [])
    for agent in agents:
        print(f"- {agent['name']} ({agent['status']})")

def create_task(name, description, priority=5):
    """Create a new task"""
    response = requests.post(f"{API_URL}/api/task-queue", json={
        "name": name,
        "description": description,
        "priority": priority
    })
    print(f"Task created: {response.json()}")

def search_memory(query):
    """Search the knowledge base"""
    response = requests.get(f"{API_URL}/api/memory/search?query={query}")
    print(f"Results: {response.json()}")

if __name__ == "__main__":
    print("🌟 KOR'TANA Interaction Demo")
    print("=" * 40)
    check_health()
    print()
    print("Creating a task...")
    create_task("Test Task", "Testing KOR'TANA functionality")
```

---

### 4. **Using the API Documentation**

1. Open <http://localhost:8000/docs>
2. Click on any endpoint to expand
3. Click "Try it out"
4. Fill in parameters
5. Click "Execute"
6. See the response and curl command

---

## 👀 **How to Watch KOR'TANA Work**

### 1. **Real-time Dashboard**

The dashboard auto-refreshes every 30 seconds:

- Watch agents change status (idle → running → completed)
- Monitor task queue progress
- See CPU/Memory usage in real-time

### 2. **Terminal Logs**

When running `uvicorn main:app --reload --port 8000`, you'll see:

```
🚀 Kor'tana API starting in development mode
📝 Request: GET /api/health - 200 OK
🤖 Agent 'Research Assistant' started
📋 Task 'Research AI' created
✅ Task 'Research AI' completed
```

### 3. **API Metrics Endpoint**

```bash
# Get performance metrics
curl http://localhost:8000/api/metrics

# Response includes:
# - Request counts
# - Error rates
# - Cache hit rates
# - Response times
```

### 4. **Detailed Health Check**

```bash
curl http://localhost:8000/api/health/detailed
```

Shows:

- Database connectivity
- Cache status
- CPU/Memory/Disk usage
- Component health

---

## 🎯 **Common Interactions**

### A. **Run an AI Agent**

```bash
# 1. Create agent
curl -X POST http://localhost:8000/api/agents/create \
  -H "Content-Type: application/json" \
  -d '{"name": "Writer", "model": "gemini-pro"}'

# 2. Execute task with agent
curl -X POST http://localhost:8000/api/agents/execute/1 \
  -H "Content-Type: application/json" \
  -d '{"task": "Write a poem about stars"}'
```

### B. **Store and Retrieve Knowledge**

```bash
# Store information
curl -X POST http://localhost:8000/api/memory/add_document \
  -H "Content-Type: application/json" \
  -d '{"title": "Meeting Notes", "content": "Discussed Q1 goals"}'

# Later, search for it
curl "http://localhost:8000/api/memory/search?query=Q1 goals"
```

### C. **Queue a Background Task**

```bash
# Create task
curl -X POST http://localhost:8000/api/task-queue \
  -H "Content-Type: application/json" \
  -d '{"name": "Data Processing", "priority": 3}'

# Check status
curl http://localhost:8000/api/task-queue
```

---

## 📊 **Monitoring Commands**

### Quick Status

```bash
curl http://localhost:8000/api/health
```

### Full System Info

```bash
curl http://localhost:8000/api/health/system
```

### Performance Metrics

```bash
curl http://localhost:8000/api/health/metrics
```

### Component Health

```bash
curl http://localhost:8000/api/health/detailed
```

---

## 🎨 **Example Workflow**

```bash
# 1. Start KOR'TANA
cd backend && uvicorn main:app --reload --port 8000

# 2. In another terminal, interact
echo "=== Checking Health ==="
curl http://localhost:8000/api/health

echo "=== Creating Agent ==="
curl -X POST http://localhost:8000/api/agents/create \
  -H "Content-Type: application/json" \
  -d '{"name": "ChatBot", "description": "Conversational AI"}'

echo "=== Creating Task ==="
curl -X POST http://localhost:8000/api/task-queue \
  -H "Content-Type: application/json" \
  -d '{"name": "Welcome Message", "description": "Generate welcome message"}'

echo "=== Checking Tasks ==="
curl http://localhost:8000/api/task-queue

echo "=== Checking System ==="
curl http://localhost:8000/api/health/detailed
```

---

## 🔧 **Troubleshooting**

### KOR'TANA not responding?

```bash
# Check if running
curl http://localhost:8000/api/health

# View logs
# (check terminal where uvicorn is running)
```

### Dashboard not loading?

1. Check backend is running on port 8000
2. Refresh browser
3. Check browser console for errors

### API returning errors?

1. Check endpoint URL is correct
2. Verify JSON format
3. Check terminal logs

---

## 🌟 **Next Steps**

1. **Explore the Dashboard** - <http://localhost:3000>
2. **Try the API** - <http://localhost:8000/docs>
3. **Run examples** - `python backend/examples/01_quickstart.py`
4. **Monitor health** - `curl http://localhost:8000/api/health/detailed`

---

**Kor'tana is ready to work with you! 🌌**
