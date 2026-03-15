# Dify Configuration Example for Kor'tana Integration

## Configuration File: dify_config.yaml

This file shows how to configure Dify to work with Kor'tana as a custom model provider.

```yaml
# Dify Configuration for Kor'tana Integration
model_provider:
  name: kortana
  type: custom
  
  # API Configuration
  api:
    base_url: http://localhost:8000/adapters/dify
    authentication:
      type: bearer
      token: your-api-key-here
    
    # Endpoint mappings
    endpoints:
      chat: /chat
      completion: /completion
      workflow: /workflows/run
      
  # Model Configuration
  models:
    - name: kortana-chat
      type: chat
      endpoint: chat
      description: "Kor'tana chat model with memory and ethical reasoning"
      
    - name: kortana-completion
      type: completion
      endpoint: completion
      description: "Kor'tana text completion model"
      
  # Capabilities
  capabilities:
    streaming: false  # Enable in future versions
    function_calling: false  # Enable in future versions
    multi_turn: true
    context_window: 4096
    
  # Performance Settings
  performance:
    timeout: 30  # seconds
    max_retries: 3
    rate_limit:
      requests_per_minute: 60
      
  # Security Settings
  security:
    verify_ssl: true
    allow_self_signed: false  # Only for development
```

## Environment Variables for Dify Integration

Add these to your `.env` file:

```bash
# Dify Platform Integration
DIFY_API_KEY=your-secure-api-key-here
DIFY_APP_ID=app-kortana-integration
DIFY_BASE_URL=http://localhost:8000/adapters/dify
DIFY_REQUIRE_AUTH=true  # Set to false only in development

# Optional: Dify Cloud Configuration
DIFY_CLOUD_ENDPOINT=https://api.dify.ai/v1
DIFY_CLOUD_API_KEY=your-dify-cloud-api-key
```

## Dify Application Configuration

### Chat Application Setup

```json
{
  "app_type": "chat",
  "name": "Kor'tana Assistant",
  "description": "AI assistant powered by Kor'tana with memory and ethical reasoning",
  "model_config": {
    "provider": "kortana",
    "model": "kortana-chat",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2048
  },
  "prompt_config": {
    "system_prompt": "You are Kor'tana, an AI assistant with advanced memory and ethical reasoning capabilities. You provide thoughtful, context-aware responses.",
    "user_prefix": "Human:",
    "assistant_prefix": "Kor'tana:",
    "variables": [
      {
        "name": "context",
        "type": "string",
        "description": "Additional context for the conversation"
      }
    ]
  },
  "conversation_config": {
    "max_history": 10,
    "enable_memory": true
  }
}
```

### Workflow Application Setup

```json
{
  "app_type": "workflow",
  "name": "Kor'tana Workflow",
  "description": "Complex workflows powered by Kor'tana",
  "workflow_config": {
    "nodes": [
      {
        "id": "input",
        "type": "input",
        "config": {
          "variables": ["user_query", "context"]
        }
      },
      {
        "id": "kortana_process",
        "type": "llm",
        "config": {
          "provider": "kortana",
          "model": "kortana-chat",
          "prompt": "{{user_query}}",
          "inputs": {
            "context": "{{context}}"
          }
        }
      },
      {
        "id": "output",
        "type": "output",
        "config": {
          "output": "{{kortana_process.answer}}"
        }
      }
    ],
    "edges": [
      {"source": "input", "target": "kortana_process"},
      {"source": "kortana_process", "target": "output"}
    ]
  }
}
```

## Prompt Templates

### Basic Chat Template

```
System: You are Kor'tana, a sacred AI companion with:
- Advanced memory capabilities
- Ethical reasoning and discernment
- Context-aware response generation

User Context: {{context}}
Conversation History: {{history}}

User Query: {{query}}

Provide a thoughtful, context-aware response that demonstrates your unique capabilities.
```

### Workflow Prompt Template

```
Task: {{task_description}}

Context Variables:
- Priority: {{priority}}
- Domain: {{domain}}
- Expected Output: {{output_format}}

Previous Steps:
{{previous_outputs}}

Process this task using your advanced reasoning capabilities and provide a structured response.
```

## API Integration Examples

### Direct API Call (Python)

```python
import requests
import os

# Configuration
KORTANA_URL = os.getenv('DIFY_BASE_URL', 'http://localhost:8000/adapters/dify')
API_KEY = os.getenv('DIFY_API_KEY', 'your-api-key')

def chat_with_kortana(query, conversation_id=None):
    """Send a chat request to Kor'tana via Dify adapter."""
    response = requests.post(
        f"{KORTANA_URL}/chat",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "query": query,
            "conversation_id": conversation_id or "default",
            "inputs": {}
        }
    )
    return response.json()

# Usage
result = chat_with_kortana("What are your capabilities?")
print(result['answer'])
```

### Workflow Execution (Python)

```python
def execute_workflow(workflow_id, inputs):
    """Execute a Kor'tana workflow."""
    response = requests.post(
        f"{KORTANA_URL}/workflows/run",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        },
        json={
            "workflow_id": workflow_id,
            "inputs": inputs
        }
    )
    return response.json()

# Usage
result = execute_workflow(
    "data_analysis_wf",
    {"query": "Analyze customer feedback", "data_source": "reviews"}
)
print(result['outputs'])
```

## Testing Configuration

### Health Check Script

```bash
#!/bin/bash
# test_dify_integration.sh

echo "Testing Dify integration with Kor'tana..."

# Test health endpoint
echo "1. Testing health endpoint..."
curl -s http://localhost:8000/adapters/dify/health | jq

# Test adapter info
echo "2. Testing adapter info..."
curl -s http://localhost:8000/adapters/dify/info | jq

# Test chat endpoint
echo "3. Testing chat endpoint..."
curl -s -X POST http://localhost:8000/adapters/dify/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer test-key" \
  -d '{
    "query": "Hello, how are you?",
    "conversation_id": "test_001"
  }' | jq

echo "Testing complete!"
```

## Deployment Configuration

### Docker Compose Example

```yaml
version: '3.8'

services:
  kortana:
    image: kortana:latest
    ports:
      - "8000:8000"
    environment:
      - DIFY_API_KEY=${DIFY_API_KEY}
      - DIFY_REQUIRE_AUTH=true
      - MEMORY_DB_URL=sqlite:///./data/kortana_memory.db
    volumes:
      - ./data:/app/data
      - ./config:/app/config
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  dify:
    image: dify/dify:latest
    ports:
      - "3000:3000"
    environment:
      - CUSTOM_MODEL_PROVIDER_KORTANA_URL=http://kortana:8000/adapters/dify
      - CUSTOM_MODEL_PROVIDER_KORTANA_KEY=${DIFY_API_KEY}
    depends_on:
      - kortana
```

### Nginx Reverse Proxy

```nginx
# nginx.conf for Kor'tana + Dify

upstream kortana_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name kortana.example.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kortana.example.com;
    
    ssl_certificate /etc/ssl/certs/kortana.crt;
    ssl_certificate_key /etc/ssl/private/kortana.key;
    
    # Dify adapter endpoints
    location /adapters/dify/ {
        proxy_pass http://kortana_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running requests
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=dify_limit:10m rate=10r/s;
    limit_req zone=dify_limit burst=20 nodelay;
}
```

## Security Best Practices

1. **API Key Management**
   - Use strong, randomly generated API keys
   - Rotate keys regularly (e.g., every 90 days)
   - Store keys in secure secrets management (e.g., AWS Secrets Manager, HashiCorp Vault)

2. **Network Security**
   - Use HTTPS in production
   - Implement IP whitelisting if possible
   - Use VPN or private networks for internal communication

3. **Authentication**
   - Always enable `DIFY_REQUIRE_AUTH=true` in production
   - Implement rate limiting to prevent abuse
   - Log all authentication attempts

4. **Data Protection**
   - Encrypt sensitive data at rest
   - Use encrypted connections for all API calls
   - Implement data retention policies

## Monitoring and Logging

### Logging Configuration

```python
# config/logging_config.py
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detailed': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
        }
    },
    'handlers': {
        'dify_adapter': {
            'class': 'logging.FileHandler',
            'filename': 'logs/dify_adapter.log',
            'formatter': 'detailed'
        }
    },
    'loggers': {
        'kortana.adapters.dify': {
            'handlers': ['dify_adapter'],
            'level': 'INFO'
        }
    }
}
```

### Metrics Collection

```python
# Example metrics to track
METRICS = {
    'requests_total': 'Total number of requests',
    'requests_success': 'Number of successful requests',
    'requests_failed': 'Number of failed requests',
    'response_time_avg': 'Average response time',
    'response_time_p95': '95th percentile response time',
    'active_conversations': 'Number of active conversations'
}
```

## Troubleshooting

See the main documentation at `docs/DIFY_INTEGRATION.md` for detailed troubleshooting steps.

## Support

For issues or questions:
- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: `docs/DIFY_INTEGRATION.md`
- Email: support@example.com
