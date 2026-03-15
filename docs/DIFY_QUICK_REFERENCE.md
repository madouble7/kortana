# Dify Integration - Quick Reference Card

## 🚀 Quick Start (5 Minutes)

### 1. Configure Environment
```bash
# Edit .env file
DIFY_API_KEY=your-secret-key-here
DIFY_REQUIRE_AUTH=false  # Set to true in production
```

### 2. Start Server
```bash
# From repository root
python -m uvicorn src.kortana.main:app --reload --port 8000
```

### 3. Test Connection
```bash
curl http://localhost:8000/adapters/dify/health
# Should return: {"status": "healthy", ...}
```

## 📡 API Endpoints

### Chat Endpoint
```bash
POST /adapters/dify/chat
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "query": "Hello, Kor'tana!",
  "conversation_id": "conv_123"
}
```

### Workflow Endpoint
```bash
POST /adapters/dify/workflows/run
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "workflow_id": "wf_789",
  "inputs": {"query": "Process this data"}
}
```

### Completion Endpoint
```bash
POST /adapters/dify/completion
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "prompt": "Complete this code: def hello():"
}
```

### Info Endpoint
```bash
GET /adapters/dify/info
# Returns adapter capabilities
```

### Health Check
```bash
GET /adapters/dify/health
# Returns operational status
```

## 🔐 Security Configuration

### Development Mode (Testing)
```bash
DIFY_REQUIRE_AUTH=false
# No authentication required - for testing only
```

### Production Mode (Secure)
```bash
DIFY_REQUIRE_AUTH=true
DIFY_API_KEY=<strong-random-key>
# All requests must include: Authorization: Bearer <key>
```

## 🛠️ Configuration Files

```
.env                          # Environment variables
├─ DIFY_API_KEY              # Your secret key
├─ DIFY_APP_ID               # Application ID
├─ DIFY_BASE_URL             # API base URL
└─ DIFY_REQUIRE_AUTH         # Security toggle

docs/
├─ DIFY_INTEGRATION.md       # Full guide
├─ DIFY_INTEGRATION_SUMMARY.md  # Implementation details
└─ DIFY_ARCHITECTURE_DIAGRAM.md # Visual diagrams

config/
└─ dify_config_example.md    # Configuration templates
```

## ⚡ Common Use Cases

### 1. Simple Chat
```python
import requests

response = requests.post(
    "http://localhost:8000/adapters/dify/chat",
    headers={"Authorization": "Bearer your-key"},
    json={"query": "What can you do?"}
)
print(response.json()["answer"])
```

### 2. Multi-turn Conversation
```python
conversation_id = "user_session_123"

# First message
response1 = requests.post(
    "http://localhost:8000/adapters/dify/chat",
    json={
        "query": "Remember this number: 42",
        "conversation_id": conversation_id
    }
)

# Follow-up message
response2 = requests.post(
    "http://localhost:8000/adapters/dify/chat",
    json={
        "query": "What number did I tell you?",
        "conversation_id": conversation_id
    }
)
```

### 3. Workflow Execution
```python
response = requests.post(
    "http://localhost:8000/adapters/dify/workflows/run",
    headers={"Authorization": "Bearer your-key"},
    json={
        "workflow_id": "data_analysis",
        "inputs": {
            "query": "Analyze customer feedback",
            "data_source": "recent_reviews"
        }
    }
)
print(response.json()["status"])
```

## 🐛 Troubleshooting

### Problem: Connection Refused
**Solution:** Ensure server is running
```bash
curl http://localhost:8000/health
```

### Problem: 401 Unauthorized
**Solution:** Check API key configuration
```bash
# In .env file:
DIFY_API_KEY=your-correct-key
DIFY_REQUIRE_AUTH=true

# In request:
Authorization: Bearer your-correct-key
```

### Problem: Slow Responses
**Solution:** Check database and enable async operations
```bash
# Monitor logs for bottlenecks
# Consider connection pooling
# Optimize memory search queries
```

### Problem: Import Errors
**Solution:** Install dependencies
```bash
pip install fastapi uvicorn pydantic sqlalchemy
```

## 📚 Documentation Links

- **Full Guide**: `docs/DIFY_INTEGRATION.md`
- **Examples**: `config/dify_config_example.md`
- **Architecture**: `docs/DIFY_ARCHITECTURE_DIAGRAM.md`
- **Summary**: `docs/DIFY_INTEGRATION_SUMMARY.md`
- **API Docs**: http://localhost:8000/docs (when server running)

## ✅ Verification Checklist

Before deployment:
- [ ] Environment variables configured
- [ ] API key set (production)
- [ ] Server starts without errors
- [ ] Health endpoint responds
- [ ] Chat endpoint works
- [ ] Authentication enforced (production)
- [ ] HTTPS configured (production)
- [ ] Logs monitored
- [ ] Backup configured

## 🎯 Key Features

✓ **No-code prompts** - Visual prompt designer compatible
✓ **Workflows** - Multi-step automation support
✓ **Chat interface** - Full conversation handling
✓ **Memory integration** - Context-aware responses
✓ **Security** - API key authentication
✓ **Scalability** - Horizontal scaling ready
✓ **Documentation** - 40KB+ guides

## 🔗 Useful Commands

```bash
# Start server
python -m uvicorn src.kortana.main:app --reload

# Run tests
python tests/test_dify_verification.py

# Check health
curl http://localhost:8000/adapters/dify/health

# View API docs
# Open browser: http://localhost:8000/docs

# View logs
tail -f logs/kortana.log  # If logging configured
```

## 📞 Support

- **GitHub Issues**: Report bugs and feature requests
- **Documentation**: See `docs/` directory
- **Code**: `src/kortana/adapters/dify_*.py`

## 🎓 Learning Path

1. **Start here**: Read `docs/DIFY_INTEGRATION.md`
2. **Understand architecture**: Review `docs/DIFY_ARCHITECTURE_DIAGRAM.md`
3. **Try examples**: Use code samples in `config/dify_config_example.md`
4. **Test locally**: Run verification tests
5. **Deploy**: Follow production security guidelines
6. **Integrate**: Connect your Dify application

---

**Version**: 1.0.0  
**Status**: Production Ready ✅  
**Last Updated**: January 22, 2026
