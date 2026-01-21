# Enhanced Chat Interface Documentation

## Overview

The Kor'tana chat interface has been significantly enhanced to provide a rich, modern user experience with full integration of the orchestrator's capabilities including memory search, ethical evaluation, and LLM-powered responses.

## What's New

### 1. Enhanced Chat API (`/chat`)

The `/chat` endpoint now uses the full `KorOrchestrator` capabilities instead of just echoing messages.

**Features:**
- Full memory search integration
- Ethical evaluation of responses
- LLM-powered responses with context awareness
- Conversation tracking via `conversation_id`
- Metadata about model usage and context

**Request:**
```json
{
  "message": "What do you remember about our project goals?",
  "conversation_id": "optional-conversation-id"
}
```

**Response:**
```json
{
  "response": "Based on our conversations, I remember that...",
  "status": "success",
  "conversation_id": "conv_12345",
  "metadata": {
    "model": "gpt-4.1-nano",
    "context_used": true
  }
}
```

### 2. OpenAI-Compatible Adapter (`/v1/chat/completions`)

For compatibility with tools like LobeChat and other OpenAI-compatible clients.

**Features:**
- OpenAI-compatible request/response format
- Full orchestrator integration
- Streaming support (coming soon)

**Request:**
```json
{
  "model": "kortana-custom",
  "messages": [
    {"role": "user", "content": "Hello, Kor'tana"}
  ]
}
```

**Response:**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1234567890,
  "model": "kortana-custom",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I assist you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20,
    "total_tokens": 30
  }
}
```

### 3. Modern Web Chat Interface

A beautiful, responsive web interface available at the root URL (`/`).

**Features:**
- Modern gradient design with smooth animations
- Real-time typing indicators
- Health status monitoring
- Error handling with user-friendly messages
- Auto-scrolling message history
- Keyboard shortcuts (Enter to send)
- Mobile-responsive design

**UI Elements:**
- **Status Indicator**: Shows connection health (green = healthy, yellow = degraded, red = offline)
- **Message Bubbles**: User messages in purple gradient, AI responses in white
- **Typing Indicator**: Animated dots while waiting for response
- **Input Field**: Clean, rounded input with send button

### 4. LobeChat Adapter Enhancement

The `/adapters/lobechat/chat` endpoint now uses the full orchestrator.

**Request:**
```json
{
  "messages": [
    {"role": "user", "content": "Tell me about yourself"}
  ]
}
```

**Response:**
```json
{
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "I am Kor'tana, an AI companion..."
    },
    "finish_reason": "stop",
    "index": 0
  }],
  "model": "kortana-custom",
  "usage": {...}
}
```

## Usage Guide

### Starting the Server

```bash
# From project root
cd /home/runner/work/kortana/kortana

# Start the server
python -m uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload
```

### Accessing the Chat Interface

1. **Web UI**: Open your browser to `http://localhost:8000/`
2. **API Documentation**: Visit `http://localhost:8000/docs` for interactive API docs
3. **Health Check**: `http://localhost:8000/health`

### Using the Web Interface

1. Open `http://localhost:8000/` in your browser
2. Type your message in the input field
3. Press Enter or click Send
4. Watch the status indicator to monitor connection health
5. View responses with metadata (model used, context availability)

### Integration with External Tools

#### LobeChat Integration

1. Configure LobeChat to use `http://localhost:8000/v1` as the base URL
2. The `/v1/chat/completions` endpoint is fully OpenAI-compatible
3. Set any model name - Kor'tana handles routing internally

#### Python Client Example

```python
import requests

def chat_with_kortana(message, conversation_id=None):
    url = "http://localhost:8000/chat"
    payload = {
        "message": message,
        "conversation_id": conversation_id
    }
    response = requests.post(url, json=payload)
    return response.json()

# Example usage
result = chat_with_kortana("Hello, Kor'tana!")
print(result["response"])
```

#### JavaScript/Browser Example

```javascript
async function sendMessage(message) {
  const response = await fetch('/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ message })
  });
  
  const data = await response.json();
  return data.response;
}

// Usage
const reply = await sendMessage("What's the weather like?");
console.log(reply);
```

## Architecture

### Request Flow

```
User Input
    ↓
Chat Endpoint (/chat)
    ↓
Database Session
    ↓
KorOrchestrator.process_query()
    ↓
1. Memory Search (semantic, top 3)
    ↓
2. Prompt Building (with context)
    ↓
3. LLM Client Call
    ↓
4. Ethical Evaluation
    ↓
5. Uncertainty Handling
    ↓
Final Response
    ↓
JSON Response to Client
```

### Components

1. **FastAPI Application** (`main.py`)
   - Routes HTTP requests
   - Manages CORS
   - Serves static files
   - Handles errors

2. **KorOrchestrator** (`orchestrator.py`)
   - Core thinking loop
   - Memory integration
   - LLM communication
   - Response evaluation

3. **Core Router** (`core_router.py`)
   - `/core/query` endpoint
   - `/v1/chat/completions` OpenAI adapter
   - Request/response models

4. **Web Interface** (`static/chat.html`)
   - Modern UI/UX
   - Real-time updates
   - Error handling
   - Health monitoring

## Configuration

### Environment Variables

Required environment variables (in `.env` file):

```env
# Database
MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db

# LLM Providers
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here

# Optional
LOG_LEVEL=INFO
APP_NAME=kortana
```

### Model Configuration

Model routing is configured in `config/models_config.json`:

```json
{
  "models": {
    "gpt-4.1-nano": {
      "provider": "openai",
      "api_key_env": "OPENAI_API_KEY",
      "model_name": "gpt-4"
    }
  },
  "default": {
    "model": "gpt-4.1-nano"
  }
}
```

## Error Handling

### Common Errors

1. **500 Internal Server Error**
   - Check API keys are set
   - Verify database connection
   - Check logs for stack traces

2. **Database Connection Error**
   - Run migrations: `alembic upgrade head`
   - Check `MEMORY_DB_URL` in `.env`

3. **LLM Service Error**
   - Verify API keys are valid
   - Check rate limits
   - Ensure model names are correct

### Error Response Format

```json
{
  "detail": "Error message here",
  "status_code": 500
}
```

## Future Enhancements

### Planned Features

1. **Streaming Responses**
   - Server-Sent Events (SSE) support
   - Real-time token streaming
   - Progressive response display

2. **Conversation Management**
   - Save/load conversations
   - Conversation history
   - Search across conversations

3. **Enhanced Memory Display**
   - Show which memories were used
   - Relevance scores
   - Memory highlights in responses

4. **Advanced UI Features**
   - Markdown rendering
   - Code syntax highlighting
   - Image support
   - Voice input/output

5. **Customization**
   - Theme selection
   - Font size adjustment
   - Layout preferences
   - Persona selection

## Testing

### Manual Testing

1. Start the server
2. Open `http://localhost:8000/`
3. Send various messages
4. Verify responses are contextual
5. Check metadata in responses

### Automated Testing

```bash
# Run basic API tests
python tests/test_chat_api_basic.py

# Run integration tests (requires full setup)
pytest tests/integration/test_chat_engine.py
```

### E2E Testing with Playwright

```bash
# Run end-to-end tests
npx playwright test tests/e2e.spec.ts
```

## Troubleshooting

### UI Not Loading

1. Check static files exist: `ls static/chat.html`
2. Verify static mount in `main.py`
3. Check browser console for errors

### No Response from API

1. Check server logs
2. Verify orchestrator initialization
3. Test with curl:
   ```bash
   curl -X POST http://localhost:8000/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "Hello"}'
   ```

### Memory Not Working

1. Check database connection
2. Verify migrations are up to date
3. Test memory search directly:
   ```python
   from src.kortana.modules.memory_core.services import MemoryCoreService
   service = MemoryCoreService(db)
   results = service.search_memories_semantic("test query", top_k=3)
   ```

## Support and Contributing

For issues, suggestions, or contributions:

1. Check existing documentation
2. Review logs for errors
3. Create detailed bug reports
4. Submit pull requests with tests

## Conclusion

The enhanced chat interface provides a robust, modern foundation for interacting with Kor'tana. With full orchestrator integration, memory capabilities, and a beautiful UI, users can now have rich, context-aware conversations with their AI companion.
