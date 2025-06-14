#!/usr/bin/env python3
"""
Test script to verify ChatEngine and Brain alias instantiation with KortanaConfig.
This script tests the complete integration of load_config() returning KortanaConfig
and ChatEngine accepting it properly.
"""

import sys
import traceback
from pathlib import Path

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))


def test_chat_engine_instantiation():
    """Test ChatEngine and Brain alias instantiation with KortanaConfig settings."""
    print("=" * 80)
    print("TESTING CHATENGINE AND BRAIN ALIAS INSTANTIATION")
    print("=" * 80)

    try:
        # Step 1: Test load_config() returns KortanaConfig
        print("\n1. Testing load_config() import and execution...")
        from kortana.config import load_config

        print("   [OK] load_config imported successfully")

        settings = load_config()
        print("   ✓ load_config() executed successfully")
        print(f"   ✓ Returned type: {type(settings)}")
        print(f"   ✓ Type name: {settings.__class__.__name__}")

        # Verify it's actually a KortanaConfig instance
        from kortana.config.schema import KortanaConfig

        if isinstance(settings, KortanaConfig):
            print("   ✓ Confirmed: settings is a KortanaConfig instance")
        else:
            print(
                f"   ✗ ERROR: settings is not a KortanaConfig instance (got {type(settings)})"
            )
            return False

        # Step 2: Test ChatEngine and Brain imports
        print("\n2. Testing ChatEngine and Brain imports...")
        from kortana.core.brain import Brain, ChatEngine

        print("   ✓ ChatEngine imported successfully")
        print("   ✓ Brain alias imported successfully")
        print(f"   ✓ Brain alias points to: {Brain}")
        print(f"   ✓ ChatEngine class: {ChatEngine}")

        # Verify Brain is actually an alias for ChatEngine
        if Brain is ChatEngine:
            print("   ✓ Confirmed: Brain is an alias for ChatEngine")
        else:
            print("   ✗ ERROR: Brain is not an alias for ChatEngine")
            return False

        # Step 3: Test ChatEngine instantiation
        print("\n3. Testing ChatEngine instantiation...")
        try:
            engine = ChatEngine(settings=settings)
            print("   ✓ ChatEngine instantiated successfully")
            print(f"   ✓ Engine type: {type(engine)}")
            print(f"   ✓ Engine session_id: {engine.session_id}")
            print(f"   ✓ Engine settings type: {type(engine.settings)}")
        except Exception as e:
            print(f"   ✗ ERROR during ChatEngine instantiation: {e}")
            print(f"   ✗ Traceback: {traceback.format_exc()}")
            return False

        # Step 4: Test Brain alias instantiation
        print("\n4. Testing Brain alias instantiation...")
        try:
            brain_alias_instance = Brain(settings=settings)
            print("   ✓ Brain alias instantiated successfully")
            print(f"   ✓ Brain instance type: {type(brain_alias_instance)}")
            print(f"   ✓ Brain session_id: {brain_alias_instance.session_id}")
            print(f"   ✓ Brain settings type: {type(brain_alias_instance.settings)}")
        except Exception as e:
            print(f"   ✗ ERROR during Brain alias instantiation: {e}")
            print(f"   ✗ Traceback: {traceback.format_exc()}")
            return False

        # Step 5: Test think method availability
        print("\n5. Testing think method availability...")
        if hasattr(brain_alias_instance, "think"):
            print("   ✓ Brain instance has think method")
            print(f"   ✓ think method: {brain_alias_instance.think}")
        else:
            print("   ✗ ERROR: Brain instance missing think method")
            return False

        if hasattr(engine, "think"):
            print("   ✓ ChatEngine instance has think method")
            print(f"   ✓ think method: {engine.think}")
        else:
            print("   ✗ ERROR: ChatEngine instance missing think method")
            return False

        # Step 6: Test process_message method availability
        print("\n6. Testing process_message method availability...")
        if hasattr(brain_alias_instance, "process_message"):
            print("   ✓ Brain instance has process_message method")
        else:
            print("   ✗ ERROR: Brain instance missing process_message method")
            return False

        if hasattr(engine, "process_message"):
            print("   ✓ ChatEngine instance has process_message method")
        else:
            print("   ✗ ERROR: ChatEngine instance missing process_message method")
            return False

        print("\n" + "=" * 80)
        print(
            "SUCCESS: ChatEngine and Brain alias instantiated successfully with KortanaConfig settings!"
        )
        print("✓ load_config() returns proper KortanaConfig instance")
        print("✓ ChatEngine accepts KortanaConfig settings parameter")
        print("✓ Brain alias works identically to ChatEngine")
        print("✓ Both think() and process_message() methods are available")
        print("✓ All type compatibility issues resolved")
        print("=" * 80)

        return True

    except Exception as e:
        print(f"\n✗ CRITICAL ERROR: {e}")
        print(f"✗ Traceback: {traceback.format_exc()}")
        return False
    finally:
        # Cleanup if instances were created
        try:
            if "engine" in locals():
                engine.shutdown()
                print("\n   ✓ ChatEngine instance cleaned up")
        except Exception:  # Changed bare except to except Exception
            pass
        try:
            if "brain_alias_instance" in locals():
                brain_alias_instance.shutdown()
                print("   ✓ Brain alias instance cleaned up")
        except Exception:  # Changed bare except to except Exception
            pass


if __name__ == "__main__":
    print("CHATENGINE AND BRAIN ALIAS VERIFICATION TEST")
    print(f"Python version: {sys.version}")
    print(f"Python path includes: {src_path}")

    success = test_chat_engine_instantiation()

    if success:
        print("\n🎉 ALL TESTS PASSED - READY FOR BATCH DIRECTIVES! 🎉")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - ISSUES NEED RESOLUTION")
        sys.exit(1)
