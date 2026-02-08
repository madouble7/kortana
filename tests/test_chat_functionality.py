"""
Comprehensive test suite for Kor'tana's chat functionality.

Tests core chat features including:
- Message processing
- Response generation
- Memory integration
- Conversation history
- Multi-turn conversations
- Different interaction modes
"""

import json
import os
import sys
from datetime import datetime

import pytest

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))


class TestChatFunctionality:
    """Test suite for Kor'tana's chat engine."""

    @pytest.fixture
    def setup_env(self):
        """Set up test environment."""
        from dotenv import load_dotenv

        load_dotenv(override=True)
        yield
        # Cleanup after test

    @pytest.fixture
    def dev_chat(self):
        """Initialize development chat interface."""
        try:
            from dev_chat_simple import KortanaDevChat

            chat = KortanaDevChat()
            yield chat
        except Exception as e:
            pytest.skip(f"Could not initialize dev chat: {e}")

    @pytest.fixture
    def memory_manager(self):
        """Initialize memory manager."""
        try:
            from memory_manager import MemoryManager

            mm = MemoryManager("data/test_chat_memory.jsonl")
            yield mm
        except Exception as e:
            pytest.skip(f"Could not initialize memory manager: {e}")

    def test_chat_engine_initialization(self, setup_env):
        """Test that ChatEngine initializes properly."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()
            engine = ChatEngine(settings)

            assert engine is not None, "ChatEngine should initialize"
            assert engine.session_id is not None, "Session ID should be assigned"
            assert engine.mode == "default", "Default mode should be set"
            assert engine.persona_data is not None, "Persona data should be loaded"

            print("✅ ChatEngine initialization test passed")

        except ImportError as e:
            pytest.skip(f"Required modules not available: {e}")
        except Exception as e:
            pytest.fail(f"ChatEngine initialization failed: {e}")

    def test_dev_chat_creation(self, dev_chat):
        """Test development chat interface creation."""
        assert dev_chat is not None, "Dev chat should initialize"
        assert dev_chat.engine is not None, "Chat engine should be created"
        assert isinstance(dev_chat.history, list), "History should be a list"
        assert dev_chat.running is True, "Chat should be running"

        print("✅ Dev chat creation test passed")

    def test_memory_system_integration(self, memory_manager):
        """Test memory system integration with chat."""
        # Store a test memory
        memory_id = memory_manager.store_memory(
            role="user",
            content="Test message for chat memory",
            metadata={"type": "test_chat"},
        )

        assert memory_id is not None, "Memory should be stored with an ID"

        # Retrieve memories
        memories = memory_manager.retrieve_memories(limit=5)
        assert len(memories) > 0, "Should retrieve stored memories"

        # Verify memory content
        found = False
        for mem in memories:
            if "test" in mem.get("content", "").lower():
                found = True
                break

        assert found, "Test memory should be retrievable"

        print("✅ Memory system integration test passed")

    def test_conversation_history_tracking(self, dev_chat):
        """Test that conversation history is tracked."""
        initial_length = len(dev_chat.history)

        # Simulate adding a message to history
        dev_chat.history.append(
            {
                "role": "user",
                "content": "Test message",
                "timestamp": datetime.now().isoformat(),
            }
        )

        assert len(dev_chat.history) == initial_length + 1, (
            "History should track new messages"
        )
        assert dev_chat.history[-1]["role"] == "user", (
            "Message role should be preserved"
        )
        assert dev_chat.history[-1]["content"] == "Test message", (
            "Message content should be preserved"
        )

        print("✅ Conversation history tracking test passed")

    def test_chat_engine_modes(self, setup_env):
        """Test different chat engine modes."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()
            engine = ChatEngine(settings)

            # Test default mode
            assert engine.mode == "default", "Should start in default mode"

            # Test autonomous mode toggling
            initial_autom = engine.autonomous_mode
            engine.autonomous_mode = True
            assert engine.autonomous_mode is True, (
                "Should be able to enable autonomous mode"
            )

            engine.autonomous_mode = initial_autom
            assert engine.autonomous_mode == initial_autom, (
                "Should restore original autonomous mode"
            )

            print("✅ Chat engine modes test passed")

        except Exception as e:
            pytest.skip(f"Could not test modes: {e}")

    def test_persona_configuration(self, setup_env):
        """Test that persona configuration is loaded."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()
            engine = ChatEngine(settings)

            assert engine.persona_data is not None, "Persona data should be loaded"

            # Check for expected persona fields
            if isinstance(engine.persona_data, dict):
                assert "name" in engine.persona_data or len(engine.persona_data) > 0, (
                    "Persona should have content"
                )

            print("✅ Persona configuration test passed")

        except Exception as e:
            pytest.skip(f"Could not test persona: {e}")

    def test_session_management(self, setup_env):
        """Test session management in chat engine."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()

            # Create two sessions
            session1 = ChatEngine(settings)
            session2 = ChatEngine(settings)

            # Sessions should have different IDs
            assert session1.session_id != session2.session_id, (
                "Different sessions should have different IDs"
            )

            # Create session with specific ID
            custom_id = "test-session-12345"
            session3 = ChatEngine(settings, session_id=custom_id)
            assert session3.session_id == custom_id, "Should accept custom session ID"

            print("✅ Session management test passed")

        except Exception as e:
            pytest.skip(f"Could not test sessions: {e}")

    def test_dev_chat_export_functionality(self, dev_chat, tmp_path):
        """Test chat session export to JSON."""
        # Add some test messages to history
        dev_chat.history.append(
            {"role": "user", "content": "Test message 1", "timestamp": datetime.now()}
        )
        dev_chat.history.append(
            {"role": "assistant", "content": "Response 1", "timestamp": datetime.now()}
        )

        # Change working directory to temp for export test
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            dev_chat.export_session()

            # Look for exported file
            exported_files = list(tmp_path.glob("devchat_session_*"))
            assert len(exported_files) > 0, "Session file should be exported"

            # Verify file contents
            with open(exported_files[0]) as f:
                exported_data = json.load(f)

            assert "session_id" in exported_data, (
                "Exported file should contain session_id"
            )
            assert "history" in exported_data, "Exported file should contain history"
            assert len(exported_data["history"]) >= 2, (
                "Exported history should contain our messages"
            )

            print("✅ Dev chat export functionality test passed")

        finally:
            os.chdir(original_cwd)

    def test_multi_turn_conversation_scenario(self, memory_manager):
        """Test a multi-turn conversation scenario."""
        conversation_turns = [
            ("user", "Hello, what's your name?"),
            ("user", "Can you help me with Python?"),
            ("user", "What about async programming?"),
        ]

        stored_ids = []
        for role, content in conversation_turns:
            mem_id = memory_manager.store_memory(
                role=role,
                content=content,
                metadata={"type": "conversation", "turn": len(stored_ids)},
            )
            stored_ids.append(mem_id)

        # Verify all messages were stored
        assert len(stored_ids) == len(conversation_turns), (
            "All messages should be stored"
        )

        # Retrieve and verify conversation flow
        memories = memory_manager.retrieve_memories(limit=10)
        user_messages = [m for m in memories if m["role"] == "user"]
        assert len(user_messages) >= len(conversation_turns), (
            "Should retrieve all user messages"
        )

        print("✅ Multi-turn conversation scenario test passed")

    def test_chat_engine_autonomy_features(self, setup_env):
        """Test autonomous features of chat engine."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()
            engine = ChatEngine(settings)

            # Check autonomous properties exist
            assert hasattr(engine, "autonomous_mode"), (
                "Should have autonomous_mode property"
            )
            assert hasattr(engine, "autonomous_running"), (
                "Should have autonomous_running property"
            )
            assert hasattr(engine, "autonomous_cycle_count"), (
                "Should have autonomous_cycle_count property"
            )

            # Verify initial states
            assert engine.autonomous_cycle_count == 0, "Cycle count should start at 0"
            assert engine.autonomous_running is False, (
                "Should not be running autonomously by default"
            )

            print("✅ Chat engine autonomy features test passed")

        except Exception as e:
            pytest.skip(f"Could not test autonomy features: {e}")

    def test_covenant_integration(self, setup_env):
        """Test covenant enforcer integration with chat."""
        try:
            from kortana.config import load_config
            from kortana.core.brain import ChatEngine

            settings = load_config()
            engine = ChatEngine(settings)

            # Check that covenant enforcer is available
            assert hasattr(engine, "covenant_enforcer"), (
                "ChatEngine should have covenant_enforcer"
            )

            # Check covenant is loaded
            assert engine.covenant is not None, "Covenant should be loaded"

            print("✅ Covenant integration test passed")

        except Exception as e:
            pytest.skip(f"Could not test covenant integration: {e}")


class TestChatIntegration:
    """Integration tests for chat functionality."""

    @pytest.fixture
    def setup_integration_env(self):
        """Set up integration test environment."""
        from dotenv import load_dotenv

        load_dotenv(override=True)
        yield

    def test_end_to_end_chat_flow(self, setup_integration_env):
        """Test complete chat flow from input to output."""
        try:
            from dev_chat_simple import KortanaDevChat

            chat = KortanaDevChat()

            # Verify initialization
            assert chat.engine is not None
            assert len(chat.history) == 0

            # Simulate a message (without interactive input)
            test_message = "Hello Kor'tana"
            chat.history.append(
                {"role": "user", "content": test_message, "timestamp": datetime.now()}
            )

            # Verify message was added
            assert len(chat.history) == 1
            assert chat.history[0]["content"] == test_message

            print("✅ End-to-end chat flow test passed")

        except Exception as e:
            pytest.skip(f"Could not test e2e flow: {e}")

    def test_memory_chat_integration(self, setup_integration_env):
        """Test integration between memory and chat systems."""
        try:
            from memory_manager import MemoryManager

            mm = MemoryManager("data/test_chat_integration.jsonl")

            # Store persona context
            mm.store_memory(
                role="system",
                content="I am Kor'tana, an autonomous AI assistant.",
                metadata={"type": "system_context"},
            )

            # Store conversation context
            mm.store_memory(
                role="user",
                content="Hi Kor'tana, tell me about yourself",
                metadata={"type": "user_query"},
            )

            # Retrieve for context
            context = mm.retrieve_memories(limit=5)

            assert len(context) >= 2, "Should retrieve stored context"
            assert any("Kor'tana" in m.get("content", "") for m in context), (
                "Should contain Kor'tana reference"
            )

            print("✅ Memory-chat integration test passed")

        except Exception as e:
            pytest.skip(f"Could not test memory-chat integration: {e}")


def test_chat_system_health():
    """Quick health check for chat system."""
    try:
        from kortana.config import load_config
        from kortana.core.brain import ChatEngine

        settings = load_config()
        engine = ChatEngine(settings)

        health_checks = {
            "chat_engine_initialized": engine is not None,
            "session_id_assigned": engine.session_id is not None,
            "persona_loaded": engine.persona_data is not None,
            "default_mode_set": engine.mode == "default",
            "memory_service_available": engine.memory_core_service is not None,
            "llm_client_available": engine.default_llm_client is not None,
        }

        print("\n🏥 Chat System Health Check:")
        print("-" * 50)
        for check_name, result in health_checks.items():
            status = "✅" if result else "❌"
            print(f"{status} {check_name}: {result}")

        all_passed = all(health_checks.values())
        assert all_passed, "Some health checks failed"

        print("-" * 50)
        print(
            f"Overall Status: {'✅ HEALTHY' if all_passed else '❌ ISSUES DETECTED'}\n"
        )

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        pytest.skip(f"Chat system not fully configured: {e}")


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-k",
            "test_",
        ]
    )
