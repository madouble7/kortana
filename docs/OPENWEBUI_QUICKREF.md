# Open WebUI Quick Reference

## Quick Start Commands

### Linux/Mac
```bash
# Start everything
./scripts/start_openwebui.sh

# Stop everything
./scripts/stop_openwebui.sh
```

### Windows
```cmd
# Start everything
scripts\start_openwebui.bat

# Stop everything
scripts\stop_openwebui.bat
```

## URLs

- **Open WebUI**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **MCP Discover**: http://localhost:8001/api/mcp/discover

## Configuration

### Environment Variables (.env)
```env
KORTANA_API_KEY=your-secure-key
WEBUI_SECRET_KEY=your-secret-key
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Open WebUI Connection Settings
- **Base URL**: `http://host.docker.internal:8000/api/openai/v1`
- **API Key**: Your `KORTANA_API_KEY`
- **Models**: gpt-4, gpt-3.5-turbo, claude-3-opus, claude-3-sonnet

## MCP Tools

| Tool | Endpoint | Purpose |
|------|----------|---------|
| search_memory | /api/mcp/memory/search | Search Kor'tana's memory |
| store_memory | /api/mcp/memory/store | Store new information |
| list_goals | /api/mcp/goals/list | List current goals |
| create_goal | /api/mcp/goals/create | Create new goal |
| gather_context | /api/mcp/context/gather | Gather contextual info |

## Common Issues

### "Invalid API Key"
- Check `KORTANA_API_KEY` in `.env`
- Restart backend after changing `.env`
- Verify key in Open WebUI settings matches

### Can't Connect to Backend
- Ensure backend is running: `curl http://localhost:8000/health`
- Use `host.docker.internal` in Docker, not `localhost`
- Check firewall settings

### MCP Tools Not Working
- Verify MCP server is running: `docker ps | grep mcp`
- Check MCP config: `config/mcp/mcp_config.json`
- Restart MCP: `docker restart kortana-mcp-server`

## API Endpoints

### OpenAI-Compatible
- `GET /api/openai/v1/models` - List models
- `POST /api/openai/v1/chat/completions` - Chat (supports streaming)

### MCP
- `GET /api/mcp/discover` - List available tools
- `POST /api/mcp/memory/search` - Search memory
- `POST /api/mcp/memory/store` - Store memory
- `POST /api/mcp/goals/list` - List goals
- `POST /api/mcp/goals/create` - Create goal
- `POST /api/mcp/context/gather` - Gather context

## Docker Commands

```bash
# View logs
docker logs kortana-open-webui
docker logs kortana-mcp-server

# Restart services
docker compose -f docker-compose.openwebui.yml restart

# Stop services
docker compose -f docker-compose.openwebui.yml down

# Remove volumes (clean slate)
docker compose -f docker-compose.openwebui.yml down -v
```

## Testing

### Test Backend
```bash
curl http://localhost:8000/health
```

### Test OpenAI API
```bash
curl -X POST http://localhost:8000/api/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Test MCP
```bash
curl http://localhost:8000/api/mcp/discover \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Full Documentation

See `docs/OPENWEBUI_INTEGRATION.md` for complete documentation.
