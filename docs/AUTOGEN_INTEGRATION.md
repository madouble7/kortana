# AutoGen Integration Guide

## Overview

Kor'tana now supports integration with Microsoft's AutoGen framework as a frontend option. This integration provides an AutoGen-compatible interface layer that enables AutoGen-based applications to communicate with Kor'tana's backend systems.

### Current Implementation

This initial release provides:
- **AutoGen-Compatible API**: Endpoints that accept and return data in AutoGen's format
- **Seamless Backend Integration**: Translates AutoGen requests to work with Kor'tana's orchestrator
- **Multi-Agent Response Format**: Structures responses in AutoGen's multi-agent format
- **Frontend Flexibility**: Enables AutoGen-based frontends to use Kor'tana without modification

### Architectural Approach

The integration follows an adapter pattern where:
1. AutoGen-formatted requests are received
2. Requests are translated to Kor'tana's internal format
3. Kor'tana's orchestrator processes the request
4. Responses are formatted in AutoGen's expected structure
5. Responses are returned to the AutoGen client

This approach prioritizes:
- **Compatibility**: AutoGen clients work without modification
- **Backend Stability**: Uses Kor'tana's proven orchestrator
- **Minimal Changes**: Follows existing adapter pattern (LobeChat)
- **Future Extensibility**: Architecture supports native AutoGen agents in future releases

## What is AutoGen?

AutoGen is Microsoft's open-source framework for building and orchestrating multi-agent AI systems. It enables:

- **Multi-agent collaboration**: Multiple AI agents working together on tasks
- **Event-driven messaging**: Asynchronous communication between agents
- **Flexible workflows**: Support for complex, multi-step reasoning
- **Model agnostic**: Works with various LLM backends (OpenAI, Anthropic, etc.)
- **Human-in-the-loop**: Seamless human intervention when needed

## Architecture

The AutoGen integration follows Kor'tana's adapter pattern:

```
AutoGen Frontend → AutoGen Adapter → Kor'tana Orchestrator → Response
                        ↓
                 Multi-Agent Coordinator
```

### Components

1. **AutoGenAdapter** (`src/kortana/adapters/autogen_adapter.py`)
   - Handles requests from AutoGen frontend
   - Coordinates multi-agent interactions
   - Integrates with Kor'tana's orchestrator

2. **AutoGen Router** (`src/kortana/adapters/autogen_router.py`)
   - Provides REST API endpoints
   - Request/response validation
   - Error handling

3. **Main Integration** (`src/kortana/main.py`)
   - Router registration
   - CORS configuration
   - Application-level integration

## API Endpoints

### 1. Chat Endpoint

**POST** `/adapters/autogen/chat`

Single or multi-agent conversation endpoint.

#### Request Format

```json
{
  "messages": [
    {
      "role": "user",
      "content": "Hello, can you help me with this task?"
    }
  ],
  "conversation_id": "optional-conversation-id",
  "agent_config": {
    "optional": "configuration"
  }
}
```

#### Response Format

```json
{
  "agent_responses": [
    {
      "agent": "kortana_assistant",
      "role": "assistant",
      "content": "I'd be happy to help! What task would you like assistance with?",
      "metadata": {
        "agent_type": "kortana_orchestrator",
        "capabilities": ["reasoning", "memory", "ethics"]
      }
    }
  ],
  "conversation_id": "conversation-id",
  "status": "success",
  "debug_info": {
    "kortana_internals": {}
  }
}
```

### 2. Multi-Agent Collaboration Endpoint

**POST** `/adapters/autogen/collaborate`

Enable multiple agents to collaborate on complex tasks.

#### Request Format

```json
{
  "task": "Analyze this code and suggest improvements with proper testing strategy",
  "agent_config": {
    "agents": ["planning_agent", "coding_agent", "testing_agent"]
  },
  "max_rounds": 10
}
```

#### Response Format

```json
{
  "collaboration_result": "Here's the comprehensive analysis...",
  "agents_involved": ["planning_agent", "reasoning_agent", "memory_agent"],
  "task": "Analyze this code...",
  "status": "completed",
  "agent_contributions": [
    {
      "agent": "planning_agent",
      "contribution": "Analyzed task structure and created execution plan"
    },
    {
      "agent": "reasoning_agent",
      "contribution": "Applied logical reasoning to the problem"
    }
  ],
  "debug_info": {}
}
```

### 3. Agent Status Endpoint

**GET** `/adapters/autogen/status`

Get status and configuration of available agents.

#### Response Format

```json
{
  "available_agents": ["assistant", "user_proxy"],
  "agent_details": {
    "assistant": {
      "role": "assistant",
      "system_message": "You are a helpful AI assistant powered by Kor'tana."
    }
  },
  "framework": "Microsoft AutoGen",
  "status": "operational"
}
```

### 4. Health Check Endpoint

**GET** `/adapters/autogen/health`

Health check for AutoGen adapter.

#### Response Format

```json
{
  "status": "healthy",
  "adapter": "AutoGen",
  "framework": "Microsoft AutoGen",
  "message": "AutoGen adapter is operational"
}
```

## Configuration

### Environment Variables

Add to your `.env` file:

```env
# AutoGen Configuration
AUTOGEN_ENABLED=true
AUTOGEN_MAX_ROUNDS=10
AUTOGEN_TIMEOUT=300
```

### Agent Configuration

Agents can be configured in the request or through environment variables:

```python
agent_config = {
    "assistant": {
        "role": "assistant",
        "system_message": "You are a helpful AI assistant.",
    },
    "user_proxy": {
        "role": "user_proxy",
        "system_message": "You represent the user.",
    }
}
```

## Usage Examples

### Python Client

```python
import httpx

# Basic chat
async def chat_with_autogen():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/adapters/autogen/chat",
            json={
                "messages": [
                    {"role": "user", "content": "Hello!"}
                ]
            }
        )
        return response.json()

# Multi-agent collaboration
async def collaborate():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/adapters/autogen/collaborate",
            json={
                "task": "Design a Python class for managing user sessions",
                "max_rounds": 5
            }
        )
        return response.json()
```

### JavaScript/TypeScript Client

```javascript
// Basic chat
async function chatWithAutoGen() {
  const response = await fetch('http://localhost:8000/adapters/autogen/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      messages: [
        { role: 'user', content: 'Hello!' }
      ]
    })
  });
  return response.json();
}

// Multi-agent collaboration
async function collaborate() {
  const response = await fetch('http://localhost:8000/adapters/autogen/collaborate', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      task: 'Design a Python class for managing user sessions',
      max_rounds: 5
    })
  });
  return response.json();
}
```

### cURL Examples

```bash
# Chat endpoint
curl -X POST http://localhost:8000/adapters/autogen/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'

# Collaboration endpoint
curl -X POST http://localhost:8000/adapters/autogen/collaborate \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Design a Python class for managing user sessions",
    "max_rounds": 5
  }'

# Status endpoint
curl http://localhost:8000/adapters/autogen/status

# Health check
curl http://localhost:8000/adapters/autogen/health
```

## Security Considerations

### Input Validation

All requests are validated using Pydantic models to ensure:
- Required fields are present
- Data types are correct
- Content is properly sanitized

### Rate Limiting

Consider implementing rate limiting for production deployments:

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

@router.post("/chat", dependencies=[Depends(RateLimiter(times=10, seconds=60))])
async def handle_autogen_chat(...):
    ...
```

### Authentication

For production use, add authentication:

```python
from fastapi import Security
from fastapi.security import HTTPBearer

security = HTTPBearer()

@router.post("/chat")
async def handle_autogen_chat(
    request: AutoGenRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db_sync)
):
    # Verify credentials
    ...
```

## Scalability

### Performance Optimization

1. **Connection Pooling**: Use database connection pooling
2. **Caching**: Implement response caching for repeated queries
3. **Async Processing**: All endpoints use async/await for non-blocking I/O
4. **Load Balancing**: Deploy multiple instances behind a load balancer

### Monitoring

Monitor key metrics:
- Request latency
- Error rates
- Agent response times
- Database query performance

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```
   Solution: Install dependencies with `pip install -e .`
   ```

2. **Database Connection Errors**
   ```
   Solution: Verify database is running and credentials are correct
   ```

3. **AutoGen Module Not Found**
   ```
   Solution: Install pyautogen with `pip install pyautogen`
   ```

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Endpoints

Use the interactive API docs at `http://localhost:8000/docs` to test all endpoints.

## Future Enhancements

The following enhancements are planned for future releases:

1. **Native AutoGen Agents**: Full AutoGen agent orchestration with actual multi-agent collaboration
2. **Agent Marketplace**: Pre-configured specialized agents (coding, planning, testing, etc.)
3. **Streaming Responses**: Support for streaming multi-agent conversations
4. **Visual Workflow Builder**: UI for designing agent workflows
5. **Advanced Memory**: Shared memory across agent conversations
6. **Custom Agent Creation**: API for defining and deploying custom agents
7. **Agent-to-Agent Communication**: Direct communication between AutoGen agents
8. **Workflow Templates**: Pre-built workflows for common multi-agent tasks

### Roadmap to Native AutoGen

The migration path to native AutoGen functionality:

**Phase 1 (Current)**: AutoGen-compatible interface layer
- ✓ API endpoints accepting AutoGen format
- ✓ Response formatting in AutoGen structure
- ✓ Integration with Kor'tana orchestrator

**Phase 2 (Planned)**: Basic AutoGen agent support
- Create native AutoGen agent instances
- Simple agent-to-agent communication
- Basic workflow coordination

**Phase 3 (Future)**: Advanced multi-agent features
- Complex workflow orchestration
- Dynamic agent creation and coordination
- Advanced memory and context sharing
- Full AutoGen framework capabilities

## Support

For issues or questions:
- Check the API documentation at `/docs`
- Review logs in the console
- Consult the main Kor'tana documentation

## References

- [Microsoft AutoGen Documentation](https://microsoft.github.io/autogen/)
- [AutoGen GitHub Repository](https://github.com/microsoft/autogen)
- [Kor'tana Architecture Documentation](./ARCHITECTURE.md)
