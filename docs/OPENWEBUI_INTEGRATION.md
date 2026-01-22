# Open WebUI Integration Guide for Kor'tana

This guide explains how to set up and use Open WebUI as a frontend for Kor'tana, including MCP (Model Context Protocol) support for extended LLM functionality.

## Overview

Open WebUI provides a modern, user-friendly chat interface for interacting with Kor'tana. This integration includes:

- **OpenAI-Compatible API**: Seamless connection to Kor'tana's backend
- **MCP Protocol Support**: Extended functionality through Model Context Protocol
- **Memory System Access**: Query and store information in Kor'tana's memory
- **Goal Management**: Create and track autonomous goals
- **Context Gathering**: Real-time context from multiple sources

## Prerequisites

- Docker and Docker Compose installed
- Kor'tana backend running (or ready to start)
- Python 3.11+ (for backend)
- Ports 3000, 8000, and 8001 available

## Quick Start

### 1. Configure Environment Variables

Copy `.env.template` to `.env` and set your API keys:

```bash
cp .env.template .env
```

Edit `.env` and set at minimum:

```env
# Required for Open WebUI authentication
KORTANA_API_KEY=your-secure-api-key-here
WEBUI_SECRET_KEY=your-long-random-secret-key

# Your LLM provider keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start Kor'tana Backend

Start the Kor'tana FastAPI server:

```bash
# Using uvicorn directly
python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000

# Or if you have a startup script
./start_server.bat
```

Verify the backend is running:
```bash
curl http://localhost:8000/health
```

### 3. Start Open WebUI with Docker Compose

Launch Open WebUI and the MCP server:

```bash
docker compose -f docker-compose.openwebui.yml up -d
```

This will start:
- **Open WebUI** on http://localhost:3000
- **MCP Server** on http://localhost:8001

### 4. Access Open WebUI

Open your browser and navigate to:
```
http://localhost:3000
```

On first access, you'll be prompted to create an admin account.

## Configuration

### Open WebUI Settings

After logging in, configure Open WebUI:

1. Click the **Settings** icon (gear) in the sidebar
2. Navigate to **Admin Settings** → **Connections**
3. Click **Add Connection** under OpenAI

Configure the connection:
- **Name**: Kor'tana
- **API Base URL**: `http://host.docker.internal:8000/api/openai/v1`
- **API Key**: Your `KORTANA_API_KEY` from `.env`
- **Default Model**: `gpt-4` or `gpt-3.5-turbo`

### Enable MCP Tools

To enable MCP (Model Context Protocol) tools:

1. Go to **Admin Settings** → **External Tools**
2. Click **Add Server**
3. Select **MCP (Streamable HTTP)**
4. Configure:
   - **Name**: Kor'tana MCP
   - **URL**: `http://host.docker.internal:8001`
   - **Authentication**: Bearer token
   - **Token**: Your `KORTANA_API_KEY`

## Available MCP Tools

Once MCP is configured, you'll have access to these tools:

### Memory Tools

**search_memory** - Search Kor'tana's memory
```json
{
  "tool": "search_memory",
  "parameters": {
    "query": "previous conversations about AI",
    "limit": 5
  }
}
```

**store_memory** - Store new information
```json
{
  "tool": "store_memory",
  "parameters": {
    "content": "User prefers concise responses",
    "tags": ["preference", "user_profile"]
  }
}
```

### Goal Management Tools

**list_goals** - View current goals
```json
{
  "tool": "list_goals",
  "parameters": {
    "status": "active"
  }
}
```

**create_goal** - Create new goals
```json
{
  "tool": "create_goal",
  "parameters": {
    "title": "Learn about quantum computing",
    "description": "Research and understand quantum computing concepts",
    "priority": 7
  }
}
```

### Context Tools

**gather_context** - Gather contextual information
```json
{
  "tool": "gather_context",
  "parameters": {
    "query": "machine learning projects",
    "sources": ["memory", "files"]
  }
}
```

## Using Open WebUI with Kor'tana

### Starting a Conversation

1. Click **New Chat** in the sidebar
2. Select the **Kor'tana** model from the dropdown
3. Start chatting!

### Example Interactions

**Simple Query:**
```
You: What can you tell me about my recent projects?
```

**Using Memory:**
```
You: Remember that I prefer Python for data science projects.
[Kor'tana will automatically store this preference]
```

**Creating Goals:**
```
You: Create a goal to research LLM fine-tuning techniques with priority 8.
[Uses MCP create_goal tool]
```

## Architecture

### Request Flow

```
User Input (Browser)
    ↓
Open WebUI (Docker)
    ↓
OpenAI-Compatible API (/api/openai/v1/chat/completions)
    ↓
Kor'tana Orchestrator
    ↓
[Memory Search] → [LLM Processing] → [Response Generation]
    ↓
OpenAI-Format Response
    ↓
Open WebUI Display
```

### MCP Integration

```
LLM (via Open WebUI)
    ↓
MCP Server (Docker)
    ↓
MCP Router (/api/mcp/*)
    ↓
Kor'tana Services (Memory, Goals, Context)
    ↓
Response with Tool Results
```

## API Endpoints

### OpenAI-Compatible Endpoints

- `GET /api/openai/v1/models` - List available models
- `POST /api/openai/v1/chat/completions` - Chat completions (supports streaming)
- `GET /api/openai/v1/health` - Health check

### MCP Endpoints

- `GET /api/mcp/discover` - Discover available tools
- `POST /api/mcp/memory/search` - Search memory
- `POST /api/mcp/memory/store` - Store memory
- `POST /api/mcp/goals/list` - List goals
- `POST /api/mcp/goals/create` - Create goal
- `POST /api/mcp/context/gather` - Gather context

## Troubleshooting

### Connection Issues

**Problem**: Open WebUI can't connect to Kor'tana backend

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/health`
2. Check API key matches in `.env` and Open WebUI settings
3. For Docker, ensure using `host.docker.internal` not `localhost`
4. Check logs: `docker logs kortana-open-webui`

### Authentication Errors

**Problem**: "Invalid API key" errors

**Solution**:
1. Verify `KORTANA_API_KEY` is set in `.env`
2. Restart the backend after changing `.env`
3. Update the API key in Open WebUI settings
4. Check logs for authentication attempts

### MCP Tools Not Available

**Problem**: MCP tools don't appear in Open WebUI

**Solution**:
1. Verify MCP server is running: `docker ps | grep mcp`
2. Check MCP configuration: `cat config/mcp/mcp_config.json`
3. Restart MCP server: `docker compose -f docker-compose.openwebui.yml restart mcp-server`
4. Verify MCP endpoint: `curl http://localhost:8001/api/mcp/discover`

### Streaming Issues

**Problem**: Responses don't stream, appear all at once

**Solution**:
1. Enable streaming in Open WebUI chat settings
2. Check network tab for proper SSE connection
3. Verify CORS headers allow streaming

## Advanced Configuration

### Custom Models

To add custom models, edit `src/kortana/adapters/openwebui_adapter.py`:

```python
models = [
    OpenAIModel(id="custom-model-name", created=int(time.time())),
    # Add more models...
]
```

### Memory Configuration

Configure memory behavior in `config/memory_config.json`:

```json
{
  "search_limit": 5,
  "relevance_threshold": 0.7,
  "auto_store": true
}
```

### MCP Server Configuration

Customize MCP tools in `config/mcp/mcp_config.json`:

```json
{
  "servers": [
    {
      "id": "custom-tool",
      "name": "Custom Tool",
      "url": "http://host.docker.internal:8000/api/custom",
      ...
    }
  ]
}
```

## Security Considerations

1. **API Keys**: Never commit `.env` files. Use strong, unique keys.
2. **Network**: In production, use HTTPS and proper authentication
3. **CORS**: Restrict `allow_origins` to specific domains
4. **Rate Limiting**: Implement rate limiting for production use
5. **Token Validation**: Ensure all MCP endpoints verify tokens

## Performance Optimization

1. **Caching**: Enable response caching for repeated queries
2. **Connection Pooling**: Configure database connection pooling
3. **Streaming**: Use streaming for long responses
4. **Memory Limits**: Set appropriate limits for memory searches

## Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Open WebUI health
curl http://localhost:3000/health

# MCP server health
curl http://localhost:8001/health
```

### Logs

```bash
# Backend logs (if using uvicorn)
tail -f uvicorn.log

# Open WebUI logs
docker logs -f kortana-open-webui

# MCP server logs
docker logs -f kortana-mcp-server
```

## Comparison with LobeChat

| Feature | Open WebUI | LobeChat |
|---------|-----------|----------|
| Self-hosted | ✅ Yes | ✅ Yes |
| MCP Support | ✅ Native | ⚠️ Limited |
| OpenAI API | ✅ Full | ✅ Full |
| UI Customization | ✅✅ Extensive | ✅ Moderate |
| Tool Integration | ✅✅ Advanced | ⚠️ Basic |
| Mobile Support | ✅ Responsive | ✅ Responsive |

## Next Steps

1. **Customize UI**: Modify Open WebUI theme and branding
2. **Add Tools**: Create custom MCP tools for specific workflows
3. **Integration**: Connect additional data sources
4. **Automation**: Set up automated goal processing
5. **Analytics**: Implement usage tracking and analytics

## Support

For issues or questions:
- Check the logs first
- Review Kor'tana documentation in `/docs`
- Open WebUI docs: https://docs.openwebui.com
- MCP documentation: https://modelcontextprotocol.io

## References

- Open WebUI: https://github.com/open-webui/open-webui
- Model Context Protocol: https://modelcontextprotocol.io
- Kor'tana Architecture: `docs/ARCHITECTURE.md`
