"""
Comprehensive Kor'tana Integration Test
Tests memory manager + vector store + environment loading
"""
import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_environment_loading():
    """Test environment variable loading with dotenv."""
    print("🔧 Environment Loading Test")    print("=" * 40)

    try:
        from dotenv import load_dotenv
        load_dotenv(override=True)  # Force override existing environment variables

        # Test key variables
        test_vars = {
            'OPENAI_API_KEY': 'OpenAI API',
            'GOOGLE_API_KEY': 'Google API',
            'KORTANA_USER_NAME': 'User Name',
            'MEMORY_DB_URL': 'Memory DB'
        }

        results = {}
        for var, desc in test_vars.items():
            value = os.getenv(var)
            if value:
                if 'placeholder' in value.lower() or 'your-api-key-here' in value:
                    results[var] = f"⚠️ Placeholder: {desc}"
                else:
                    masked = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
                    results[var] = f"✅ Valid: {masked}"
            else:
                results[var] = f"❌ Missing: {desc}"

        for var, status in results.items():
            print(f"  {var}: {status}")

        # Check if we have at least one valid API key
        valid_keys = sum(1 for status in results.values() if "✅ Valid" in status)
        print(f"\n📊 Summary: {valid_keys}/{len(test_vars)} variables properly configured")

        return valid_keys > 0

    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False

def test_memory_system():
    """Test the core memory management system."""
    print("\n💾 Memory System Test")
    print("=" * 40)

    try:
        from memory_manager import MemoryManager

        # Initialize with test file
        mm = MemoryManager("data/test_integration_memory.jsonl")
        print("✅ Memory manager initialized")

        # Store test memories
        test_data = [
            ("user", "Matt is building Kor'tana as an autonomous AI companion", {"type": "project_info", "user": "Matt"}),
            ("system", "Kor'tana uses Gemini 2.0 Flash for core reasoning", {"type": "technical", "component": "llm"}),
            ("assistant", "I understand Matt's vision for autonomous AI development", {"type": "understanding"}),
            ("user", "The project emphasizes clean code and minimal interfaces", {"type": "preferences", "user": "Matt"}),
            ("system", "Memory system stores both conversations and project context", {"type": "technical", "component": "memory"})
        ]

        stored_memories = []
        for role, content, metadata in test_data:
            result = mm.store_memory(role, content, metadata)
            stored_memories.append(result)
            print(f"✅ Stored: {result['id'][:16]}... [{role}]")

        # Test retrieval methods
        all_memories = mm.retrieve_memories(limit=10)
        user_memories = mm.retrieve_memories(role="user", limit=5)
        technical_memories = mm.retrieve_memories(metadata_filter={"type": "technical"}, limit=5)
        matt_memories = mm.retrieve_memories(metadata_filter={"user": "Matt"}, limit=5)

        print(f"\n📊 Retrieval Results:")
        print(f"  Total memories: {len(all_memories)}")
        print(f"  User memories: {len(user_memories)}")
        print(f"  Technical memories: {len(technical_memories)}")
        print(f"  Matt-specific: {len(matt_memories)}")

        # Verify persistence
        if os.path.exists(mm.memory_file):
            with open(mm.memory_file, 'r') as f:
                lines = f.readlines()
            print(f"  Persisted entries: {len(lines)}")

        return len(stored_memories) == len(test_data)

    except Exception as e:
        print(f"❌ Memory system test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_vector_store():
    """Test vector store functionality if available."""
    print("\n🔍 Vector Store Test")
    print("=" * 40)

    try:
        from vector_store import VectorStore, VECTOR_DEPS_AVAILABLE

        if not VECTOR_DEPS_AVAILABLE:
            print("⚠️ Vector dependencies not available")
            print("  Run: pip install chromadb sentence-transformers")
            return False

        vs = VectorStore(collection_name="test_integration")
        print("✅ Vector store initialized")

        # Test adding memories
        test_memories = [
            ("mem1", "Matt wants to build an autonomous AI agent called Kor'tana"),
            ("mem2", "Kor'tana should be a sacred companion with evolving intelligence"),
            ("mem3", "The project uses Python, VS Code, and multiple LLM providers"),
            ("mem4", "Memory system includes both local storage and vector search"),
            ("mem5", "Clean code and minimal interfaces are important to Matt")
        ]

        added_count = 0
        for mem_id, content in test_memories:
            success = vs.add_memory(mem_id, content)
            if success:
                added_count += 1
                print(f"✅ Added: {mem_id}")
            else:
                print(f"❌ Failed: {mem_id}")

        # Test search functionality
        search_results = vs.search_memories("autonomous AI agent", limit=3)
        print(f"\n🔍 Search for 'autonomous AI agent': {len(search_results)} results")

        for i, result in enumerate(search_results[:2]):
            print(f"  {i+1}. {result.get('content', 'N/A')[:60]}...")

        # Get collection stats
        stats = vs.get_collection_stats()
        print(f"\n📊 Collection Stats: {stats}")

        return added_count > 0

    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_workflow():
    """Test the integrated memory + vector workflow."""
    print("\n🔄 Integrated Workflow Test")
    print("=" * 40)

    try:
        from memory_manager import MemoryManager
        from vector_store import VectorStore, VECTOR_DEPS_AVAILABLE

        if not VECTOR_DEPS_AVAILABLE:
            print("⚠️ Skipping integration test - vector store not available")
            return True  # Not a failure, just not available

        # Initialize both systems
        mm = MemoryManager("data/integration_workflow.jsonl")
        vs = VectorStore(collection_name="integration_test")

        print("✅ Both systems initialized")

        # Test workflow: store in memory, add to vector store
        workflow_memory = mm.store_memory(
            "user",
            "Testing integrated workflow with memory persistence and vector search",
            {"workflow": "integration", "test": True}
        )

        vector_success = vs.add_memory(
            workflow_memory['id'],
            workflow_memory['content']
        )

        print(f"✅ Workflow test: Memory stored and vector indexed")

        # Test retrieval from both systems
        memory_results = mm.retrieve_memories(metadata_filter={"workflow": "integration"})
        vector_results = vs.search_memories("integrated workflow", limit=3)

        print(f"📊 Workflow Results:")
        print(f"  Memory system: {len(memory_results)} matches")
        print(f"  Vector search: {len(vector_results)} matches")

        return len(memory_results) > 0 and len(vector_results) > 0

    except Exception as e:
        print(f"❌ Integrated workflow test failed: {e}")
        return False

def main():
    """Run comprehensive integration tests."""
    print("🚀 Kor'tana Comprehensive Integration Test")
    print("=" * 70)
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    # Run all tests
    tests = [
        ("Environment Loading", test_environment_loading),
        ("Memory System", test_memory_system),
        ("Vector Store", test_vector_store),
        ("Integrated Workflow", test_integrated_workflow)
    ]

    results = {}
    for test_name, test_func in tests:
        print(f"\n{'='*70}")
        results[test_name] = test_func()

    # Final summary
    print("\n" + "="*70)
    print("📊 INTEGRATION TEST SUMMARY")
    print("="*70)

    passed = 0
    total = len(tests)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {test_name:.<30} {status}")
        if result:
            passed += 1

    print(f"\n🎯 Overall Score: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Kor'tana integration is ready!")
        print("\n🚀 READY FOR PRODUCTION:")
        print("  ✅ Memory system operational")
        print("  ✅ Vector search functional")
        print("  ✅ Environment configured")
        print("  ✅ Integration workflow tested")

        print("\n🔧 RECOMMENDED ACTIONS:")
        print("  1. Update any placeholder API keys in .env")
        print("  2. Connect memory system to brain.py")
        print("  3. Test end-to-end Kor'tana functionality")
        print("  4. Deploy and begin autonomous operations")

    elif passed >= total * 0.75:
        print("\n✅ MOSTLY READY! Minor issues to address:")
        failed_tests = [name for name, result in results.items() if not result]
        for test in failed_tests:
            print(f"  🔧 Fix: {test}")

    else:
        print("\n⚠️ SIGNIFICANT ISSUES DETECTED:")
        print("  Check failed tests above and resolve before proceeding.")

    # Next steps based on results
    if results.get("Environment Loading", False):
        if not results.get("Vector Store", False):
            print("\n💡 TIP: Vector store failed but environment is good.")
            print("     Try: pip install --upgrade chromadb sentence-transformers")

    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
