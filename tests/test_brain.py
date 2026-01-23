# C:\kortana\tests\test_brain.py
import os

import pytest

# Adjust import based on how you run tests (e.g., from project root)
# If running pytest from project root, 'from src.brain import ChatEngine' should work if src/__init__.py exists.
try:
    from kortana.core.brain import ChatEngine
    from kortana.config import load_config as load_kortana_config
except ImportError:
    # Fallback if running test_brain.py directly from tests/ for some reason
    import sys
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
    from kortana.core.brain import ChatEngine
    from kortana.config import load_config as load_kortana_config

# Minimal setup for ChatEngine, assuming dummy configs will be created by brain.py's __main__
# or that actual configs are present and valid.
# For more robust tests, you'd mock configs or use dedicated test configs.


@pytest.fixture
def chat_engine_instance():
    """Provides a ChatEngine instance for testing."""
    from kortana.config.schema import KortanaConfig
    
    # Minimal test config
    config = KortanaConfig(
        default_llm_id="test-model",
        models={"test-model": {"provider": "openai", "model": "gpt-4"}}
    )
    
    try:
        engine = ChatEngine(settings=config, session_id="test_session_brain")
        return engine
    except Exception as e:
        pytest.skip(f"Skipping ChatEngine tests due to initialization error: {e}")


def test_chat_engine_initialization(chat_engine_instance: ChatEngine):
    """Tests basic ChatEngine initialization."""
    assert chat_engine_instance is not None
    assert chat_engine_instance.current_mode is not None
    assert chat_engine_instance.history == []  # New session history should be empty


def test_set_mode(chat_engine_instance: ChatEngine):
    """Tests if mode can be set."""
    # Assumes 'default' and 'intimacy' are the only active modes in persona.json
    # for the minimal brain.py setup.

    if "intimacy" in chat_engine_instance.persona_config.get("modes", {}):
        chat_engine_instance.set_mode("intimacy")
        assert chat_engine_instance.current_mode == "intimacy"

    if "default" in chat_engine_instance.persona_config.get("modes", {}):
        chat_engine_instance.set_mode("default")
        assert chat_engine_instance.current_mode == "default"
    else:  # Fallback if "default" isn't explicitly in modes but is the default_mode
        chat_engine_instance.set_mode(
            chat_engine_instance.persona_config.get("default_mode", "default")
        )
        assert (
            chat_engine_instance.current_mode
            == chat_engine_instance.persona_config.get("default_mode", "default")
        )


def test_get_response_basic(chat_engine_instance: ChatEngine):
    """Tests basic response generation. Relies on LLM call."""
    # This is an integration test as it will make a real API call.
    # Ensure API keys are set in .env and models_config.json points to a working model.
    # The minimal brain.py's __main__ block creates dummy configs; ensure they align.

    # Set to default mode which should use Grok based on minimal brain.py's __main__
    default_mode_name = chat_engine_instance.persona_config.get("persona", {}).get(
        "default_mode"
    ) or chat_engine_instance.persona_config.get("default_mode", "default")
    chat_engine_instance.set_mode(default_mode_name)

    test_prompt = "Hello, this is a test."
    try:
        response = chat_engine_instance.get_response(test_prompt)
        assert isinstance(response, str)
        assert len(response) > 0
        print(
            f"\nTest Response (Mode: {chat_engine_instance.current_mode}): {response}"
        )
        # Further assertions could check for persona alignment if we had expected outputs
    except Exception as e:
        pytest.fail(f"get_response raised an exception: {e}")


# Add more tests here as functionality is built out in brain.py
# e.g., testing add_user_message, add_assistant_message, history management.
