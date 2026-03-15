# Open WebUI Troubleshooting Guide

## Common Issues and Solutions

### 1. Backend Connection Issues

#### Problem: "Failed to connect to backend" in Open WebUI

**Symptoms:**
- Open WebUI displays connection error
- Health check fails
- No models appear in dropdown

**Diagnosis:**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check backend logs
tail -f logs/kortana.log  # or wherever your logs are
```

**Solutions:**

1. **Backend not running:**
   ```bash
   # Start the backend
   python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000
   ```

2. **Wrong URL in Open WebUI:**
   - In Open WebUI settings, use `http://host.docker.internal:8000/api/openai/v1`
   - NOT `http://localhost:8000` (Docker can't resolve localhost)

3. **Port already in use:**
   ```bash
   # Find process using port 8000
   lsof -i :8000  # Linux/Mac
   netstat -ano | findstr :8000  # Windows
   
   # Kill the process or use a different port
   ```

---

### 2. Authentication Errors

#### Problem: "Invalid API key" or "Unauthorized" errors

**Symptoms:**
- 401 Unauthorized responses
- Authentication failures in logs
- Can't access any endpoints

**Diagnosis:**
```bash
# Test with curl
curl -H "Authorization: Bearer YOUR_KEY" http://localhost:8000/api/openai/v1/models
```

**Solutions:**

1. **API key mismatch:**
   - Check `.env` file: `KORTANA_API_KEY=your-key-here`
   - Restart backend after changing `.env`
   - Update key in Open WebUI settings

2. **Missing Bearer prefix:**
   - Format must be: `Authorization: Bearer YOUR_KEY`
   - Not just `Authorization: YOUR_KEY`

3. **Environment variable not loaded:**
   ```bash
   # Verify environment
   echo $KORTANA_API_KEY  # Linux/Mac
   echo %KORTANA_API_KEY%  # Windows
   
   # If empty, source .env or restart terminal
   ```

---

### 3. Docker Issues

#### Problem: Docker containers won't start

**Symptoms:**
- `docker compose up` fails
- Containers exit immediately
- Port binding errors

**Diagnosis:**
```bash
# Check container status
docker ps -a

# View container logs
docker logs kortana-open-webui
docker logs kortana-mcp-server

# Check for port conflicts
docker ps | grep -E "3000|8001"
```

**Solutions:**

1. **Port conflicts:**
   ```bash
   # Change ports in docker-compose.openwebui.yml
   ports:
     - "3001:8080"  # Instead of 3000:8080
   ```

2. **Missing environment variables:**
   - Ensure `.env` file exists
   - Docker Compose reads from `.env` automatically

3. **Image pull issues:**
   ```bash
   # Pull images manually
   docker pull ghcr.io/open-webui/open-webui:main
   docker pull ghcr.io/open-webui/mcpo:main
   ```

4. **Volume permission issues:**
   ```bash
   # On Linux, fix permissions
   sudo chown -R $USER:$USER ./config/mcp
   ```

---

### 4. MCP Tools Not Working

#### Problem: MCP tools don't appear or fail to execute

**Symptoms:**
- Tools not visible in Open WebUI
- Tool invocations fail
- MCP errors in logs

**Diagnosis:**
```bash
# Check MCP server
curl http://localhost:8001/api/mcp/discover \
  -H "Authorization: Bearer YOUR_KEY"

# Check MCP container
docker logs kortana-mcp-server
```

**Solutions:**

1. **MCP server not running:**
   ```bash
   # Restart MCP container
   docker restart kortana-mcp-server
   
   # Or restart all
   docker compose -f docker-compose.openwebui.yml restart
   ```

2. **Invalid MCP configuration:**
   - Check `config/mcp/mcp_config.json` syntax
   - Validate JSON: `python -m json.tool config/mcp/mcp_config.json`

3. **MCP not configured in Open WebUI:**
   - Go to Admin Settings → External Tools
   - Add MCP server: `http://host.docker.internal:8001`
   - Set authentication token

4. **Wrong endpoint URLs:**
   - MCP endpoints should point to backend: `http://host.docker.internal:8000/api/mcp/*`
   - Not to MCP container directly

---

### 5. Streaming Issues

#### Problem: Responses don't stream, appear all at once

**Symptoms:**
- Long wait, then full response
- No progressive display
- Streaming toggle has no effect

**Diagnosis:**
```bash
# Test streaming with curl
curl -X POST http://localhost:8000/api/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hi"}],"stream":true}'
```

**Solutions:**

1. **Streaming not implemented yet:**
   - Current implementation returns complete response
   - Enhancement planned for future version

2. **Buffering issues:**
   - Check nginx/proxy configuration if using one
   - Disable response buffering

3. **CORS issues:**
   - Ensure CORS headers allow streaming
   - Check browser console for errors

---

### 6. Model Selection Issues

#### Problem: Models don't appear in Open WebUI

**Symptoms:**
- Empty model dropdown
- "No models available" message
- Only default models visible

**Diagnosis:**
```bash
# Check available models
curl http://localhost:8000/api/openai/v1/models \
  -H "Authorization: Bearer YOUR_KEY"
```

**Solutions:**

1. **API connection issue:**
   - Fix backend connection first (see issue #1)

2. **Add more models:**
   Edit `src/kortana/adapters/openwebui_adapter.py`:
   ```python
   models = [
       OpenAIModel(id="gpt-4", ...),
       OpenAIModel(id="gpt-3.5-turbo", ...),
       OpenAIModel(id="your-custom-model", ...),
   ]
   ```

3. **Model not configured in LLM router:**
   - Check `config/models_config.json`
   - Ensure model has API keys configured

---

### 7. Memory/Goal Tools Failing

#### Problem: Memory search or goal operations fail

**Symptoms:**
- MCP tool returns errors
- "Service unavailable" messages
- Database errors in logs

**Diagnosis:**
```bash
# Test memory endpoint directly
curl -X POST http://localhost:8000/api/mcp/memory/search \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"tool_name":"search_memory","parameters":{"query":"test","limit":5}}'
```

**Solutions:**

1. **Database not initialized:**
   ```bash
   # Initialize database
   alembic upgrade head
   
   # Or run setup
   python scripts/setup_database.py
   ```

2. **Service import errors:**
   - Check that MemoryService and GoalService are properly imported
   - Review logs for import errors

3. **Missing dependencies:**
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   ```

---

### 8. Performance Issues

#### Problem: Slow responses or timeouts

**Symptoms:**
- Long wait times
- Timeout errors
- High CPU/memory usage

**Diagnosis:**
```bash
# Check resource usage
docker stats kortana-open-webui
htop  # or top on Linux/Mac
Task Manager  # on Windows

# Check logs for slow queries
grep "slow" logs/kortana.log
```

**Solutions:**

1. **Database optimization:**
   - Add indexes to frequently queried fields
   - Enable query caching
   - Use connection pooling

2. **Memory search optimization:**
   - Reduce search limit
   - Optimize vector embeddings
   - Use faster embedding model

3. **LLM API latency:**
   - Check API status
   - Consider caching common responses
   - Use faster models for simple queries

4. **Container resources:**
   ```yaml
   # In docker-compose.openwebui.yml, add:
   deploy:
     resources:
       limits:
         cpus: '2'
         memory: 4G
   ```

---

### 9. Environment Issues

#### Problem: Environment variables not loading

**Symptoms:**
- "API key not configured" errors
- Settings not taking effect
- Default values used instead

**Diagnosis:**
```bash
# Check if .env exists
ls -la .env

# Verify contents
cat .env

# Check if loaded in Python
python -c "import os; print(os.getenv('KORTANA_API_KEY'))"
```

**Solutions:**

1. **Create .env file:**
   ```bash
   cp .env.template .env
   # Edit .env with your values
   ```

2. **Restart services:**
   ```bash
   # Restart backend
   # (Stop uvicorn and start again)
   
   # Restart Docker
   docker compose -f docker-compose.openwebui.yml restart
   ```

3. **Check .env location:**
   - Should be in project root
   - Docker Compose looks for `.env` in same directory as compose file

---

### 10. Installation Issues

#### Problem: Dependencies won't install

**Symptoms:**
- pip install errors
- Import errors
- Version conflicts

**Diagnosis:**
```bash
# Check Python version
python --version  # Should be 3.11+

# Check pip
pip --version

# Try installing individually
pip install fastapi
```

**Solutions:**

1. **Python version too old:**
   ```bash
   # Install Python 3.11 or newer
   # Use pyenv or download from python.org
   ```

2. **Virtual environment issues:**
   ```bash
   # Create fresh venv
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   
   # Install dependencies
   pip install -r requirements.txt
   ```

3. **Dependency conflicts:**
   ```bash
   # Try with specific versions
   pip install "fastapi>=0.104.1"
   
   # Or use poetry
   poetry install
   ```

---

## Debugging Commands

### Quick Health Check
```bash
# Check all services
curl http://localhost:8000/health          # Backend
curl http://localhost:3000/health          # Open WebUI
curl http://localhost:8001/health          # MCP (if available)

# Check models
curl -H "Authorization: Bearer YOUR_KEY" \
  http://localhost:8000/api/openai/v1/models

# Test chat
curl -X POST http://localhost:8000/api/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"gpt-4","messages":[{"role":"user","content":"Hello"}]}'
```

### View Logs
```bash
# Backend logs (if using uvicorn)
tail -f logs/uvicorn.log

# Docker logs
docker logs -f kortana-open-webui
docker logs -f kortana-mcp-server

# Follow all logs
docker compose -f docker-compose.openwebui.yml logs -f
```

### Container Management
```bash
# List containers
docker ps -a

# Restart containers
docker compose -f docker-compose.openwebui.yml restart

# Stop containers
docker compose -f docker-compose.openwebui.yml down

# Clean restart (removes volumes)
docker compose -f docker-compose.openwebui.yml down -v
docker compose -f docker-compose.openwebui.yml up -d
```

### Network Debugging
```bash
# Check ports
netstat -an | grep -E "8000|3000|8001"  # Linux/Mac
netstat -an | findstr "8000 3000 8001"  # Windows

# Test connectivity
telnet localhost 8000
# Or
nc -zv localhost 8000  # Linux/Mac
```

---

## Getting Help

If you can't resolve your issue:

1. **Check logs first**: Most issues show up in logs
2. **Verify configuration**: Double-check all URLs and keys
3. **Test components individually**: Isolate the problem
4. **Search existing issues**: Check GitHub issues
5. **Ask for help**: Include:
   - Error messages
   - Logs
   - Configuration (without sensitive data)
   - Steps to reproduce

---

## Additional Resources

- [Integration Guide](OPENWEBUI_INTEGRATION.md)
- [Architecture Documentation](OPENWEBUI_ARCHITECTURE.md)
- [Quick Reference](OPENWEBUI_QUICKREF.md)
- [Open WebUI Docs](https://docs.openwebui.com)
- [FastAPI Docs](https://fastapi.tiangolo.com)
