"""
Minimal test suite for brain.py core functionality
Tests ChatEngine initialization, mode setting, and basic response generation
"""

import os
from unittest.mock import Mock, patch

import pytest

from src.brain import ChatEngine


@pytest.fixture
def mock_config_files():
    """Mock configuration files to avoid dependency on actual config files"""
    mock_persona = {
        "persona": {
            "default_mode": "presence",
            "modes": {
                "presence": {"description": "Gentle, caring presence"},
                "fire": {"description": "Bold, catalytic energy"},
                "whisper": {"description": "Soft, reverent tone"},
            },
        }
    }

    mock_identity = {
        "presence_states": {
            "presence": {
                "cadence": {"description": "Steady, warm rhythm"},
                "emotional_range": ["calm", "caring", "supportive"],
            }
        }
    }

    mock_models = {
        "models": {
            "gpt-4.1-nano": {
                "provider": "openai",
                "api_key_env": "OPENAI_API_KEY",
                "cost_per_1m_input": 0.15,
                "cost_per_1m_output": 0.60,
            }
        },
        "default_model": "gpt-4.1-nano",
    }

    return {
        "persona.json": mock_persona,
        "identity.json": mock_identity,
        "models_config.json": mock_models,
    }


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    client = Mock()
    client.generate_response.return_value = {
        "choices": [
            {
                "message": {
                    "content": "Hello, I am here with you in this gentle moment.",
                    "tool_calls": [],
                }
            }
        ],
        "usage": Mock(prompt_tokens=50, completion_tokens=20),
        "reasoning": None,
    }
    return client


@pytest.fixture
def chat_engine(mock_config_files, mock_llm_client):
    """Create ChatEngine instance with mocked dependencies"""
    with (
        patch("brain.os.path.exists", return_value=True),
        patch("brain.load_dotenv"),
        patch("brain.os.makedirs"),
        patch.object(ChatEngine, "_load_json_config") as mock_load_config,
        patch("brain.LLMClientFactory") as mock_factory,
        patch("brain.SacredModelRouter") as mock_router,
        patch("brain.MemoryManager") as mock_memory,
        patch("brain.CovenantEnforcer") as mock_covenant,
        patch("brain.load_memory", return_value=[]),
        patch("brain.SacredTrinityRouter") as mock_trinity,
        patch.object(ChatEngine, "_append_to_memory_journal"),
    ):
        # Configure config loading
        def config_side_effect(path):
            filename = os.path.basename(path)
            return mock_config_files.get(filename, {})

        mock_load_config.side_effect = config_side_effect

        # Configure LLM factory
        mock_factory_instance = Mock()
        mock_factory_instance.validate_configuration.return_value = True
        mock_factory_instance.create_client.return_value = mock_llm_client
        mock_factory.return_value = mock_factory_instance

        # Configure router
        mock_router_instance = Mock()
        mock_router_instance.loaded_models_config = mock_config_files[
            "models_config.json"
        ]
        mock_router_instance.select_model_with_sacred_guidance.return_value = (
            "gpt-4.1-nano"
        )
        mock_router_instance.get_model_config.return_value = mock_config_files[
            "models_config.json"
        ]["models"]["gpt-4.1-nano"]
        mock_router_instance.sacred_config.update_performance_data = Mock()
        mock_router.return_value = mock_router_instance

        # Configure memory
        mock_memory_instance = Mock()
        mock_memory_instance.search.return_value = []
        mock_memory.return_value = mock_memory_instance

        # Configure covenant
        mock_covenant_instance = Mock()
        mock_covenant_instance.check_output.return_value = True
        mock_covenant.return_value = mock_covenant_instance

        # Configure trinity router
        mock_trinity_instance = Mock()
        mock_trinity_instance.analyze_prompt_intent.return_value = "compassion"
        mock_trinity.return_value = mock_trinity_instance

        # Disable scheduler for tests
        with patch("brain.BackgroundScheduler"):
            engine = ChatEngine()
            engine.llm_clients = {"gpt-4.1-nano": mock_llm_client}
            return engine


class TestChatEngineBasic:
    """Test basic ChatEngine functionality"""

    def test_initialization(self, chat_engine):
        """Test ChatEngine initializes correctly"""
        assert chat_engine is not None
        assert hasattr(chat_engine, "current_mode")
        assert hasattr(chat_engine, "history")
        assert hasattr(chat_engine, "default_model_id")
        assert chat_engine.default_model_id == "gpt-4.1-nano"

    def test_mode_setting(self, chat_engine):
        """Test mode setting functionality"""
        # Test valid mode
        chat_engine.set_mode("fire")
        assert chat_engine.current_mode == "fire"

        # Test invalid mode falls back to default
        chat_engine.set_mode("invalid_mode")
        assert chat_engine.current_mode == "presence"  # Should fallback to default

    def test_add_user_message(self, chat_engine):
        """Test adding user messages to history"""
        initial_length = len(chat_engine.history)
        chat_engine.add_user_message("Hello Kor'tana")

        assert len(chat_engine.history) == initial_length + 1
        assert chat_engine.history[-1]["role"] == "user"
        assert chat_engine.history[-1]["content"] == "Hello Kor'tana"

    def test_add_assistant_message(self, chat_engine):
        """Test adding assistant messages to history"""
        initial_length = len(chat_engine.history)
        chat_engine.add_assistant_message("Hello, I am here with you")

        assert len(chat_engine.history) == initial_length + 1
        assert chat_engine.history[-1]["role"] == "assistant"
        assert chat_engine.history[-1]["content"] == "Hello, I am here with you"

    def test_basic_response_generation(self, chat_engine):
        """Test basic response generation"""
        user_input = "Hello Kor'tana, how are you today?"
        response = chat_engine.get_response(user_input)

        # Should return a string response
        assert isinstance(response, str)
        assert len(response) > 0

        # Should have added messages to history
        assert len(chat_engine.history) >= 2  # user + assistant messages

    def test_system_prompt_building(self, chat_engine):
        """Test system prompt construction"""
        system_prompt = chat_engine.build_system_prompt()

        assert isinstance(system_prompt, str)
        assert len(system_prompt) > 0
        # Should contain mode information
        assert (
            chat_engine.current_mode in system_prompt.lower()
            or "presence" in system_prompt.lower()
        )


class TestChatEngineAdvanced:
    """Test advanced ChatEngine functionality"""

    def test_task_classification(self, chat_engine):
        """Test task classification functionality"""
        # Test code generation task
        task_category = chat_engine._classify_task(
            "write code for a function", "presence"
        )
        assert task_category.value == "CODE_GENERATION"

        # Test research task
        task_category = chat_engine._classify_task("analyze this document", "presence")
        assert task_category.value == "RESEARCH"

    def test_mode_detection(self, chat_engine):
        """Test automatic mode detection"""
        # Test urgent/fire mode detection
        detected_mode = chat_engine.detect_mode("URGENT HELP NEEDED NOW!")
        assert detected_mode in [
            "fire",
            "tactical",
        ]  # Could be either based on keywords

    def test_response_shaping_by_mode(self, chat_engine):
        """Test response shaping based on current mode"""
        test_response = "This is a test response"

        # Test presence mode (default)
        chat_engine.set_mode("presence")
        shaped_response = chat_engine._shape_response_by_mode(test_response)
        assert isinstance(shaped_response, str)

        # Test fire mode
        chat_engine.set_mode("fire")
        shaped_response = chat_engine._shape_response_by_mode(test_response)
        assert isinstance(shaped_response, str)


def test_minimal_integration():
    """Minimal integration test - can import and create ChatEngine"""
    try:
        # Test that we can import and instantiate without major errors
        with (
            patch("brain.load_dotenv"),
            patch("brain.os.makedirs"),
            patch("brain.LLMClientFactory"),
            patch("brain.SacredModelRouter"),
            patch("brain.MemoryManager"),
            patch("brain.CovenantEnforcer"),
            patch("brain.load_memory", return_value=[]),
            patch("brain.SacredTrinityRouter"),
            patch("brain.BackgroundScheduler"),
            patch("brain.MonitoringAgent"),
            patch("brain.PlanningAgent"),
            patch("brain.TestingAgent"),
            patch.object(ChatEngine, "_load_json_config", return_value={}),
            patch.object(ChatEngine, "_append_to_memory_journal"),
        ):
            engine = ChatEngine()
            assert engine is not None
            assert hasattr(engine, "current_mode")
            assert hasattr(engine, "history")

    except Exception as e:
        pytest.fail(f"Minimal integration test failed: {e}")


def test_can_import_brain_module():
    """Test that brain module can be imported successfully"""
    try:
        import brain

        assert hasattr(brain, "ChatEngine")
    except ImportError as e:
        pytest.fail(f"Cannot import brain module: {e}")


if __name__ == "__main__":
    # Allow running directly for quick testing
    pytest.main([__file__, "-v"])
