# LobeChat Integration - Quick Reference

## 🚀 Quick Start

### Start with Docker Compose
```bash
# 1. Setup environment
cp .env.template .env
# Edit .env and add your API keys

# 2. Start services
docker-compose up -d

# 3. Access LobeChat
# Open http://localhost:3210 in your browser
```

### Configure LobeChat
1. Open LobeChat at http://localhost:3210
2. Click Settings (⚙️) → Language Model
3. Add Custom Provider:
   - **Name**: Kor'tana
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: [from your .env file]
4. Select Model: `kortana-default`

## 📋 API Endpoints

### OpenAI-Compatible Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/models` | GET | List available models |
| `/v1/chat/completions` | POST | Chat completion (main) |
| `/v1/health` | GET | API health check |

### Legacy Endpoints (Backward Compatibility)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/lobe/chat` | POST | Legacy LobeChat adapter |
| `/adapters/lobechat/chat` | POST | Legacy adapter endpoint |

## 🔑 Environment Variables

### Required
```env
KORTANA_API_KEY=your_secure_key_here
OPENAI_API_KEY=sk-...
```

### Optional
```env
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
PINECONE_API_KEY=...
```

## 🧪 Testing

### Test API Endpoint
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer YOUR_KORTANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "kortana-default",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Validate Structure
```bash
python validate_lobechat_integration.py
```

## 📦 Available Models

| Model ID | Description |
|----------|-------------|
| `kortana-default` | Intelligent routing (recommended) |
| `gpt-4o-mini-openai` | OpenAI GPT-4o Mini |
| `gemini-2.0-flash-lite` | Google Gemini 2.0 |

## 🛠️ Useful Commands

### Docker
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f

# Restart a service
docker-compose restart kortana-backend
```

### Manual Backend Start
```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Start server
uvicorn src.kortana.main:app --host 0.0.0.0 --port 8000 --reload
```

## 🐛 Troubleshooting

### Connection Failed
- ✅ Check backend: `curl http://localhost:8000/health`
- ✅ Verify Base URL has `/v1`: `http://localhost:8000/v1`
- ✅ Check API key matches `.env` file

### 401 Unauthorized
- ✅ Set `KORTANA_API_KEY` in `.env`
- ✅ Use correct key in LobeChat
- ✅ No "Bearer" prefix in LobeChat UI

### CORS Errors
- ✅ Check `localhost:3210` in CORS origins
- ✅ Restart backend after changes

## 📖 Documentation

- **Complete Guide**: [docs/LOBECHAT_INTEGRATION_GUIDE.md](docs/LOBECHAT_INTEGRATION_GUIDE.md)
- **Frontend Setup**: [lobechat-frontend/README.md](lobechat-frontend/README.md)
- **API Docs**: http://localhost:8000/docs (when running)
- **Legacy Guide**: [docs/LOBECHAT_CONNECTION.md](docs/LOBECHAT_CONNECTION.md)

## 🔒 Security

1. Never commit `.env` files
2. Use strong API keys in production
3. Configure CORS properly for production
4. Use HTTPS in production
5. Enable rate limiting for production

## 🎯 Features

- ✅ OpenAI-compatible API
- ✅ Multi-model support
- ✅ Memory integration
- ✅ Ethical AI evaluation
- ✅ Docker deployment
- ✅ Easy configuration
- ⏳ Streaming responses (future)
- ⏳ User authentication (future)

## 📞 Support

For issues:
1. Check troubleshooting section
2. Review logs: `docker-compose logs -f`
3. Consult full documentation
4. Test API endpoints directly
