# Dify Integration Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         DIFY PLATFORM                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐ │
│  │   Chat Apps      │  │   Workflows      │  │  Agents/Prompts  │ │
│  │  (No-code UI)    │  │  (Automation)    │  │  (Visual Design) │ │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘ │
│           │                     │                     │             │
│           └─────────────────────┴─────────────────────┘             │
│                                 │                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │ HTTP/HTTPS
                                  │ Bearer Token Auth
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    KOR'TANA BACKEND SERVER                           │
│                      (FastAPI Application)                           │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │              /adapters/dify/* Routes                          │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │          Dify Router (dify_router.py)                   │ │  │
│  │  │  • POST /chat       - Chat messages                     │ │  │
│  │  │  • POST /workflows/run - Workflow execution             │ │  │
│  │  │  • POST /completion - Text completion                   │ │  │
│  │  │  • GET /info        - Adapter information               │ │  │
│  │  │  • GET /health      - Health check                      │ │  │
│  │  └──────────────┬──────────────────────────────────────────┘ │  │
│  │                 │ Pydantic Validation                          │  │
│  │                 ▼                                               │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │
│  │  │         Dify Adapter (dify_adapter.py)                  │ │  │
│  │  │  • handle_chat_request()                                │ │  │
│  │  │  • handle_workflow_request()                            │ │  │
│  │  │  • handle_completion_request()                          │ │  │
│  │  │  • Request/Response transformation                      │ │  │
│  │  └──────────────┬──────────────────────────────────────────┘ │  │
│  └─────────────────┼──────────────────────────────────────────────┘  │
│                    │                                                  │
│                    ▼                                                  │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │              KorOrchestrator (Core Logic)                   │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐  │    │
│  │  │   Memory     │  │   Reasoning  │  │     Ethical      │  │    │
│  │  │    System    │  │    Engine    │  │   Discernment    │  │    │
│  │  └──────────────┘  └──────────────┘  └──────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                        DATA FLOW EXAMPLE                             │
└─────────────────────────────────────────────────────────────────────┘

1. User asks question in Dify chat app
   ↓
2. Dify sends POST /adapters/dify/chat
   {
     "query": "What is AI?",
     "conversation_id": "conv_123"
   }
   ↓
3. Dify Router validates request (Pydantic models)
   ↓
4. API key verification (verify_dify_api_key)
   ↓
5. Dify Adapter transforms request
   ↓
6. KorOrchestrator processes:
   - Searches memory for relevant context
   - Generates response using LLM
   - Applies ethical discernment
   ↓
7. Dify Adapter transforms response
   {
     "answer": "AI is...",
     "conversation_id": "conv_123",
     "metadata": {...}
   }
   ↓
8. Response returned to Dify
   ↓
9. User sees response in Dify chat interface

┌─────────────────────────────────────────────────────────────────────┐
│                      SECURITY LAYERS                                 │
└─────────────────────────────────────────────────────────────────────┘

Layer 1: Network (HTTPS, reverse proxy)
         ↓
Layer 2: Authentication (API Key verification)
         ↓
Layer 3: Input Validation (Pydantic models)
         ↓
Layer 4: Business Logic (Adapter + Orchestrator)
         ↓
Layer 5: Data Access (Database sessions)

┌─────────────────────────────────────────────────────────────────────┐
│                   CONFIGURATION HIERARCHY                            │
└─────────────────────────────────────────────────────────────────────┘

.env (Environment Variables)
 ├─ DIFY_API_KEY          → API authentication
 ├─ DIFY_APP_ID           → Application identifier
 ├─ DIFY_BASE_URL         → API endpoint
 └─ DIFY_REQUIRE_AUTH     → Security toggle
                            └─ false (dev) / true (prod)

config/dify_config_example.md
 ├─ YAML configurations
 ├─ Docker Compose setup
 ├─ Nginx configuration
 └─ Monitoring setup

docs/DIFY_INTEGRATION.md
 ├─ Setup instructions
 ├─ API documentation
 ├─ Security guidelines
 └─ Troubleshooting

┌─────────────────────────────────────────────────────────────────────┐
│                   DEPLOYMENT OPTIONS                                 │
└─────────────────────────────────────────────────────────────────────┘

Option 1: Single Server
┌────────────────┐
│  Kor'tana +    │
│  Dify Adapter  │ ← Direct connection
│  (Port 8000)   │
└────────────────┘

Option 2: With Reverse Proxy
┌────────────┐      ┌────────────────┐
│   Nginx    │ ───→ │   Kor'tana     │
│ (Port 80)  │      │  (Port 8000)   │
└────────────┘      └────────────────┘
     ↑
   HTTPS + SSL

Option 3: Distributed
┌────────────┐      ┌──────────────┐      ┌────────────────┐
│    Dify    │ ───→ │ Load Balancer│ ───→ │ Kor'tana       │
│   Cloud    │      │              │      │ Instance 1     │
└────────────┘      │              │ ───→ │ Instance 2     │
                    └──────────────┘      │ Instance N     │
                                          └────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                      KEY BENEFITS                                    │
└─────────────────────────────────────────────────────────────────────┘

For Developers:
✓ No-code prompt engineering
✓ Visual workflow builder
✓ Quick prototyping
✓ Multiple LLM providers

For Users:
✓ Intuitive chat interface
✓ Customizable applications
✓ Workflow automation
✓ Real-time responses

For Operations:
✓ Easy deployment
✓ Horizontal scaling
✓ Monitoring ready
✓ Security built-in

For Kor'tana:
✓ Extended reach
✓ More use cases
✓ Better accessibility
✓ Community growth
```
