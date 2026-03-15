"""Test LLM clients directly"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
load_dotenv()

print("=" * 80)
print("TESTING LLM CONFIGURATION")
print("=" * 80)

print("\n1. Environment Variables:")
print(f"   OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:30]}...")
print(f"   OPENROUTER_API_KEY: {os.getenv('OPENROUTER_API_KEY', 'NOT SET')[:30]}...")
print(f"   LLM_MODEL: {os.getenv('LLM_MODEL', 'NOT SET')}")

print("\n2. Loading Kortana config...")
try:
    from kortana.config import load_config
    config_path = Path(__file__).parent / "kortana.yaml"
    settings = load_config(str(config_path))
    print(f"   ✅ Config loaded")
    print(f"   default_llm_id: {settings.default_llm_id}")
except Exception as e:
    print(f"   ❌ Config error: {e}")
    sys.exit(1)

print("\n3. Creating LLM client...")
try:
    from kortana.llm_clients.factory import LLMClientFactory
    factory = LLMClientFactory(settings)
    client = factory.get_client(settings.default_llm_id)
    
    if client:
        print(f"   ✅ Client created: {type(client).__name__}")
    else:
        print(f"   ❌ Client is None!")
        sys.exit(1)
except Exception as e:
    print(f"   ❌ Factory error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing LLM request...")
try:
    import asyncio
    
    async def test_request():
        response = await client.complete({
            "role": "user",
            "content": "Say 'hello' in one word"
        })
        return response
    
    result = asyncio.run(test_request())
    print(f"   ✅ SUCCESS!")
    print(f"   Response: {result.get('content', 'NO CONTENT')}")
    
except Exception as e:
    print(f"   ❌ LLM request failed: {e}")
    import traceback
    traceback.print_exc()
    
    # Try to understand the error
    if "401" in str(e) or "unauthorized" in str(e).lower():
        print("\n   → API key issue - check if keys are valid")
    elif "404" in str(e) or "not found" in str(e).lower():
        print("\n   → Model not found - check model name")
    elif "rate" in str(e).lower():
        print("\n   → Rate limit hit")

print("\n" + "=" * 80)
