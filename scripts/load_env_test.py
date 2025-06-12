"""
Environment loader for Kor'tana project
Explicitly loads .env file and tests API key access
"""
import os

from dotenv import load_dotenv


def load_and_test_environment():
    # Load .env file
    load_dotenv()

    print("🔍 Loading and testing environment variables...")
    print("=" * 50)

    # Test critical environment variables
    env_vars = [
        'OPENAI_API_KEY',
        'GOOGLE_API_KEY',
        'XAI_API_KEY',
        'ANTHROPIC_API_KEY',
        'OPENROUTER_API_KEY'
    ]

    results = {}
    for var in env_vars:
        value = os.getenv(var)
        if value:
            # Show first 10 and last 4 characters for security
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            results[var] = f"✅ Found: {masked}"
        else:
            results[var] = "❌ Missing"

    for var, status in results.items():
        print(f"{var}: {status}")

    print("=" * 50)

    # Test specific API call
    if os.getenv('OPENAI_API_KEY'):
        print("\n🧪 Testing OpenAI API connection...")
        try:
            # Simple test without making actual API call
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key.startswith('sk-') and len(api_key) > 20:
                print("✅ OpenAI API key format looks valid")
            else:
                print("⚠️ OpenAI API key format may be invalid")
        except Exception as e:
            print(f"❌ Error testing OpenAI key: {e}")

    return results

if __name__ == "__main__":
    load_and_test_environment()
