"""
Interactive Chat Test for Kor'tana
Run this script to test the chat functionality interactively.
"""

import os
import sys
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))


def print_header(text):
    """Print formatted header."""
    print("\n" + "=" * 70)
    print(f"🗣️  {text}")
    print("=" * 70)


def print_section(text):
    """Print formatted section."""
    print(f"\n📌 {text}")
    print("-" * 70)


def test_dev_chat_interface():
    """Test the dev chat interface."""
    print_section("Testing Dev Chat Interface")

    try:
        from dev_chat_simple import KortanaDevChat

        print("Initializing KortanaDevChat...")
        chat = KortanaDevChat()

        # Basic checks
        tests = {
            "Chat engine created": chat.engine is not None,
            "History initialized": isinstance(chat.history, list),
            "Running state set": chat.running is True,
        }

        for test_name, result in tests.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        all_passed = all(tests.values())
        return all_passed

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_chat_engine():
    """Test the core ChatEngine."""
    print_section("Testing Core ChatEngine")

    try:
        from kortana.config import load_config
        from kortana.core.brain import ChatEngine

        print("Loading configuration...")
        settings = load_config()

        print("Initializing ChatEngine...")
        engine = ChatEngine(settings)

        tests = {
            "Engine initialized": engine is not None,
            "Session ID assigned": engine.session_id is not None,
            "Default mode set": engine.mode == "default",
            "Persona data loaded": engine.persona_data is not None,
            "Memory service available": engine.memory_core_service is not None,
            "LLM client available": engine.default_llm_client is not None,
        }

        for test_name, result in tests.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        if engine.session_id:
            print(f"\n  Session ID: {engine.session_id}")

        all_passed = all(tests.values())
        return all_passed

    except Exception as e:
        print(f"  ❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_memory_system():
    """Test memory system integration."""
    print_section("Testing Memory System Integration")

    try:
        from memory_manager import MemoryManager

        print("Initializing MemoryManager...")
        mm = MemoryManager("data/test_chat_interactive.jsonl")

        # Test storing memory
        print("Storing test memory...")
        mem_id = mm.store_memory(
            role="user",
            content="Test message: Hello Kor'tana!",
            metadata={"type": "test_message", "timestamp": datetime.now().isoformat()},
        )

        tests = {
            "Memory stored": mem_id is not None,
            "Memory ID generated": isinstance(mem_id, str) and len(mem_id) > 0,
        }

        # Test retrieving memory
        print("Retrieving memories...")
        memories = mm.retrieve_memories(limit=5)
        tests["Memories retrieved"] = len(memories) > 0

        for test_name, result in tests.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        if memories:
            print(f"\n  Retrieved {len(memories)} memories")
            print(f"  Latest memory: {memories[-1].get('content', 'N/A')[:50]}...")

        all_passed = all(tests.values())
        return all_passed

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_conversation_flow():
    """Test conversation flow."""
    print_section("Testing Conversation Flow")

    try:
        from dev_chat_simple import KortanaDevChat
        from memory_manager import MemoryManager

        print("Setting up conversation test...")
        chat = KortanaDevChat()
        mm = MemoryManager("data/test_chat_conversation.jsonl")

        # Simulate conversation
        conversation = [
            {"role": "user", "content": "Hello Kor'tana, how are you?"},
            {"role": "user", "content": "Can you help me with a project?"},
            {"role": "user", "content": "What's your main capability?"},
        ]

        print(f"Simulating {len(conversation)} message exchange...")

        for i, msg in enumerate(conversation, 1):
            # Store in memory
            mm.store_memory(msg["role"], msg["content"], {"turn": i})

            # Add to chat history
            chat.history.append(
                {
                    "role": msg["role"],
                    "content": msg["content"],
                    "timestamp": datetime.now().isoformat(),
                }
            )

            print(f"  {i}. Stored: {msg['content'][:40]}...")

        tests = {
            "All messages stored in chat": len(chat.history) == len(conversation),
            "Messages retrievable from memory": len(mm.retrieve_memories(limit=10))
            >= len(conversation),
        }

        for test_name, result in tests.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        all_passed = all(tests.values())
        return all_passed

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_session_management():
    """Test session management."""
    print_section("Testing Session Management")

    try:
        from kortana.config import load_config
        from kortana.core.brain import ChatEngine

        print("Creating multiple sessions...")
        settings = load_config()

        session1 = ChatEngine(settings)
        session2 = ChatEngine(settings)

        tests = {
            "Different session IDs": session1.session_id != session2.session_id,
            "Session1 ID exists": session1.session_id is not None,
            "Session2 ID exists": session2.session_id is not None,
        }

        # Test custom session ID
        custom_id = "test-chat-session-001"
        session3 = ChatEngine(settings, session_id=custom_id)
        tests["Custom session ID accepted"] = session3.session_id == custom_id

        for test_name, result in tests.items():
            status = "✅" if result else "❌"
            print(f"  {status} {test_name}")

        print(f"\n  Session 1 ID: {session1.session_id[:16]}...")
        print(f"  Session 2 ID: {session2.session_id[:16]}...")
        print(f"  Session 3 ID (custom): {session3.session_id}")

        all_passed = all(tests.values())
        return all_passed

    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def interactive_chat_demo():
    """Run interactive chat demo."""
    print_section("Interactive Chat Demo")
    print("Starting interactive chat interface...")
    print("(Type 'exit' to quit)\n")

    try:
        from dev_chat_simple import KortanaDevChat

        chat = KortanaDevChat()
        chat.print_intro()

        print("\n💡 To test the chat system, you can:")
        print("  - Type a message and it will be logged to history")
        print("  - Use 'status' to check session statistics")
        print("  - Use 'export' to save the conversation")
        print("  - Use 'exit' to quit\n")

        return True

    except Exception as e:
        print(f"❌ Error starting demo: {e}")
        return False


def main():
    """Run all tests."""
    print_header("KOR'TANA CHAT FUNCTIONALITY TEST SUITE")

    print("\n📊 Running Tests...\n")

    results = {}

    # Run tests
    print("Test 1: Dev Chat Interface")
    results["Dev Chat Interface"] = test_dev_chat_interface()

    print("\n" + "=" * 70)

    print("Test 2: Core ChatEngine")
    results["ChatEngine"] = test_chat_engine()

    print("\n" + "=" * 70)

    print("Test 3: Memory System")
    results["Memory System"] = test_memory_system()

    print("\n" + "=" * 70)

    print("Test 4: Conversation Flow")
    results["Conversation Flow"] = test_conversation_flow()

    print("\n" + "=" * 70)

    print("Test 5: Session Management")
    results["Session Management"] = test_session_management()

    # Summary
    print_header("TEST SUMMARY")

    print()
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {status}: {test_name}")

    print()
    total_tests = len(results)
    passed_tests = sum(1 for r in results.values() if r)
    total_percent = (passed_tests / total_tests * 100) if total_tests > 0 else 0

    print(f"  Total: {passed_tests}/{total_tests} passed ({total_percent:.0f}%)")
    print()

    if all(results.values()):
        print("✅ ALL TESTS PASSED!")
        print("🗣️  Kor'tana's chat functionality is working correctly!")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

    print("\n" + "=" * 70 + "\n")

    # Offer demo
    try:
        demo_choice = input(
            "Would you like to start the interactive chat demo? (y/n): "
        )
        if demo_choice.lower() in ("y", "yes"):
            interactive_chat_demo()
    except EOFError:
        pass  # Not running in interactive mode


if __name__ == "__main__":
    main()
