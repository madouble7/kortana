import requests
import json

def test_kortana_backend():
    """Test if Kor'tana backend is running and responding"""

    base_url = "http://localhost:8000"

    print("🔍 Testing Kor'tana Backend Connection...")

    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working!")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to Kor'tana backend at http://localhost:8000")
        print("   Make sure to start the server first:")
        print("   cd c:\\project-kortana")
        print("   python src\\kortana\\main.py")
        return False
    except Exception as e:
        print(f"❌ Error testing health endpoint: {e}")
        return False

    # Test LobeChat adapter endpoint
    try:
        test_payload = {
            "messages": [
                {"role": "user", "content": "Hello Kor'tana, testing connection!"}
            ]
        }

        response = requests.post(
            f"{base_url}/adapters/lobechat/chat",
            json=test_payload,
            timeout=10
        )

        if response.status_code == 200:
            print("✅ LobeChat adapter endpoint working!")
            result = response.json()
            print(f"   Response: {result}")
            return True
        else:
            print(f"❌ LobeChat adapter failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing LobeChat adapter: {e}")
        return False

if __name__ == "__main__":
    success = test_kortana_backend()

    if success:
        print("\n🎉 SUCCESS! Kor'tana backend is ready for LobeChat connection!")
        print("\nNext steps:")
        print("1. Start LobeChat frontend:")
        print("   cd c:\\project-kortana\\lobechat-frontend")
        print("   npm run dev")
        print("2. Configure LobeChat to use: http://localhost:8000/adapters/lobechat/chat")
        print("3. Start chatting!")
    else:
        print("\n❌ Backend not ready. Please start Kor'tana backend first.")
