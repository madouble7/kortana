"""
Quick test of OpenAI API key and model availability
"""
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
model = os.getenv("LLM_MODEL", "gpt-5-nano")

print(f"API Key: {api_key[:20]}..." if api_key else "❌ No API key found")
print(f"Model: {model}")
print("\nTesting OpenAI connection...\n")

try:
    from openai import OpenAI
    
    client = OpenAI(api_key=api_key)
    
    # Test with a simple completion
    print(f"Attempting to use model: {model}")
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say 'hello' in one word"}],
        max_tokens=10
    )
    
    print(f"✅ SUCCESS! Response: {response.choices[0].message.content}")
    print(f"\nModel used: {response.model}")
    print(f"Tokens used: {response.usage.total_tokens}")
    
except Exception as e:
    print(f"❌ ERROR: {e}")
    print(f"\nError type: {type(e).__name__}")
    
    # Try listing available models
    print("\n" + "="*60)
    print("Attempting to list available models...")
    print("="*60)
    try:
        models = client.models.list()
        gpt_models = [m.id for m in models.data if 'gpt' in m.id.lower()]
        print(f"\nAvailable GPT models ({len(gpt_models)}):")
        for m in sorted(gpt_models):
            print(f"  - {m}")
    except Exception as list_error:
        print(f"Could not list models: {list_error}")
