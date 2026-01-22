# Multimodal Integration Guide

This guide walks you through integrating Kor'tana's multimodal capabilities into your application.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Quick Start](#quick-start)
3. [Configuration](#configuration)
4. [Integration Steps](#integration-steps)
5. [Testing](#testing)
6. [Production Deployment](#production-deployment)
7. [Troubleshooting](#troubleshooting)

## Prerequisites

Before integrating multimodal capabilities, ensure you have:

- Python 3.11 or higher
- Kor'tana installed and running
- OpenAI API key (for vision and audio features)
- Database configured (for memory integration)

## Quick Start

### 1. Start Kor'tana Server

```bash
cd /path/to/kortana
python -m uvicorn src.kortana.main:app --reload
```

The server will start on `http://localhost:8000`.

### 2. Verify Multimodal Capabilities

```bash
curl http://localhost:8000/multimodal/capabilities
```

You should see a list of supported features.

### 3. Make Your First Multimodal Request

```python
import requests

response = requests.post(
    "http://localhost:8000/multimodal/text",
    json={"text": "Hello, Kor'tana!"}
)

print(response.json())
```

## Configuration

### Environment Variables

Set up the following environment variables:

```bash
# Required for vision capabilities
OPENAI_API_KEY=your_openai_api_key

# Optional: Database URL for memory integration
MEMORY_DB_URL=sqlite:///./kortana_memory.db

# Optional: Model configuration
MODELS_CONFIG_PATH=config/models_config.json
```

### Models Configuration

Create or update `config/models_config.json`:

```json
{
  "models": {
    "gpt-4-vision-preview": {
      "provider": "openai",
      "model_name": "gpt-4-vision-preview",
      "api_key_env": "OPENAI_API_KEY",
      "capabilities": ["text", "image"],
      "default_params": {
        "temperature": 0.7,
        "max_tokens": 2000
      }
    }
  }
}
```

## Integration Steps

### Step 1: Import Required Modules

For Python integration:

```python
from src.kortana.core.multimodal import (
    MultimodalPromptGenerator,
    ContentType,
    SimulationQuery
)
from src.kortana.services.multimodal_service import MultimodalService
```

### Step 2: Initialize Components

```python
from sqlalchemy.orm import Session
from src.kortana.services.database import get_db_sync

# Get database session
db = next(get_db_sync())

# Create multimodal service
service = MultimodalService(db)

# Create prompt generator
generator = MultimodalPromptGenerator()
```

### Step 3: Create and Process Prompts

#### Text Prompt

```python
# Create prompt
prompt = generator.create_text_prompt(
    "Explain quantum computing",
    context={"user": "student"}
)

# Process prompt
response = await service.process_prompt(prompt)
print(response.content)
```

#### Image Prompt

```python
# Create image prompt
prompt = generator.create_image_prompt(
    image_data="https://example.com/chart.png",
    encoding="url",
    caption="Sales data Q4 2024"
)

# Process prompt
response = await service.process_prompt(prompt)
print(response.content)
```

#### Mixed Content Prompt

```python
# Create mixed prompt
prompt = generator.create_mixed_prompt(
    contents=[
        {"type": "text", "data": "Analyze this image and audio:"},
        {"type": "image", "data": "https://example.com/img.jpg", "encoding": "url"},
        {"type": "audio", "data": "https://example.com/audio.mp3", "encoding": "url"}
    ],
    primary_type=ContentType.TEXT,
    instruction="Provide a comprehensive analysis"
)

# Process prompt
response = await service.process_prompt(prompt)
```

### Step 4: Handle Responses

```python
if response.success:
    print(f"Response: {response.content}")
    print(f"Model used: {response.processing_info.get('model_used')}")
    print(f"Tokens: {response.processing_info.get('usage', {})}")
else:
    print(f"Error: {response.error_message}")
```

## REST API Integration

### Using the HTTP API

#### Setup HTTP Client

```python
import requests

BASE_URL = "http://localhost:8000"
```

#### Text Prompt

```python
response = requests.post(
    f"{BASE_URL}/multimodal/text",
    json={"text": "Your query here"}
)
result = response.json()
```

#### Image Analysis

```python
response = requests.post(
    f"{BASE_URL}/multimodal/image",
    json={
        "image_url": "https://example.com/image.jpg",
        "caption": "Image description"
    }
)
result = response.json()
```

#### File Upload

```python
with open("local_file.jpg", "rb") as f:
    response = requests.post(
        f"{BASE_URL}/multimodal/upload",
        files={"file": f},
        data={"content_type": "image", "caption": "My image"}
    )
result = response.json()
```

## Memory Integration

### Enable Memory Context

```python
# Process with memory enabled
response = await service.process_prompt(prompt, use_memory=True)
```

### Store Custom Memory

```python
from src.kortana.memory.memory_manager import MemoryManager

memory_manager = MemoryManager(db)
memory_manager.store_memory(
    content="Important information to remember",
    metadata={"type": "note", "importance": "high"}
)
```

### Search Memories

```python
memories = memory_manager.search_memories("quantum computing", top_k=5)
for memory in memories:
    print(memory)
```

## Testing

### Run Unit Tests

```bash
# Test multimodal models
pytest tests/test_multimodal_models.py -v

# Test processors
pytest tests/test_multimodal_processors.py -v

# Test prompt generator
pytest tests/test_multimodal_prompt_generator.py -v

# Test API
pytest tests/test_multimodal_api.py -v

# Run all multimodal tests
pytest tests/test_multimodal_*.py -v
```

### Manual Testing

Create a test script:

```python
# test_integration.py
import asyncio
import requests

def test_text_endpoint():
    """Test text endpoint."""
    response = requests.post(
        "http://localhost:8000/multimodal/text",
        json={"text": "Hello, Kor'tana!"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    print("✓ Text endpoint working")

def test_capabilities():
    """Test capabilities endpoint."""
    response = requests.get("http://localhost:8000/multimodal/capabilities")
    assert response.status_code == 200
    result = response.json()
    assert "supported_content_types" in result
    print("✓ Capabilities endpoint working")

if __name__ == "__main__":
    test_capabilities()
    test_text_endpoint()
    print("\n✓ All tests passed!")
```

Run the test:

```bash
python test_integration.py
```

## Production Deployment

### Security Considerations

1. **Add Authentication**
   ```python
   from fastapi import Depends, HTTPException
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @router.post("/multimodal/text")
   async def process_text(
       request: TextPromptRequest,
       token: str = Depends(security)
   ):
       # Validate token
       if not validate_token(token):
           raise HTTPException(status_code=401)
       # Process request...
   ```

2. **Rate Limiting**
   ```python
   from slowapi import Limiter
   from slowapi.util import get_remote_address
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/multimodal/text")
   @limiter.limit("10/minute")
   async def process_text(request: Request, ...):
       # Process request...
   ```

3. **Input Validation**
   - Validate file sizes
   - Check file types
   - Sanitize URLs
   - Limit prompt lengths

### Performance Optimization

1. **Use Async Processing**
   ```python
   import asyncio
   
   async def process_batch(prompts):
       tasks = [service.process_prompt(p) for p in prompts]
       return await asyncio.gather(*tasks)
   ```

2. **Enable Caching**
   ```python
   from functools import lru_cache
   
   @lru_cache(maxsize=100)
   def process_cached_prompt(prompt_text):
       # Process and cache results
       pass
   ```

3. **Connection Pooling**
   - Configure database connection pool
   - Use persistent HTTP connections for API calls

### Monitoring

Add logging and monitoring:

```python
import logging

logger = logging.getLogger(__name__)

@router.post("/multimodal/text")
async def process_text(request: TextPromptRequest):
    logger.info(f"Processing text prompt: {request.text[:50]}...")
    start_time = time.time()
    
    try:
        result = await service.process_prompt(prompt)
        duration = time.time() - start_time
        logger.info(f"Processed in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"Error processing prompt: {e}")
        raise
```

## Troubleshooting

### Common Issues

#### 1. "OPENAI_API_KEY not found"

**Solution:** Set the environment variable:
```bash
export OPENAI_API_KEY=your_api_key
```

#### 2. "Models config not found"

**Solution:** Ensure the config file exists:
```bash
ls -la config/models_config.json
```

#### 3. "Database connection failed"

**Solution:** Check database URL:
```bash
echo $MEMORY_DB_URL
# Should output: sqlite:///./kortana_memory.db
```

#### 4. "Import errors"

**Solution:** Ensure Kor'tana is installed:
```bash
pip install -e .
```

#### 5. "Timeout errors"

**Solution:** Increase timeout for long-running operations:
```python
response = requests.post(
    url,
    json=data,
    timeout=60  # 60 seconds
)
```

### Debug Mode

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.kortana.core.multimodal")
logger.setLevel(logging.DEBUG)
```

### Check Service Health

```python
def check_health():
    """Check service health."""
    try:
        # Check API
        response = requests.get("http://localhost:8000/health")
        assert response.status_code == 200
        
        # Check multimodal capabilities
        response = requests.get("http://localhost:8000/multimodal/capabilities")
        assert response.status_code == 200
        
        print("✓ Service is healthy")
        return True
    except Exception as e:
        print(f"✗ Service health check failed: {e}")
        return False
```

## Next Steps

1. Review [Usage Examples](MULTIMODAL_USAGE_EXAMPLES.md) for more code samples
2. Check [API Reference](MULTIMODAL_API_REFERENCE.md) for detailed endpoint documentation
3. Explore [Capabilities Documentation](MULTIMODAL_CAPABILITIES.md) for architecture details
4. Join the community for support and discussions

## Support

If you encounter issues:
1. Check this guide and the troubleshooting section
2. Review the test suite for examples
3. Check server logs for error messages
4. Create an issue on GitHub with details
