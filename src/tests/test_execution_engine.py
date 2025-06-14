import pytest

from kortana.config.schema import KortanaConfig


def test_chat_engine_config_creation():
    """Test that we can create a default configuration."""
    settings = KortanaConfig()
    assert settings is not None
    assert hasattr(settings, "default_llm_id")
    assert hasattr(settings, "agents")
    assert hasattr(settings, "memory")
    assert hasattr(settings, "persona")
    assert hasattr(settings, "paths")


@pytest.mark.skip(reason="ChatEngine initialization starts background processes")
def test_chat_engine_initialization():
    """Test ChatEngine initialization (currently skipped due to background processes)."""
    from kortana.core.brain import ChatEngine

    settings = KortanaConfig()
    engine = ChatEngine(settings=settings)
    assert engine is not None
