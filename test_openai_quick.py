"""Quick OpenAI test with current config"""
import os
from dotenv import load_dotenv

load_dotenv()

print("Testing OpenAI API...")
print(f"API Key: {os.getenv('OPENAI_API_KEY', 'NOT FOUND')[:50]}...")
print(f"Model: {os.getenv('LLM_MODEL', 'NOT SET')}\n")

try:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Try the configured model
    model = os.getenv('LLM_MODEL', 'gpt-4o-mini')
    print(f"Testing model: {model}")
    
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": "Say hello"}],
        max_tokens=10
    )
    
    print(f"✅ SUCCESS!\n")
    print(f"Response: {response.choices[0].message.content}")
    print(f"Model used: {response.model}")
    
except Exception as e:
    print(f"❌ ERROR: {e}\n")
    
    # Try common model names
    print("Trying other models...")
    for test_model in ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]:
        try:
            print(f"  Testing {test_model}...", end=" ")
            r = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            print(f"✅ WORKS! (response: {r.choices[0].message.content})")
        except Exception as e2:
            print(f"❌ {str(e2)[:50]}")
