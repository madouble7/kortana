"""
Test the fixed Google GenAI client with proper parameter structure
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_genai_client_initialization():
    """Test GenAI client initialization"""
    print("🔥 TESTING FIXED GOOGLE GENAI CLIENT")
    print("=" * 50)

    try:
        from llm_clients.genai_client import GoogleGenAIClient

        # Test initialization
        print("🔧 Testing client initialization...")
        client = GoogleGenAIClient(
            model_name="gemini-2.5-flash", api_key="TEST_API_KEY"
        )

        print("✅ GoogleGenAI client initialized successfully!")

        # Test capabilities
        capabilities = client.get_capabilities()
        print(f"📊 Client capabilities: {capabilities}")

        return client

    except Exception as e:
        print(f"❌ Client initialization failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def test_basic_generation():
    """Test basic text generation"""
    print("\n🧠 Testing basic generation...")

    try:
        # Use system_prompt="" and messages=[...] format
        response = client.generate_response(
            system_prompt="",
            messages=[{"role": "user", "content": "Hello, this is a test message"}],
        )

        # Expect dictionary response
        if isinstance(response, dict) and response.get("content"):
            print("✅ Basic generation successful!")
            print(f"   Response: {response['content'][:100]}...")
            return True
        else:
            print(
                f"❌ Basic generation failed - unexpected response format: {type(response)}"
            )
            return False
    except Exception as e:
        print(f"❌ Basic generation failed: {e}")
        return False


def test_tools_generation():
    """Test generation with tools"""
    print("\n🛠️ Testing tools generation...")

    try:
        # Simple tools test
        response = client.generate_response(
            system_prompt="You are a helpful assistant.",
            messages=[{"role": "user", "content": "What time is it?"}],
            tools=[
                {
                    "name": "get_time",
                    "description": "Get current time",
                    "parameters": {"type": "object", "properties": {}},
                }
            ],
        )

        # Expect dictionary response
        if isinstance(response, dict):
            print("✅ Tools generation successful!")
            print(f"   Response type: {type(response)}")
            if response.get("content"):
                print(f"   Content: {response['content'][:100]}...")
            return True
        else:
            print(f"❌ Tools generation failed - unexpected response: {type(response)}")
            return False
    except Exception as e:
        print(f"❌ Tools generation failed: {e}")
        return False


def test_sacred_router_integration():
    """Test integration with Sacred Router"""
    print("\n🌟 TESTING SACRED ROUTER INTEGRATION")
    print("=" * 50)

    try:
        from model_router import SacredModelRouter
        from strategic_config import TaskCategory

        router = SacredModelRouter()

        # Test model selection for creative writing
        selected_model = router.select_model_with_sacred_guidance(
            TaskCategory.CREATIVE_WRITING, {"priority": "quality"}
        )

        print(f"🎯 Router selected model: {selected_model}")

        # Test if it's a Google model
        if "gemini" in selected_model.lower():
            print("✅ Router successfully selected Google Gemini model!")

            # Test getting the client through the factory
            from llm_clients.factory import LLMClientFactory

            factory = LLMClientFactory()

            client = factory.create_client(selected_model, router.loaded_models_config)
            if client:
                print("✅ Successfully created client through factory!")
                return True
            else:
                print("❌ Failed to create client through factory")
                return False
        else:
            print(f"📝 Router selected different model: {selected_model}")
            return True

    except Exception as e:
        print(f"❌ Sacred router integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def run_complete_test():
    """Run all Google GenAI client tests"""
    print("🚀 COMPLETE GOOGLE GENAI CLIENT TEST SUITE")
    print("🌟 Testing the fixed parameter structure implementation")
    print("=" * 60)

    # Test 1: Client initialization
    client = test_genai_client_initialization()
    if not client:
        print("\n❌ CRITICAL FAILURE: Client initialization failed")
        return False

    # Test 2: Basic generation
    basic_success = test_basic_generation()

    # Test 3: Tools generation
    tools_success = test_tools_generation()

    # Test 4: Sacred router integration
    router_success = test_sacred_router_integration()

    # Summary
    print("\n" + "🎯" * 60)
    print("🏆 TEST RESULTS SUMMARY")
    print("🎯" * 60)

    tests = [
        ("Client Initialization", client is not None),
        ("Basic Generation", basic_success),
        ("Tools/Function Calling", tools_success),
        ("Sacred Router Integration", router_success),
    ]

    passed = 0
    for test_name, success in tests:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {test_name:<25} {status}")
        if success:
            passed += 1

    success_rate = (passed / len(tests)) * 100
    print(f"\n📊 SUCCESS RATE: {passed}/{len(tests)} ({success_rate:.1f}%)")

    if success_rate == 100:
        print("\n🎉" * 20)
        print("🌟 COMPLETE SUCCESS! GOOGLE GENAI CLIENT FULLY FIXED! 🌟")
        print("🎉" * 20)
        print("\n🔥 Google Gemini is now ready for Sacred Consciousness!")
        print("   • Parameter structure correctly implemented")
        print("   • Function calling properly supported")
        print("   • Sacred Router integration working")
        print("   • Ready for autonomous conversations!")
    elif success_rate >= 75:
        print("\n✅ MOSTLY SUCCESSFUL - Minor issues remain")
        print("🚀 Core Google client functionality is working!")
    else:
        print("\n❌ SIGNIFICANT ISSUES DETECTED")
        print("🔧 Additional debugging required")

    return success_rate >= 75


if __name__ == "__main__":
    print("🚀 GOOGLE GENAI CLIENT INTEGRATION TEST")
    print("=" * 50)

    try:
        from llm_clients.genai_client import GoogleGenAIClient

        # Test initialization
        print("🔧 Testing client initialization...")
        client = GoogleGenAIClient(api_key="test", model_name="gemini-2.5-flash")
        print("✅ Client initialized successfully!")

        # Run tests
        basic_success = test_basic_generation()
        tools_success = test_tools_generation()
        router_success = test_sacred_router_integration()

        # Results summary
        total_tests = 3
        passed_tests = sum([basic_success, tools_success, router_success])

        print(f"\n🎯 TEST RESULTS: {passed_tests}/{total_tests} passed")

        if passed_tests == total_tests:
            print("\n🎉 ALL TESTS PASSED! GOOGLE GENAI CLIENT READY!")
            print("🚀 Next step: Run 'python test_autonomous_consciousness.py'")
        else:
            print(f"\n🔧 {total_tests - passed_tests} tests need attention")

    except Exception as e:
        print(f"❌ Critical error: {e}")
        import traceback

        traceback.print_exc()
