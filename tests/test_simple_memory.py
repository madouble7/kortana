"""
Simple memory manager test without complex dependencies.
Tests just the core memory functionality.
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_memory_only():
    """Test only the memory manager without other dependencies."""
    print("🧪 Simple Memory Manager Test")
    print("=" * 50)

    try:
        from memory_manager import MemoryManager

        # Test initialization
        mm = MemoryManager("data/test_memory.jsonl")
        print("✅ Memory manager initialized")

        # Test storing memories
        memory1 = mm.store_memory("user", "Matt likes building AI agents", {"topic": "preferences"})
        print(f"✅ Stored memory 1: {memory1['id']}")

        memory2 = mm.store_memory("system", "Kor'tana uses memory for context", {"topic": "technical"})
        print(f"✅ Stored memory 2: {memory2['id']}")

        memory3 = mm.store_memory("assistant", "I understand the project goals", {"topic": "understanding"})
        print(f"✅ Stored memory 3: {memory3['id']}")

        # Test retrieval
        all_memories = mm.retrieve_memories(limit=10)
        print(f"✅ Retrieved {len(all_memories)} total memories")

        user_memories = mm.retrieve_memories(role="user")
        print(f"✅ Retrieved {len(user_memories)} user memories")

        system_memories = mm.retrieve_memories(role="system")
        print(f"✅ Retrieved {len(system_memories)} system memories")

        # Test metadata filtering
        preference_memories = mm.retrieve_memories(metadata_filter={"topic": "preferences"})
        print(f"✅ Retrieved {len(preference_memories)} preference memories")

        # Display sample memory
        if all_memories:
            latest = all_memories[0]
            print("\n📝 Latest memory:")
            print(f"   ID: {latest['id']}")
            print(f"   Role: {latest['role']}")
            print(f"   Content: {latest['content']}")
            print(f"   Metadata: {latest.get('metadata', {})}")

        # Check memory file
        if os.path.exists(mm.memory_file):
            with open(mm.memory_file) as f:
                lines = f.readlines()
            print(f"\n💾 Memory file: {mm.memory_file}")
            print(f"   Total entries: {len(lines)}")

        print("\n✅ Memory test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_environment():
    """Test environment variable loading."""
    print("\n🔧 Environment Test")
    print("=" * 30)

    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Check key environment variables
        env_vars = ['OPENAI_API_KEY', 'GOOGLE_API_KEY', 'KORTANA_USER_NAME']

        for var in env_vars:
            value = os.getenv(var)
            if value and value != 'placeholder-replace-with-actual-key-here':
                masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
                print(f"   {var}: ✅ {masked}")
            else:
                print(f"   {var}: ❌ Missing or placeholder")

        return True

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def main():
    """Run the simple tests."""
    print("🚀 Kor'tana Simple Test Suite")
    print("=" * 60)

    # Test memory system
    memory_ok = test_memory_only()

    # Test environment
    env_ok = test_environment()

    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS")
    print("=" * 60)

    print(f"Memory System: {'✅ PASSED' if memory_ok else '❌ FAILED'}")
    print(f"Environment:   {'✅ PASSED' if env_ok else '❌ FAILED'}")

    if memory_ok and env_ok:
        print("\n🎉 All core systems are working!")
        print("\n🚀 READY FOR NEXT STEPS:")
        print("  1. Install vector dependencies: pip install chromadb sentence-transformers")
        print("  2. Update API keys in .env if needed")
        print("  3. Test Kor'tana brain integration")
    else:
        print("\n⚠️ Some systems need attention. Check errors above.")

    return memory_ok and env_ok

if __name__ == "__main__":
    main()
