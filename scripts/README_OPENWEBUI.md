# Open WebUI Integration Scripts

This directory contains scripts for managing the Open WebUI integration with Kor'tana.

## Available Scripts

### Startup Scripts

#### Linux/Mac
```bash
./scripts/start_openwebui.sh
```
- Starts Kor'tana backend on port 8000
- Launches Open WebUI and MCP server via Docker Compose
- Waits for backend to be ready before starting frontend
- Displays URLs and status

#### Windows
```cmd
scripts\start_openwebui.bat
```
- Same functionality as Linux/Mac version
- Opens backend in separate command window
- Displays URLs and status

### Shutdown Scripts

#### Linux/Mac
```bash
./scripts/stop_openwebui.sh
```
- Stops Docker containers
- Terminates backend process

#### Windows
```cmd
scripts\stop_openwebui.bat
```
- Same functionality as Linux/Mac version

### Validation Script

```bash
python scripts/validate_openwebui_integration.py
```
- Validates all integration files exist
- Checks Python syntax
- Validates JSON configuration
- Verifies Docker Compose setup
- Checks main.py integration
- Validates environment template

### Testing Script

```bash
python tests/test_openwebui_integration.py
```
- Comprehensive integration tests
- Structure validation
- Configuration validation
- Documentation checks
- Returns 0 on success, 1 on failure

## Usage Examples

### First Time Setup

1. **Validate integration:**
   ```bash
   python scripts/validate_openwebui_integration.py
   ```

2. **Set up environment:**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Start everything:**
   ```bash
   ./scripts/start_openwebui.sh  # or .bat on Windows
   ```

4. **Access Open WebUI:**
   - Open http://localhost:3000
   - Create admin account
   - Configure Kor'tana connection

### Daily Usage

**Start:**
```bash
./scripts/start_openwebui.sh
```

**Stop:**
```bash
./scripts/stop_openwebui.sh
```

### Troubleshooting

**Check if backend is running:**
```bash
curl http://localhost:8000/health
```

**Check Docker containers:**
```bash
docker ps | grep kortana
```

**View logs:**
```bash
docker logs kortana-open-webui
docker logs kortana-mcp-server
```

**Validate setup:**
```bash
python scripts/validate_openwebui_integration.py
```

## Script Details

### start_openwebui.sh / start_openwebui.bat

**What it does:**
1. Checks for `.env` file, creates from template if missing
2. Starts Kor'tana backend (uvicorn)
3. Waits for backend to become healthy
4. Starts Docker Compose (Open WebUI + MCP server)
5. Displays access URLs

**Requirements:**
- Python 3.11+
- Docker and Docker Compose
- `.env` file with API keys

**Troubleshooting:**
- If backend won't start, check port 8000 availability
- If Docker won't start, check ports 3000 and 8001
- Check logs if health check fails

### stop_openwebui.sh / stop_openwebui.bat

**What it does:**
1. Stops Docker Compose services
2. Finds and kills backend process

**Note:**
- Safe to run multiple times
- Won't affect other Python processes

### validate_openwebui_integration.py

**What it validates:**
- File existence and structure
- Python syntax
- JSON configuration
- Docker Compose setup
- Main.py integration
- Environment configuration

**Exit codes:**
- 0: All checks passed
- 1: One or more checks failed

**Usage in CI/CD:**
```bash
python scripts/validate_openwebui_integration.py
if [ $? -eq 0 ]; then
    echo "Validation passed"
else
    echo "Validation failed"
    exit 1
fi
```

## Environment Variables

Required in `.env`:

```env
# Kor'tana Security
KORTANA_API_KEY=your-secure-api-key
WEBUI_SECRET_KEY=your-long-random-secret-key

# LLM Provider Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Ports

- **3000**: Open WebUI frontend
- **8000**: Kor'tana backend API
- **8001**: MCP server

Ensure these ports are available before starting.

## Common Issues

### Port Already in Use

**Linux/Mac:**
```bash
lsof -i :8000  # Find process using port 8000
kill <PID>     # Kill the process
```

**Windows:**
```cmd
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Permission Denied (Linux/Mac)

```bash
chmod +x scripts/start_openwebui.sh
chmod +x scripts/stop_openwebui.sh
```

### Backend Won't Start

1. Check Python version: `python --version`
2. Check dependencies: `pip list | grep fastapi`
3. Check logs for errors
4. Verify `.env` file exists

### Docker Issues

```bash
# Check Docker is running
docker ps

# Check images are pulled
docker images | grep open-webui

# Pull images manually
docker pull ghcr.io/open-webui/open-webui:main
docker pull ghcr.io/open-webui/mcpo:main
```

## Additional Documentation

- [Integration Guide](../docs/OPENWEBUI_INTEGRATION.md)
- [Quick Reference](../docs/OPENWEBUI_QUICKREF.md)
- [Architecture](../docs/OPENWEBUI_ARCHITECTURE.md)
- [Troubleshooting](../docs/OPENWEBUI_TROUBLESHOOTING.md)

## Contributing

When adding new scripts:

1. Follow existing naming convention
2. Add help/usage information
3. Update this README
4. Make scripts executable (Linux/Mac)
5. Test on multiple platforms if possible
