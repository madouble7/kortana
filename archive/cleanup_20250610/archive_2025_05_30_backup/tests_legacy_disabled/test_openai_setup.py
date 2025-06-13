"""
Test OpenAI SDK Setup for Kor'tana
Verify official SDK structure works perfectly
"""

import os

from openai import OpenAI


def test_openai_connection():
    """Test basic OpenAI API connection"""
    print("🔍 Testing OpenAI SDK Connection...")

    try:
        # Initialize client with official SDK structure
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # Test with GPT-4.1-nano
        response = client.chat.completions.create(
            model="gpt-4.1-nano",
            messages=[
                {"role": "user", "content": "Hello, I am Kor'tana. Test my connection."}
            ],
            max_tokens=50,
        )

        print("✅ OpenAI SDK Test Successful!")
        print(f"📊 Model: {response.model}")
        print(f"🗣️  Response: {response.choices[0].message.content}")
        print(f"⚡ Tokens Used: {response.usage.total_tokens}")

        return True

    except Exception as e:
        print(f"❌ OpenAI SDK Test Failed: {e}")
        return False


if __name__ == "__main__":
    print("🚀 TESTING OPENAI SDK SETUP FOR KOR'TANA")
    print("=" * 50)

    success = test_openai_connection()

    if success:
        print("\n🎉 Ready for autonomous development!")
    else:
        print("\n⚠️  Check your API key and connection")
