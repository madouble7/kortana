# Open WebUI Integration Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                      http://localhost:3000                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Open WebUI (Docker)                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Frontend UI                                              │  │
│  │  - Chat Interface                                         │  │
│  │  - Model Selection                                        │  │
│  │  - Settings & Configuration                              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                    │
│  ┌──────────────────────────┼────────────────────────────────┐ │
│  │  OpenAI Client           │  MCP Client                    │ │
│  └──────────────┬───────────┴───────────┬────────────────────┘ │
└─────────────────┼───────────────────────┼──────────────────────┘
                  │                       │
                  │                       │
                  ▼                       ▼
    ┌─────────────────────────┐   ┌───────────────────────┐
    │  OpenAI-Compatible API  │   │   MCP Server (Docker) │
    │  :8000/api/openai/v1    │   │   :8001               │
    └─────────┬───────────────┘   └───────┬───────────────┘
              │                           │
              └───────────┬───────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Kor'tana Backend (FastAPI)                    │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  API Routers                                              │  │
│  │                                                            │  │
│  │  ┌──────────────────┐  ┌──────────────────┐             │  │
│  │  │ OpenWebUI Adapter│  │   MCP Router     │             │  │
│  │  │                  │  │                  │             │  │
│  │  │ - /models        │  │ - /discover      │             │  │
│  │  │ - /chat/         │  │ - /memory/*      │             │  │
│  │  │   completions    │  │ - /goals/*       │             │  │
│  │  │                  │  │ - /context/*     │             │  │
│  │  └────────┬─────────┘  └────────┬─────────┘             │  │
│  └───────────┼────────────────────┼──────────────────────────┘ │
│              │                    │                             │
│  ┌───────────┼────────────────────┼──────────────────────────┐ │
│  │           ▼                    ▼                           │ │
│  │  ┌────────────────────────────────────────────────────┐  │ │
│  │  │           Kor'tana Orchestrator                     │  │ │
│  │  │                                                      │  │ │
│  │  │  - Query Processing                                 │  │ │
│  │  │  - Context Assembly                                 │  │ │
│  │  │  - Response Generation                              │  │ │
│  │  └──────┬────────────────────────────┬────────────────┘  │ │
│  │         │                            │                   │ │
│  │         ▼                            ▼                   │ │
│  │  ┌────────────────┐         ┌──────────────────┐       │ │
│  │  │ Memory Service │         │  Goal Service    │       │ │
│  │  │                │         │                  │       │ │
│  │  │ - Search       │         │ - List           │       │ │
│  │  │ - Store        │         │ - Create         │       │ │
│  │  │ - Retrieve     │         │ - Update         │       │ │
│  │  └────────┬───────┘         └─────────┬────────┘       │ │
│  └───────────┼───────────────────────────┼────────────────┘ │
│              │                           │                   │
│  ┌───────────┼───────────────────────────┼────────────────┐ │
│  │           ▼                           ▼                 │ │
│  │  ┌─────────────────────────────────────────────────┐  │ │
│  │  │            Database Layer                        │  │ │
│  │  │                                                   │  │ │
│  │  │  ┌──────────────┐    ┌──────────────┐           │  │ │
│  │  │  │   Memory DB  │    │   Goals DB   │           │  │ │
│  │  │  │  (Vector)    │    │  (Relational)│           │  │ │
│  │  │  └──────────────┘    └──────────────┘           │  │ │
│  │  └─────────────────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            External LLM Services                      │  │
│  │                                                        │  │
│  │  • OpenAI (GPT-4, GPT-3.5)                           │  │
│  │  • Anthropic (Claude)                                 │  │
│  │  • Google (Gemini)                                    │  │
│  │  • xAI (Grok)                                         │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## Request Flow Diagrams

### Chat Completion Flow

```
User Message
    │
    ▼
Open WebUI Frontend
    │
    │ POST /api/openai/v1/chat/completions
    │ Headers: Authorization: Bearer <API_KEY>
    │ Body: {model, messages[], stream}
    │
    ▼
OpenWebUI Adapter
    │
    │ 1. Verify API Key
    │ 2. Parse OpenAI format
    │ 3. Extract user query
    │
    ▼
Kor'tana Orchestrator
    │
    ├─► Memory Service
    │   └─► Search relevant memories
    │
    ├─► LLM Service
    │   └─► Generate response
    │
    └─► Response Assembly
        │
        ▼
OpenAI-Format Response
    │
    │ {id, model, choices[], usage}
    │
    ▼
Open WebUI Display
```

### MCP Tool Invocation Flow

```
LLM Decides to Use Tool
    │
    ▼
Open WebUI → MCP Server
    │
    │ POST /api/mcp/memory/search
    │ Headers: Authorization: Bearer <API_KEY>
    │ Body: {tool_name, parameters}
    │
    ▼
MCP Router
    │
    │ 1. Verify Token
    │ 2. Route to Service
    │
    ▼
Service Layer
    │
    ├─► Memory Service
    │   ├─► search_memory(query, limit)
    │   └─► store_memory(content, tags)
    │
    ├─► Goal Service
    │   ├─► list_goals(status)
    │   └─► create_goal(title, desc, priority)
    │
    └─► Context Service
        └─► gather_context(query, sources)
            │
            ▼
MCP Response
    │
    │ {success, result, error}
    │
    ▼
LLM Context
    │
    ▼
Enhanced Response
```

## Component Responsibilities

### Open WebUI (Frontend)
- **Purpose**: User interface for chat interactions
- **Technology**: Docker container (Node.js/React)
- **Key Features**:
  - Chat interface
  - Model selection
  - Settings management
  - MCP tool integration
  - Streaming support

### OpenWebUI Adapter
- **Purpose**: Translate between OpenAI API and Kor'tana
- **Location**: `src/kortana/adapters/openwebui_adapter.py`
- **Responsibilities**:
  - Parse OpenAI-format requests
  - Authenticate requests
  - Transform to Kor'tana format
  - Format responses for OpenAI spec
  - Handle streaming

### MCP Router
- **Purpose**: Expose Kor'tana tools via MCP protocol
- **Location**: `src/kortana/api/routers/mcp_router.py`
- **Responsibilities**:
  - Tool discovery endpoint
  - Memory operations
  - Goal management
  - Context gathering
  - Authentication

### MCP Server (Docker)
- **Purpose**: Bridge between Open WebUI and MCP endpoints
- **Technology**: mcpo (FastAPI proxy)
- **Configuration**: `config/mcp/mcp_config.json`
- **Responsibilities**:
  - HTTP/SSE to MCP translation
  - Request routing
  - Connection management

### Kor'tana Orchestrator
- **Purpose**: Core business logic
- **Location**: `src/kortana/core/orchestrator.py`
- **Responsibilities**:
  - Query processing
  - Memory search
  - LLM interaction
  - Response generation
  - Context assembly

## Data Flow

### Input Processing
```
User Input → OpenAI Format → Internal Format → Orchestrator
```

### Context Gathering
```
Query → Memory Search → LLM Context → Goal Check → Final Context
```

### Response Generation
```
Context + Query → LLM → Raw Response → Format → Validate → Return
```

### Tool Execution
```
LLM Request → MCP Call → Service Layer → Database → Response
```

## Security Architecture

### Authentication Layers

1. **API Key Authentication**
   - All requests require `KORTANA_API_KEY`
   - Bearer token format
   - Validated at router level

2. **Docker Network Isolation**
   - Services communicate via `kortana-network`
   - External access only via exposed ports

3. **CORS Configuration**
   - Configured in FastAPI middleware
   - Allows specific origins only (production)

### Security Flow
```
Request
    │
    ▼
CORS Check
    │
    ▼
API Key Verification
    │
    ▼
Rate Limiting (future)
    │
    ▼
Service Execution
```

## Scalability Considerations

### Horizontal Scaling
```
Load Balancer
    │
    ├─► Backend Instance 1
    ├─► Backend Instance 2
    └─► Backend Instance N
         │
         └─► Shared Database
```

### Caching Strategy
```
Request → Cache Check → [HIT] → Return Cached
                     → [MISS] → Process → Cache → Return
```

### Database Optimization
- Connection pooling
- Index optimization
- Query caching
- Vector search optimization

## Monitoring Points

### Health Checks
- `/health` - Backend health
- `/api/openai/v1/health` - OpenAI API health
- `/api/mcp/discover` - MCP tools health

### Metrics to Monitor
- Request latency
- Token usage
- Error rates
- Memory operations/sec
- Active connections
- Cache hit rate

### Logging Points
- API requests/responses
- Authentication attempts
- MCP tool invocations
- LLM API calls
- Database queries
- Errors and exceptions

## Configuration Files

### Docker Compose
```yaml
docker-compose.openwebui.yml
├── open-webui service
│   ├── Ports: 3000:8080
│   ├── Environment variables
│   └── Volume mounts
├── mcp-server service
│   ├── Ports: 8001:8000
│   ├── Configuration mount
│   └── Data persistence
└── Network: kortana-network
```

### MCP Configuration
```json
config/mcp/mcp_config.json
├── servers[]
│   ├── id, name, description
│   ├── url, authentication
│   └── tools[]
└── settings
    ├── hot_reload
    └── timeout_seconds
```

### Environment Variables
```
.env
├── KORTANA_API_KEY
├── WEBUI_SECRET_KEY
├── OPENAI_API_KEY
├── ANTHROPIC_API_KEY
└── Other LLM keys
```

## Integration Points

### With Existing Kor'tana Systems
- Memory Core (`src/kortana/modules/memory_core/`)
- Goal Engine (`src/kortana/core/goal_engine/`)
- LLM Clients (`src/kortana/llm_clients/`)
- Orchestrator (`src/kortana/core/orchestrator.py`)

### With External Systems
- OpenAI API
- Anthropic API
- Vector databases (Pinecone, Chroma)
- Relational databases (PostgreSQL, SQLite)

## Deployment Scenarios

### Development
```
Local Machine
├── Backend: python -m uvicorn ...
└── Frontend: docker compose up
```

### Production
```
Server/Cloud
├── Backend: gunicorn/uvicorn workers
├── Frontend: docker compose with volumes
├── Reverse Proxy: nginx/traefik
└── SSL/TLS: Let's Encrypt
```

## Future Enhancements

1. **Streaming Improvements**
   - Token-by-token streaming
   - Progress indicators

2. **Additional MCP Tools**
   - File system access
   - Web search
   - Code execution

3. **Performance**
   - Response caching
   - Database optimization
   - CDN for static assets

4. **Features**
   - Multi-user support
   - Role-based access
   - Usage analytics
   - Custom model fine-tuning

## References

- OpenAI API Specification: https://platform.openai.com/docs/api-reference
- MCP Protocol: https://modelcontextprotocol.io
- Open WebUI: https://docs.openwebui.com
- FastAPI: https://fastapi.tiangolo.com
