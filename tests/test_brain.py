import os
import pytest

from kortana.brain import ChatEngine
from kortana.config import load_kortana_config

@pytest.fixture
def chat_engine_instance():
    """Provides a ChatEngine instance for testing."""
    try:
        settings = load_kortana_config()
        engine = ChatEngine(settings=settings, session_id="test_session_brain")
        return engine
    except Exception as e:
        pytest.skip(f"Skipping ChatEngine tests: {e}")


def test_chat_engine_initialization(chat_engine_instance: ChatEngine):
    """Tests basic ChatEngine initialization."""
    assert chat_engine_instance is not None
    assert chat_engine_instance.mode == "default"
    assert chat_engine_instance.history == []


def test_set_mode(chat_engine_instance: ChatEngine):
    """Tests if mode can be set."""
    chat_engine_instance.set_mode("presence")
    assert chat_engine_instance.mode == "presence"
    assert chat_engine_instance.current_mode == "presence"


def test_get_response_basic(chat_engine_instance: ChatEngine):
    """Tests basic response generation."""
    chat_engine_instance.set_mode("default")
    test_prompt = "Hello, this is a test."
    try:
        response = chat_engine_instance.get_response(test_prompt)
        assert isinstance(response, str)
    except Exception as e:
        pytest.fail(f"get_response raised an exception: {e}")


# Add more tests here as functionality is built out in brain.py
# e.g., testing add_user_message, add_assistant_message, history management.
