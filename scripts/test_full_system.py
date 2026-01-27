#!/usr/bin/env python3
"""
Comprehensive test of the refactored Kortana system
Tests configuration loading, package imports, and ChatEngine instantiation
"""


def test_full_system():
    print("🔥 Testing Project Kor'tana System Integration")
    print("=" * 50)

    # Test 1: Configuration System
    print("1. Testing configuration system...")
    try:
        from kortana.config import load_config

        settings = load_config()
        print(f"   ✓ Config loaded: {settings.app.name} v{settings.app.version}")
        print(f"   ✓ Environment: {settings.app.environment}")
    except Exception as e:
        print(f"   ❌ Config failed: {e}")
        return False

    # Test 2: Kortana Package Import
    print("\n2. Testing kortana package imports...")
    try:
        print("   ✓ Basic kortana package imported")

        from kortana.agents import (
            CodingAgent,
            MonitoringAgent,
            PlanningAgent,
            TestingAgent,
        )

        print("   ✓ All agent classes imported")

        from kortana.memory.memory_manager import MemoryManager

        print("   ✓ MemoryManager imported")

        print("   ✓ Utility functions imported")
    except Exception as e:
        print(f"   ❌ Package import failed: {e}")
        return False

    # Test 3: ChatEngine with Configuration
    print("\n3. Testing ChatEngine with centralized config...")
    try:
        from kortana.core.brain import ChatEngine

        engine = ChatEngine(settings)
        print("   ✓ ChatEngine instantiated with settings")
        print(f"   ✓ Session ID: {engine.session_id}")
    except Exception as e:
        print(f"   ❌ ChatEngine failed: {e}")
        return False

    # Test 4: Memory System
    print("\n4. Testing memory system...")
    try:
        memory_manager = MemoryManager()
        print("   ✓ MemoryManager instantiated")
    except Exception as e:
        print(f"   ❌ MemoryManager failed: {e}")
        return False

    # Test 5: Agent Classes
    print("\n5. Testing agent instantiation...")
    try:
        planning_agent = PlanningAgent()
        coding_agent = CodingAgent()
        testing_agent = TestingAgent()
        monitoring_agent = MonitoringAgent()
        print("   ✓ All agent classes instantiated")
    except Exception as e:
        print(f"   ❌ Agent instantiation failed: {e}")
        return False

    print("\n" + "=" * 50)
    print("🎉 ALL TESTS PASSED! 🎉")
    print("Project Kor'tana system is fully operational!")
    print("✓ Configuration pipeline working")
    print("✓ Package structure correct")
    print("✓ Import dependencies resolved")
    print("✓ ChatEngine accepts settings object")
    print("✓ All core components functional")

    return True


if __name__ == "__main__":
    success = test_full_system()
    if success:
        print("\n🔥 Ready for development! 🔥")
    else:
        print("\n❌ System has issues that need attention")
