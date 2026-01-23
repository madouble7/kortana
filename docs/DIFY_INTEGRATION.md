# Dify Platform Integration Guide

This guide explains how to integrate Kor'tana with the Dify platform as a frontend option.

## What is Dify?

Dify is an open-source LLM application development platform that provides:
- **No-code prompt engineering** - Design and test prompts without coding
- **Workflow automation** - Build complex AI workflows with visual tools
- **Chat interface generation** - Create custom chat applications quickly
- **Multi-model support** - Switch between different LLM providers easily
- **Agent orchestration** - Build autonomous AI agents with tool integration

## Architecture Overview

The Dify integration follows Kor'tana's adapter pattern:

```
Dify Application → Dify API → Kor'tana Dify Adapter → KorOrchestrator → Backend Models
```

### Key Components

1. **DifyAdapter** (`src/kortana/adapters/dify_adapter.py`)
   - Handles request/response transformation
   - Manages chat, workflow, and completion modes
   - Ensures data security and minimal latency

2. **Dify Router** (`src/kortana/adapters/dify_router.py`)
   - Provides REST API endpoints for Dify
   - Implements authentication and validation
   - Handles errors gracefully

3. **Main Application** (`src/kortana/main.py`)
   - Registers Dify routes with FastAPI
   - Manages CORS and middleware

## Setup Instructions

### Prerequisites

1. Python 3.11+
2. Kor'tana backend running
3. Dify account (optional, for hosted version)

### Step 1: Configure Environment

Add the following to your `.env` file:

```bash
# Dify Platform Integration
DIFY_API_KEY=your-dify-api-key-here
DIFY_APP_ID=your-dify-app-id-here
DIFY_BASE_URL=https://api.dify.ai/v1
DIFY_REQUIRE_AUTH=false  # Set to true in production
```

### Step 2: Start Kor'tana Server

```bash
# Activate your virtual environment
source venv311/bin/activate  # On Windows: venv311\Scripts\activate.bat

# Start the server
python -m uvicorn src.kortana.main:app --reload --port 8000
```

### Step 3: Verify Integration

Check that the Dify adapter is running:

```bash
curl http://localhost:8000/adapters/dify/health
```

Expected response:
```json
{
  "status": "healthy",
  "adapter": "Dify",
  "version": "1.0.0",
  "message": "Dify adapter is operational and ready to process requests"
}
```

## API Endpoints

### 1. Chat Endpoint

**POST** `/adapters/dify/chat`

Process chat messages from Dify applications.

**Request:**
```json
{
  "query": "What is the meaning of life?",
  "conversation_id": "conv_123",
  "user": "user_456",
  "inputs": {"context": "philosophical"}
}
```

**Response:**
```json
{
  "answer": "The meaning of life is a profound question...",
  "conversation_id": "conv_123",
  "metadata": {
    "kortana_internals": {...},
    "processing_timestamp": "2025-01-22T10:30:00Z"
  }
}
```

**Example with curl:**
```bash
curl -X POST http://localhost:8000/adapters/dify/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key" \
  -d '{
    "query": "Hello, Kortana!",
    "conversation_id": "test_001"
  }'
```

### 2. Workflow Endpoint

**POST** `/adapters/dify/workflows/run`

Execute Dify workflows with Kor'tana backend processing.

**Request:**
```json
{
  "workflow_id": "wf_789",
  "inputs": {
    "query": "Analyze customer feedback",
    "data_source": "recent_reviews"
  },
  "user": "analyst_123"
}
```

**Response:**
```json
{
  "workflow_id": "wf_789",
  "status": "completed",
  "outputs": {
    "result": "Analysis complete...",
    "metadata": {...}
  }
}
```

### 3. Completion Endpoint

**POST** `/adapters/dify/completion`

Handle text completion requests from Dify.

**Request:**
```json
{
  "prompt": "Write a function that calculates fibonacci numbers",
  "inputs": {"language": "python"},
  "user": "dev_001"
}
```

**Response:**
```json
{
  "completion": "def fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)",
  "metadata": {
    "model": "kortana",
    "usage": {"total_tokens": 45}
  }
}
```

### 4. Adapter Info Endpoint

**GET** `/adapters/dify/info`

Get information about adapter capabilities.

**Response:**
```json
{
  "name": "DifyAdapter",
  "version": "1.0.0",
  "supported_features": [
    "chat_completion",
    "workflow_automation",
    "text_completion",
    "no_code_prompts",
    "multi_model_support"
  ],
  "security": {
    "data_encryption": true,
    "api_key_required": true,
    "rate_limiting": true
  },
  "capabilities": {
    "minimal_latency": true,
    "customization": true,
    "extensibility": true,
    "scalability": true
  }
}
```

## Configuring Dify to Use Kor'tana

### For Self-Hosted Dify

1. Navigate to your Dify settings
2. Go to **Model Providers** → **Custom**
3. Add a new custom model:
   - **Name:** Kor'tana
   - **API Endpoint:** `http://your-kortana-server:8000/adapters/dify/chat`
   - **API Key:** Your configured DIFY_API_KEY
   - **Model Type:** Chat

### For Dify Cloud

1. Log into your Dify Cloud account
2. Create a new application
3. In application settings, add a custom API:
   - **Endpoint:** Your Kor'tana server URL
   - **Authentication:** Bearer token (your API key)

## Security Considerations

### Production Deployment

For production environments, enable authentication:

```bash
# .env
DIFY_REQUIRE_AUTH=true
```

### API Key Management

- Store API keys securely (use secrets manager in production)
- Rotate keys regularly
- Use different keys for different environments
- Never commit `.env` files to version control

### Data Encryption

All data transmitted between Dify and Kor'tana should use HTTPS in production:

```bash
# Use reverse proxy (nginx/caddy) with SSL certificates
# Or configure uvicorn with SSL:
uvicorn src.kortana.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
# Future enhancement: Add rate limiting middleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
```

## Customization

### Custom Prompt Templates

Dify allows you to create custom prompt templates. These can include:
- System prompts for Kor'tana's personality
- Context variables from memory
- User-specific instructions

### Workflow Nodes

Create complex workflows in Dify that:
- Query multiple Kor'tana endpoints
- Combine results from different sources
- Apply conditional logic based on responses
- Integrate with external tools and APIs

### Response Formatting

Customize how Kor'tana's responses are formatted in Dify:

```python
# In dify_adapter.py, modify the response structure:
dify_response = {
    "answer": final_response,
    "conversation_id": conversation_id,
    "custom_field": "your_value",  # Add custom fields
    "metadata": {...}
}
```

## Monitoring and Debugging

### Check Adapter Status

```bash
# Health check
curl http://localhost:8000/adapters/dify/health

# Adapter information
curl http://localhost:8000/adapters/dify/info
```

### Enable Debug Logging

Set LOG_LEVEL in `.env`:

```bash
LOG_LEVEL=DEBUG
```

### View Logs

The adapter logs all requests and responses:

```python
# Logs appear in console:
# "DifyAdapter received chat request: {...}"
# "DifyAdapter sending response: {...}"
```

## Performance Optimization

### Minimize Latency

1. **Use connection pooling** for database connections
2. **Enable async processing** for I/O operations
3. **Cache frequently accessed data** using Redis or similar
4. **Deploy close to your users** to reduce network latency

### Scalability

1. **Horizontal scaling**: Run multiple Kor'tana instances behind a load balancer
2. **Database optimization**: Use connection pooling and query optimization
3. **Memory management**: Implement memory cleanup for long-running processes
4. **Resource limits**: Set appropriate limits for concurrent requests

## Troubleshooting

### Common Issues

#### 1. "Missing Authorization header" Error

**Solution:** Include the Authorization header in your requests:
```bash
-H "Authorization: Bearer your-api-key"
```

#### 2. Connection Refused

**Solution:** Ensure Kor'tana server is running:
```bash
curl http://localhost:8000/health
```

#### 3. Slow Response Times

**Possible causes:**
- Database queries taking too long
- Memory search inefficient
- External API calls blocking

**Solutions:**
- Optimize database indexes
- Implement vector database for semantic search
- Use async operations for external calls

#### 4. "Internal Server Error"

**Debug steps:**
1. Check server logs for detailed error messages
2. Verify database connection
3. Ensure all required environment variables are set
4. Test with simple requests first

## Examples

### Python Client Example

```python
import requests

def chat_with_kortana(message: str):
    response = requests.post(
        "http://localhost:8000/adapters/dify/chat",
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer your-api-key"
        },
        json={
            "query": message,
            "conversation_id": "demo_session"
        }
    )
    return response.json()

# Usage
result = chat_with_kortana("Tell me about yourself")
print(result["answer"])
```

### JavaScript/Node.js Example

```javascript
async function chatWithKortana(message) {
    const response = await fetch('http://localhost:8000/adapters/dify/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer your-api-key'
        },
        body: JSON.stringify({
            query: message,
            conversation_id: 'demo_session'
        })
    });
    return await response.json();
}

// Usage
chatWithKortana('Hello Kortana!')
    .then(result => console.log(result.answer));
```

## API Documentation

Once the server is running, visit:
- **OpenAPI/Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## Support and Resources

- **Kor'tana Documentation:** See `/docs` directory
- **Dify Documentation:** https://docs.dify.ai
- **GitHub Issues:** Report bugs and feature requests
- **Architecture Guide:** See `docs/ARCHITECTURE.md`

## Future Enhancements

Planned improvements for the Dify integration:

1. **Streaming responses** - Real-time token streaming
2. **Multi-turn conversations** - Better conversation state management
3. **Tool integration** - Support for Dify's tool/function calling
4. **Advanced workflows** - More complex workflow node types
5. **Analytics dashboard** - Usage metrics and insights
6. **WebSocket support** - For real-time bidirectional communication

## Contributing

To contribute to the Dify integration:

1. Review the existing adapter code
2. Follow the established patterns
3. Add tests for new features
4. Update documentation
5. Submit pull requests

## License

This integration follows the same license as the main Kor'tana project (MIT License).
