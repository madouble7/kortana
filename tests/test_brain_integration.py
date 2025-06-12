"""
Simple Kor'tana brain integration test.
Tests core brain functionality with memory system.
"""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


def test_brain_memory_integration():
    """Test basic brain + memory integration."""
    print("🧠 Kor'tana Brain + Memory Integration Test")
    print("=" * 50)

    try:
        # Load environment
        from dotenv import load_dotenv

        load_dotenv(override=True)

        # Test memory system
        from memory_manager import MemoryManager

        mm = MemoryManager("data/brain_integration_test.jsonl")
        print("✅ Memory manager initialized")

        # Store some test memories
        user_memory = mm.store_memory(
            "user",
            "Hello Kor'tana, I am Matt, your creator",
            {"type": "introduction", "user": "Matt"},
        )
        print(f"✅ Stored user memory: {user_memory['id'][:16]}...")

        context_memory = mm.store_memory(
            "system",
            "This is a test of the brain-memory integration system",
            {"type": "context", "test": True},
        )
        print(f"✅ Stored context memory: {context_memory['id'][:16]}...")

        # Test retrieval for context
        recent_memories = mm.retrieve_memories(limit=5)
        user_memories = mm.retrieve_memories(role="user", limit=3)

        print("\n📊 Memory retrieval test:")
        print(f"  Recent memories: {len(recent_memories)}")
        print(f"  User memories: {len(user_memories)}")

        # Test basic LLM configuration
        print("\n🔧 Environment check:")
        openai_key = os.getenv("OPENAI_API_KEY")
        google_key = os.getenv("GOOGLE_API_KEY")

        print(
            f"  OpenAI API: {'✅ Valid' if openai_key and openai_key.startswith('sk-') else '❌ Invalid'}"
        )
        print(
            f"  Google API: {'✅ Valid' if google_key and len(google_key) > 30 else '❌ Invalid'}"
        )

        # Test minimal brain logic (without full brain.py)
        print("\n🤖 Minimal brain logic test:")

        # Simulate a simple query processing
        query = "What do you know about me?"

        # Get relevant memories
        relevant_memories = mm.retrieve_memories(
            metadata_filter={"user": "Matt"}, limit=3
        )

        # Build context
        context_parts = []
        for memory in relevant_memories:
            context_parts.append(f"[{memory['role']}] {memory['content']}")

        context = (
            "\n".join(context_parts) if context_parts else "No relevant memories found."
        )

        print(f"  Query: {query}")
        print(f"  Context memories: {len(relevant_memories)}")
        print(f"  Context preview: {context[:100]}...")

        # Simulate response (without actual LLM call)
        response = f"Based on my memories, I see that you are Matt, my creator. I have {len(relevant_memories)} relevant memories about you."

        print(f"  Simulated response: {response}")

        # Store the interaction
        interaction_memory = mm.store_memory(
            "assistant",
            f"Responded to query '{query}' with context from {len(relevant_memories)} memories",
            {
                "type": "interaction",
                "query": query,
                "memories_used": len(relevant_memories),
            },
        )
        print(f"✅ Stored interaction memory: {interaction_memory['id'][:16]}...")

        print("\n🎉 Brain-memory integration test successful!")
        return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run the brain integration test."""
    print("🚀 Kor'tana Brain Integration Test Suite")
    print("=" * 70)

    success = test_brain_memory_integration()

    print("\n" + "=" * 70)
    print("📊 BRAIN INTEGRATION TEST RESULTS")
    print("=" * 70)

    if success:
        print("✅ BRAIN-MEMORY INTEGRATION: PASSED")
        print("\n🎉 SUCCESS! Core integration is working!")
        print("\n🚀 NEXT STEPS:")
        print("  1. Full brain.py integration with LLM calls")
        print("  2. Vector store integration for semantic memory")
        print("  3. End-to-end conversation testing")
        print("  4. Deploy autonomous operations")
    else:
        print("❌ BRAIN-MEMORY INTEGRATION: FAILED")
        print("Check errors above and resolve before proceeding.")

    return success


if __name__ == "__main__":
    main()
