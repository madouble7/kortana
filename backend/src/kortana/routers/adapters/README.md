# Frontend Adapters

This directory contains adapter implementations that provide compatibility with various frontend frameworks and AI chat interfaces.

## Overview

The adapters enable Kor'tana to integrate seamlessly with popular AI frontend frameworks by providing API compatibility layers. Each adapter translates requests from its respective frontend format into Kor'tana's internal format and vice versa.

## Available Adapters

### 1. AutoGen Adapter (`autogen_adapter.py`)

**Purpose**: Multi-agent workflow compatibility for AutoGen-based frontends

**Base Path**: `/api/adapters/autogen`

**Features**:
- Multi-agent conversation orchestration
- Agent creation and management
- Group chat sessions
- Compatible with Microsoft's AutoGen framework

**Key Endpoints**:
- `POST /conversation` - Start multi-agent conversation
- `POST /agent/create` - Create new agent
- `GET /agents/list` - List available agents
- `POST /group-chat` - Initiate group chat

**Example Usage**:
```bash
curl -X POST http://localhost:8000/api/adapters/autogen/conversation \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze this code and suggest improvements",
    "agents": ["coder", "reviewer"],
    "max_rounds": 5
  }'
```

### 2. CopilotKit Adapter (`copilotkit_adapter.py`)

**Purpose**: CopilotKit-compatible API with frontend actions and tools support

**Base Path**: `/api/adapters/copilotkit`

**Features**:
- Frontend actions triggering
- Real-time WebSocket communication
- Tool registration and management
- Context-aware responses

**Key Endpoints**:
- `POST /chat` - Handle chat requests with actions
- `WebSocket /ws` - Real-time streaming
- `POST /actions/register` - Register frontend action
- `POST /tools/register` - Register frontend tool
- `GET /config` - Get configuration

**Example Usage**:
```bash
curl -X POST http://localhost:8000/api/adapters/copilotkit/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Help me write a function"}],
    "actions": [{"name": "insert_code", "description": "Insert code into editor"}]
  }'
```

**WebSocket Example**:
```javascript
const ws = new WebSocket('ws://localhost:8000/api/adapters/copilotkit/ws');
ws.onopen = () => {
  ws.send(JSON.stringify({ message: "Hello Kortana" }));
};
```

### 3. Open WebUI Adapter (`openwebui_adapter.py`)

**Purpose**: Open WebUI compatibility with MCP (Model Context Protocol) support

**Base Path**: `/api/adapters/openwebui`

**Features**:
- OpenAI-compatible chat completions
- Streaming responses
- MCP tool integration
- Model listing and management

**Key Endpoints**:
- `POST /chat/completions` - Chat completions (streaming supported)
- `GET /models` - List available models
- `POST /mcp/tools/register` - Register MCP tool
- `GET /mcp/tools/list` - List MCP tools
- `GET /health` - Health check

**Example Usage**:
```bash
curl -X POST http://localhost:8000/api/adapters/openwebui/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-ai",
    "messages": [{"role": "user", "content": "Explain MCP protocol"}],
    "stream": false
  }'
```

**Streaming Example**:
```bash
curl -X POST http://localhost:8000/api/adapters/openwebui/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-ai",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

### 4. LobeChat Adapter (`lobechat_adapter.py`)

**Purpose**: LobeChat integration with full OpenAI API compatibility

**Base Path**: `/api/adapters/lobechat`

**Features**:
- OpenAI v1 API format
- Function calling support
- Plugin integration
- Embeddings support
- Full streaming capability

**Key Endpoints**:
- `POST /v1/chat/completions` - Chat completions
- `GET /v1/models` - List models
- `POST /v1/functions/register` - Register function
- `GET /v1/functions/list` - List functions
- `POST /v1/embeddings` - Create embeddings
- `GET /v1/health` - Health check

**Example Usage**:
```bash
curl -X POST http://localhost:8000/api/adapters/lobechat/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-ai",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant"},
      {"role": "user", "content": "Explain Kor'tana"}
    ],
    "stream": false
  }'
```

**Function Calling Example**:
```bash
curl -X POST http://localhost:8000/api/adapters/lobechat/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-ai",
    "messages": [{"role": "user", "content": "Search for Python tutorials"}],
    "functions": [
      {
        "name": "search_knowledge",
        "description": "Search the knowledge base",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {"type": "string"}
          }
        }
      }
    ]
  }'
```

## Architecture

### Request Flow

```
Frontend → Adapter → Kor'tana Services → AI Provider → Response → Adapter → Frontend
```

### Component Integration

All adapters use Kor'tana's existing services:

- `services.multi_model_ai.ai_service` - Multi-provider AI service
- `services.gemini.gemini_service` - Google Gemini integration
- Backend routers (agents, memory, knowledge, etc.)

### Error Handling

All adapters follow consistent error handling:
- 400: Bad Request (missing/invalid parameters)
- 503: Service Unavailable (AI service not configured)
- 500: Internal Server Error (unexpected errors)

## Configuration

### Environment Variables

No additional environment variables are required. Adapters use existing Kor'tana configuration:

```env
GEMINI_API_KEY=your-key
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
```

### CORS Configuration

Ensure CORS allows your frontend origin in `backend/.env`:

```env
CORS_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:5173
```

## Testing

### Health Checks

Test each adapter's health endpoint:

```bash
# AutoGen adapter
curl http://localhost:8000/api/adapters/autogen/agents/list

# CopilotKit adapter
curl http://localhost:8000/api/adapters/copilotkit/config

# Open WebUI adapter
curl http://localhost:8000/api/adapters/openwebui/health

# LobeChat adapter
curl http://localhost:8000/api/adapters/lobechat/v1/health
```

### Integration Testing

Run the test suite:

```bash
cd backend
pytest tests/test_adapters.py -v
```

## Development

### Adding a New Adapter

1. Create new file in `routers/adapters/your_adapter.py`
2. Define FastAPI router with appropriate endpoints
3. Import in `routers/adapters/__init__.py`
4. Mount in `main.py`
5. Add documentation
6. Add tests

### Adapter Pattern

All adapters follow this pattern:

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class RequestModel(BaseModel):
    # Define request schema
    pass

class ResponseModel(BaseModel):
    # Define response schema
    pass

@router.post("/endpoint")
async def endpoint(request: RequestModel) -> ResponseModel:
    try:
        from services.multi_model_ai import ai_service

        if ai_service is None:
            raise HTTPException(503, "AI service not available")

        # Process request
        result = await ai_service.analyze_text(request.text)

        return {"response": result}
    except Exception as e:
        raise HTTPException(500, str(e))
```

## Deployment

The adapters are automatically included when deploying Kor'tana. No additional deployment steps required.

### Docker

```bash
docker build -t kortana-backend .
docker run -p 8000:8000 kortana-backend
```

### Google Cloud Run

Deployed automatically via GitHub Actions on push to main branch.

## API Documentation

When the backend is running, view complete API documentation at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

Filter by tags:
- `adapters` - All adapter endpoints
- `autogen` - AutoGen-specific
- `copilotkit` - CopilotKit-specific
- `openwebui` - Open WebUI-specific
- `lobechat` - LobeChat-specific

## Troubleshooting

### Adapter Returns 503

**Cause**: AI service not configured

**Solution**: Ensure at least one AI provider API key is set:
```bash
export GEMINI_API_KEY=your-key
# or
export OPENAI_API_KEY=your-key
```

### WebSocket Connection Failed

**Cause**: CORS or proxy configuration

**Solution**:
1. Check CORS_ORIGINS includes your frontend URL
2. Ensure WebSocket connections are allowed through proxy/firewall
3. Use correct WebSocket URL scheme (ws:// or wss://)

### Streaming Not Working

**Cause**: Buffering or incorrect content type

**Solution**:
1. Verify `stream: true` in request
2. Check client supports `text/event-stream`
3. Disable buffering in reverse proxy

## Support

For issues or questions:
- GitHub Issues: [KOR-TANA/kortana/issues](https://github.com/KOR-TANA/kortana/issues)
- Documentation: [docs/](../../docs/)

## License

MIT License - See [LICENSE](../../LICENSE)
