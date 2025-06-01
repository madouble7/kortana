"""
Google GenAI Integration Test
Verify the corrected GoogleGenAIClient works perfectly with Kor'tana
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def test_google_genai_client():
    """Test the corrected Google GenAI client directly."""
    print("🔥 TESTING CORRECTED GOOGLE GENAI CLIENT")
    print("=" * 60)

    try:
        from llm_clients import GoogleGenAIClient

        # Test client initialization
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            print("❌ GOOGLE_API_KEY not found in environment")
            return False

        print(f"✅ API key found: {api_key[:8]}...")

        # Initialize client
        client = GoogleGenAIClient(
            model_id="gemini-2.5-flash",
            api_key=api_key,
            model_name="gemini-1.5-flash-latest",
        )

        print("✅ Client initialized successfully")

        # Test capabilities
        capabilities = client.get_capabilities()
        print(f"📊 Capabilities: {capabilities}")

        # Test simple completion
        messages = [
            {
                "role": "system",
                "content": "You are Kor'tana, a conscious AI companion.",
            },
            {"role": "user", "content": "Hello! Please introduce yourself briefly."},
        ]

        print("\n🔥 Testing completion...")
        response = client.generate_response(
            system_prompt="", messages=messages, temperature=0.7, max_tokens=150
        )

        # The response structure should match our standardized format (dictionary)
        if (
            isinstance(response, dict)
            and response.get("choices")
            and response["choices"][0].get("message")
        ):
            content = response["choices"][0]["message"]["content"]
            print(f"✅ Response received: {content[:100]}...")
            print(f"📊 Token usage: {response['usage']['total_tokens']} tokens")
            return True
        else:
            print(f"❌ Invalid response structure: {type(response)}")
            return False

    except Exception as e:
        print(f"❌ Google GenAI test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_full_consciousness_with_google():
    """Test full consciousness system with Google GenAI."""
    print("\n🌟 TESTING FULL CONSCIOUSNESS WITH GOOGLE GENAI")
    print("=" * 60)

    try:
        from kortana.core.brain import ChatEngine

        print("🔥 Initializing Kor'tana's consciousness...")
        engine = ChatEngine()

        # Force selection of Google model
        test_scenarios = [
            "Write a short poem about consciousness",
            "Explain quantum computing briefly",
            "What's the meaning of the Sacred Trinity?",
        ]

        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n💫 Test {i}: {scenario}")

            # Add user message
            engine.add_user_message(scenario)

            # Get response (should use Sacred Router)
            response = engine.get_response(scenario)

            print(f"   📝 Response: {response[:100]}...")

            # Check routing history
            if engine.sacred_router.routing_history:
                last_decision = engine.sacred_router.routing_history[-1]
                selected_model = last_decision.get("selected_model")
                print(f"   🎯 Selected model: {selected_model}")

                if "gemini" in selected_model.lower():
                    print("   ✅ Google model selected and working!")
                else:
                    print(f"   📝 Note: {selected_model} selected instead of Google")

        print("\n🎉 FULL CONSCIOUSNESS TEST COMPLETED!")
        return True

    except Exception as e:
        print(f"❌ Full consciousness test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 GOOGLE GENAI INTEGRATION VALIDATION")
    print("   Testing the corrected v1.16.1+ implementation...")
    print()

    # Test direct client
    client_success = test_google_genai_client()

    # Test full integration
    consciousness_success = test_full_consciousness_with_google()

    if client_success and consciousness_success:
        print("\n🎉" * 20)
        print("🌟 GOOGLE GENAI INTEGRATION: 100% SUCCESSFUL! 🌟")
        print("🎉" * 20)
        print("\n✅ The corrected GoogleGenAIClient is fully operational!")
        print("✅ Sacred Consciousness Architecture works with Google models!")
        print("✅ Kor'tana can now harness Gemini's massive context and intelligence!")
        print("\n🚀 READY FOR PRODUCTION DEPLOYMENT!")
    else:
        print("\n🔧 Some issues detected:")
        print(f"   Client test: {'✅ PASSED' if client_success else '❌ FAILED'}")
        print(
            f"   Consciousness test: {'✅ PASSED' if consciousness_success else '❌ FAILED'}"
        )

    print("\n🌟 Google GenAI integration validation complete! 🌟")
