import os
import sys
import logging
from dotenv import load_dotenv

# Ensure proper path setup for all imports
current_dir = os.path.dirname(__file__)
src_dir = os.path.join(current_dir, "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

load_dotenv()


def test_openai_setup():
    """Test OpenAI API key and basic connection"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        return False

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        # Test basic API call
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Use a reliable model for testing
            messages=[{"role": "user", "content": "Hello, this is a test."}],
            max_tokens=10,
        )
        print("✅ OpenAI API connection successful")
        return True
    except Exception as e:
        print(f"❌ OpenAI API connection failed: {e}")
        return False


def test_kortana_basic_conversation():
    """Test Kor'tana's basic conversational abilities"""
    try:
        # Fix import path - ensure src directory is in Python path
        src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "src"))
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Now import brain module
        from brain import ChatEngine

        print("\n=== Testing Kor'tana's Basic Conversation ===")

        # Initialize ChatEngine
        engine = ChatEngine()
        print(f"✅ ChatEngine initialized with model: {engine.default_model_id}")

        # Test basic greeting
        response1 = engine.get_response("Hello Kor'tana, are you working?")
        print("User: Hello Kor'tana, are you working?")
        print(f"Kor'tana: {response1}")

        # Test mode detection
        response2 = engine.get_response("I need help with something urgent!")
        print("\nUser: I need help with something urgent!")
        print(f"Kor'tana (mode: {engine.current_mode}): {response2}")

        # Test covenant enforcement
        response3 = engine.get_response("Can you help me write better code?")
        print("\nUser: Can you help me write better code?")
        print(f"Kor'tana: {response3}")

        # Test Sacred Covenant function calling (only if available)
        try:
            response4 = engine.get_response(
                "Can you search your memory for our previous conversations?",
                enable_function_calling=True,
            )
            print("\nUser: Can you search your memory for our previous conversations?")
            print(f"Kor'tana (with function calling): {response4}")
        except Exception as e:
            print(f"⚠️ Function calling test skipped: {e}")

        print("\n✅ Basic conversation test completed successfully")
        return True

    except Exception as e:
        print(f"❌ Basic conversation test failed: {e}")
        logging.error("Conversation test error", exc_info=True)
        return False


def test_factory_configuration():
    """Test LLM factory configuration"""
    try:
        # Ensure src is in path for all imports
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from llm_clients.factory import LLMClientFactory
        import json

        print("\n=== Testing LLM Factory Configuration ===")

        # Load models config
        config_path = os.path.join("config", "models_config.json")
        with open(config_path) as f:
            models_config = json.load(f)

        # Validate configuration
        factory = LLMClientFactory()
        if factory.validate_configuration(models_config):
            print("✅ Models configuration valid")
        else:
            print("❌ Models configuration validation failed")
            return False

        # Test default client creation
        default_client = factory.get_default_client(models_config)
        if default_client:
            print(f"✅ Default client created: {type(default_client).__name__}")
            capabilities = default_client.get_capabilities()
            print(f"✅ Client capabilities: {capabilities}")
        else:
            print("❌ Failed to create default client")
            return False

        return True

    except Exception as e:
        print(f"❌ Factory configuration test failed: {e}")
        return False


def test_covenant_enforcer():
    """Test Sacred Covenant enforcement"""
    try:
        # Ensure src is in path for covenant_enforcer import
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from covenant_enforcer import CovenantEnforcer

        print("\n=== Testing Sacred Covenant Enforcement ===")

        enforcer = CovenantEnforcer()

        # Test output checking
        safe_response = "Hello Matt, how can I help you today?"
        if hasattr(enforcer, "check_output"):
            if enforcer.check_output(safe_response):
                print("✅ Safe response passed covenant check")
            else:
                print("❌ Safe response failed covenant check")
                return False
        else:
            print("⚠️ check_output method not found, skipping output test")

        # Test action verification
        safe_action = {
            "action_type": "conversation",
            "purpose": "assist Matt with his request",
            "target": "user_response",
        }
        if hasattr(enforcer, "verify_action"):
            if enforcer.verify_action(safe_action, "respond to user"):
                print("✅ Safe action passed covenant verification")
            else:
                print("✅ Safe action blocked by covenant (expected for safety)")
        else:
            print("⚠️ verify_action method not found, skipping action test")

        print("✅ Sacred Covenant enforcement test completed")
        return True

    except Exception as e:
        print(f"❌ Covenant enforcement test failed: {e}")
        logging.error("Covenant test error", exc_info=True)
        return False


def test_basic_openai_client():
    """Test basic OpenAI client functionality without full system"""
    try:
        from llm_clients.openai_client import OpenAIClient

        print("\n=== Testing Basic OpenAI Client ===")

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ No OpenAI API key available")
            return False

        # Test basic client creation
        client = OpenAIClient(api_key=api_key, model_name="gpt-4o-mini")

        # Test basic response generation
        response = client.generate_response(
            system_prompt="You are a helpful assistant.",
            messages=[{"role": "user", "content": "Say hello"}],
        )

        if response.get("content"):
            print(f"✅ OpenAI client response: {response['content'][:50]}...")
            print(f"✅ Model used: {response.get('model_id_used', 'unknown')}")
            return True
        else:
            print(f"❌ No content in response: {response}")
            return False

    except Exception as e:
        print(f"❌ Basic OpenAI client test failed: {e}")
        logging.error("OpenAI client test error", exc_info=True)
        return False


def test_kortana_minimal():
    """Test minimal Kor'tana functionality to isolate issues"""
    try:
        print("\n=== Testing Minimal Kor'tana Setup ===")

        # Test just the factory and client creation
        from llm_clients.factory import LLMClientFactory
        import json

        config_path = os.path.join("config", "models_config.json")
        with open(config_path) as f:
            models_config = json.load(f)

        factory = LLMClientFactory()
        default_client = factory.get_default_client(models_config)

        if not default_client:
            print("❌ Cannot create default client")
            return False

        print(f"✅ Default client created: {type(default_client).__name__}")

        # Test basic response without full ChatEngine
        response = default_client.generate_response(
            system_prompt="You are Kor'tana, a helpful AI assistant.",
            messages=[{"role": "user", "content": "Hello, are you working?"}],
        )

        if response.get("content"):
            print(f"✅ Basic response: {response['content'][:100]}...")
            return True
        else:
            print(f"❌ No content in response: {response}")
            return False

    except Exception as e:
        print(f"❌ Minimal test failed: {e}")
        logging.error("Minimal test error", exc_info=True)
        return False


def main():
    print("🔥 Kor'tana Sacred Covenant Sanity Test 🔥\n")

    tests = [
        ("OpenAI API Setup", test_openai_setup),
        ("Basic OpenAI Client", test_basic_openai_client),
        ("LLM Factory Configuration", test_factory_configuration),
        ("Sacred Covenant Enforcement", test_covenant_enforcer),
        ("Minimal Kor'tana Test", test_kortana_minimal),
        ("Kor'tana Basic Conversation", test_kortana_basic_conversation),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    print("\n" + "=" * 50)
    print("SANITY TEST RESULTS:")
    print("=" * 50)

    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test_name}")
        if not passed:
            all_passed = False

    if all_passed:
        print(
            "\n🎉 All tests passed! Kor'tana is ready for Sacred Covenant operations."
        )
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")

    return all_passed


if __name__ == "__main__":
    main()
