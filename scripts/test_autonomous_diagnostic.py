#!/usr/bin/env python3
"""
Configuration test to diagnose autonomous awakening issues.
"""

import sys
import traceback


def test_config_loading():
    """Test configuration loading step by step."""
    print("🔧 Testing Configuration Loading...")
    print("=" * 50)

    try:
        print("1. Testing basic import...")
        from kortana.config import load_config
        print("✅ Config import successful")

        print("\n2. Testing config loading...")
        config = load_config()
        print(f"✅ Raw config loaded: {type(config)}")
        print(f"   Keys: {list(config.keys()) if isinstance(config, dict) else 'Not a dict'}")

        print("\n3. Testing KortanaConfig creation...")
        from kortana.config.schema import KortanaConfig

        print("✅ KortanaConfig import successful")

        print("\n4. Testing KortanaConfig instantiation...")
        settings = KortanaConfig(**config)
        print("✅ KortanaConfig created successfully")
        print(f"   Default LLM ID: {settings.default_llm_id}")
        print(f"   Has agents config: {hasattr(settings, 'agents')}")
        print(f"   Has paths config: {hasattr(settings, 'paths')}")

        return True, settings

    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False, None

def test_brain_initialization(settings):
    """Test ChatEngine initialization."""
    print("\n🧠 Testing ChatEngine Initialization...")
    print("=" * 50)

    try:
        from kortana.core.brain import ChatEngine
        print("✅ ChatEngine import successful")

        print("\n   Creating ChatEngine instance...")
        chat_engine = ChatEngine(settings=settings)
        print("✅ ChatEngine initialized successfully")

        print(f"   Session ID: {chat_engine.session_id}")
        print(f"   Autonomous mode: {chat_engine.autonomous_mode}")

        return True, chat_engine

    except Exception as e:
        print(f"❌ ChatEngine initialization failed: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        return False, None

def main():
    """Main diagnostic function."""
    print("🚀 AUTONOMOUS AWAKENING DIAGNOSTIC")
    print("=" * 60)

    # Test configuration
    config_success, settings = test_config_loading()

    if not config_success:
        print("\n❌ Configuration loading failed - cannot proceed")
        return 1

    # Test brain initialization
    brain_success, chat_engine = test_brain_initialization(settings)

    if not brain_success:
        print("\n❌ ChatEngine initialization failed")
        return 1

    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 60)
    print("✅ Configuration: READY")
    print("✅ ChatEngine: READY")
    print("✅ Autonomous Systems: READY FOR ACTIVATION")

    # Cleanup
    if chat_engine:
        chat_engine.shutdown()

    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
