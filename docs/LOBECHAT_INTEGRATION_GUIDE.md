# LobeChat Integration Setup Guide

This guide provides step-by-step instructions for integrating LobeChat as the primary AI-driven frontend for Kor'tana.

## Architecture Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│   LobeChat UI   │────────▶│  Kor'tana API    │────────▶│   AI Services   │
│  (Port 3210)    │         │  (Port 8000)     │         │  (OpenAI, etc)  │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                            │
        │                            │
        ▼                            ▼
  User Interface          ┌──────────────────┐
                         │  Memory & DB      │
                         │  (Vector Store)   │
                         └──────────────────┘
```

## Quick Start

### Option 1: Docker Compose (Recommended)

1. **Set up environment variables**:
   ```bash
   cp .env.template .env
   # Edit .env and add your API keys
   ```

2. **Start both services**:
   ```bash
   docker-compose up -d
   ```

3. **Access LobeChat**:
   - Open your browser to http://localhost:3210
   - Configure the custom API endpoint (see Configuration section below)

### Option 2: Manual Setup

#### Backend Setup

1. **Install dependencies**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your API keys
   ```

3. **Start the backend**:
   ```bash
   uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload
   ```

#### Frontend Setup

1. **Using Docker**:
   ```bash
   docker run -d -p 3210:3210 \
     -e OPENAI_API_KEY=not_required \
     lobehub/lobe-chat:latest
   ```

2. **Or using npm** (requires Node.js 18+):
   ```bash
   cd lobechat-frontend
   npm install
   npm run dev
   ```

## Configuring LobeChat to Use Kor'tana

### Step 1: Open LobeChat Settings

1. Navigate to http://localhost:3210
2. Click the **Settings** icon (⚙️) in the bottom left
3. Select **Language Model** from the settings menu

### Step 2: Add Custom Provider

1. Click **Add Custom Provider**
2. Fill in the following details:

   **Provider Configuration:**
   - **Provider Name**: `Kor'tana`
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: `<your-kortana-api-key>` (from `.env` file)
   
   ⚠️ **Important**: The `/v1` path is required as it's the OpenAI-compatible endpoint

3. Click **Test Connection** to verify
4. Click **Save** to add the provider

### Step 3: Configure Model

1. In the **Model** dropdown, select **Custom Model**
2. Enter one of the following model IDs:
   - `kortana-default` (Recommended - uses Kor'tana's intelligent routing)
   - `gpt-4o-mini-openai` (Direct OpenAI access through Kor'tana)
   - `gemini-2.0-flash-lite` (Google's Gemini model through Kor'tana)

### Step 4: Customize System Prompt (Optional)

Set a custom system prompt to leverage Kor'tana's capabilities:

```
You are Kor'tana, a highly autonomous AI agent and sacred companion with 
advanced memory capabilities and ethical discernment. You have access to 
your memory system to provide context-aware responses, and you operate with 
a deep commitment to wisdom, compassion, and truth. Respond thoughtfully 
and reflectively, maintaining your unique personality while prioritizing 
the user's well-being.
```

## API Endpoints

Kor'tana provides OpenAI-compatible endpoints that LobeChat can use:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completion (main endpoint) |
| `/v1/health` | GET | Health check for the API |
| `/health` | GET | Overall system health |
| `/docs` | GET | Interactive API documentation |

## Features

### Memory Integration
- Kor'tana automatically searches its memory for relevant context
- Previous conversations are retrieved to provide continuity
- Context is seamlessly integrated into responses

### Multi-Model Support
- Intelligent routing between multiple AI providers
- Automatic fallback if primary model is unavailable
- Performance tracking and optimization

### Ethical Discernment
- Responses are evaluated for ethical considerations
- Algorithmic arrogance detection
- Uncertainty handling and transparent communication

### Security
- API key authentication
- CORS configuration for secure cross-origin requests
- Rate limiting (can be configured)

## Troubleshooting

### Connection Issues

**Problem**: LobeChat can't connect to Kor'tana
- ✅ Verify backend is running: `curl http://localhost:8000/health`
- ✅ Check the Base URL includes `/v1`: `http://localhost:8000/v1`
- ✅ Verify API key matches the one in `.env`
- ✅ Check CORS settings allow localhost:3210

### Authentication Errors

**Problem**: 401 Unauthorized
- ✅ Ensure `KORTANA_API_KEY` is set in `.env`
- ✅ Use the correct key in LobeChat settings
- ✅ Format: No "Bearer" prefix needed in LobeChat UI

### Response Issues

**Problem**: No response or error messages
- ✅ Check backend logs: `docker-compose logs kortana-backend`
- ✅ Verify LLM API keys (OpenAI, etc.) are valid
- ✅ Test the orchestrator directly: `curl -X POST http://localhost:8000/v1/chat/completions -H "Authorization: Bearer YOUR_KEY" -H "Content-Type: application/json" -d '{"model":"kortana-default","messages":[{"role":"user","content":"Hello"}]}'`

### Docker Issues

**Problem**: Containers won't start
- ✅ Check Docker is running: `docker ps`
- ✅ View logs: `docker-compose logs`
- ✅ Rebuild: `docker-compose build --no-cache`
- ✅ Remove and recreate: `docker-compose down -v && docker-compose up -d`

## Advanced Configuration

### Custom Models

Add custom models by editing `/v1/models` endpoint in `src/kortana/adapters/lobechat_openai_adapter.py`:

```python
ModelInfo(
    id="my-custom-model",
    object="model",
    created=int(time.time()),
    owned_by="kortana"
)
```

### Token Counting Accuracy

The current implementation uses a simplified token estimation (word count × 1.3). For production deployments requiring accurate token counting:

1. **Install tiktoken** (optional dependency):
   ```bash
   pip install tiktoken
   ```

2. **Update the token counting logic** in `lobechat_openai_adapter.py`:
   ```python
   import tiktoken
   
   # In create_chat_completion function:
   encoding = tiktoken.encoding_for_model("gpt-4")
   prompt_tokens = sum(len(encoding.encode(msg.content)) for msg in request.messages)
   completion_tokens = len(encoding.encode(response_content))
   ```

3. Or accept the approximation for non-billing use cases where exact counts aren't critical.

### Environment Variables

Key environment variables for LobeChat integration:

```env
# Kor'tana API
KORTANA_API_KEY=your_secure_key_here

# AI Service Keys
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...

# LobeChat Configuration
LOBECHAT_FRONTEND_URL=http://localhost:3210
LOBECHAT_BACKEND_URL=http://localhost:8000

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:3210,http://localhost:8080
```

### Streaming Support

To enable streaming responses (future enhancement):
1. Set `stream: true` in chat completion requests
2. Backend will need to implement SSE (Server-Sent Events)
3. Current implementation returns complete responses

## Development

### Testing the API

Test the OpenAI-compatible endpoint:

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KORTANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-default",
    "messages": [
      {"role": "system", "content": "You are Kor'\''tana, a helpful AI assistant."},
      {"role": "user", "content": "What can you help me with?"}
    ]
  }'
```

### Viewing API Documentation

Access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Security Best Practices

1. **Never commit `.env` files** - They contain sensitive API keys
2. **Use strong API keys** - Generate random, complex keys for production
3. **Configure CORS properly** - Restrict origins in production
4. **Enable rate limiting** - Prevent abuse of your API
5. **Use HTTPS** - In production, always use SSL/TLS
6. **Regular updates** - Keep dependencies updated for security patches

## Performance Optimization

1. **Database Connection Pooling**: Configure in `services/database.py`
2. **Caching**: Enable Redis for response caching (future enhancement)
3. **Load Balancing**: Use nginx for multiple backend instances
4. **CDN**: Serve LobeChat static files via CDN in production

## Next Steps

- [ ] Set up monitoring and logging
- [ ] Configure backup for conversation history
- [ ] Implement streaming responses
- [ ] Add user authentication
- [ ] Set up production deployment
- [ ] Configure SSL certificates
- [ ] Implement rate limiting
- [ ] Add analytics and usage tracking

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review backend logs: `docker-compose logs -f kortana-backend`
3. Check LobeChat logs: `docker-compose logs -f lobechat-frontend`
4. Consult the API documentation: http://localhost:8000/docs

## Resources

- [LobeChat Documentation](https://lobehub.com/docs)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- Kor'tana Architecture: `docs/ARCHITECTURE.md`
