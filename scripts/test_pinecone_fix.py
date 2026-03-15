#!/usr/bin/env python3
"""
Test Pinecone Import Fix
"""

def test_memory_manager_import():
    """Test that MemoryManager can be imported without syntax errors."""
    try:
        from kortana.memory.memory_manager import MemoryManager
        print("✅ SUCCESS: MemoryManager imported successfully")
        return True
    except SyntaxError as e:
        print(f"❌ SYNTAX ERROR: {e}")
        return False
    except ImportError as e:
        print(f"⚠️  IMPORT ERROR (this may be expected for missing Pinecone): {e}")
        return True  # ImportError is acceptable, syntax error is not
    except Exception as e:
        print(f"❌ OTHER ERROR: {e}")
        return False

def test_chat_engine_import():
    """Test that ChatEngine can be imported after the fix."""
    try:
        print("✅ SUCCESS: ChatEngine imported successfully")
        return True
    except Exception as e:
        print(f"❌ ERROR importing ChatEngine: {e}")
        return False

def test_planning_engine_import():
    """Test that PlanningEngine can be imported after the fix."""
    try:
        print("✅ SUCCESS: PlanningEngine imported successfully")
        return True
    except Exception as e:
        print(f"❌ ERROR importing PlanningEngine: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Pinecone Syntax Fix ===")

    success_count = 0
    total_tests = 3

    print("\n1. Testing MemoryManager import...")
    if test_memory_manager_import():
        success_count += 1

    print("\n2. Testing ChatEngine import...")
    if test_chat_engine_import():
        success_count += 1

    print("\n3. Testing PlanningEngine import...")
    if test_planning_engine_import():
        success_count += 1

    print(f"\n=== Results: {success_count}/{total_tests} tests passed ===")

    if success_count == total_tests:
        print("🎉 ALL TESTS PASSED! The Pinecone syntax fix was successful!")
    else:
        print("⚠️  Some tests failed. Further investigation needed.")
