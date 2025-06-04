"""
Integration test for ChatEngine in the brain module.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Make sure PYTHONPATH includes the project root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.kortana.core.brain import ChatEngine


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = MagicMock()

    # Set up the necessary attributes
    config.paths = MagicMock()
    config.paths.persona_file_path = "config/persona.json"
    config.paths.identity_file_path = "config/identity.json"
    config.paths.covenant_file_path = "config/covenant.yaml"

    config.default_llm_id = "gpt-3.5-turbo"
    config.agents = MagicMock()
    config.agents.default_llm_id = "gpt-3.5-turbo"
    config.agents.types = {
        "coding": {},
        "planning": {},
        "testing": {},
        "monitoring": {"enabled": True, "interval_seconds": 60},
    }

    return config


@pytest.mark.asyncio
@patch("src.kortana.core.brain.PineconeMemoryManager")
@patch("src.kortana.core.brain.JsonLogMemoryManager")
@patch("src.kortana.core.brain.LLMClientFactory")
@patch("src.kortana.core.brain.SacredModelRouter")
@patch("src.kortana.core.brain.CovenantEnforcer")
async def test_chat_engine_lowercase_love(
    mock_covenant_enforcer,
    mock_router,
    mock_llm_factory,
    mock_json_memory,
    mock_pinecone_memory,
    mock_config,
):
    """Test that ChatEngine applies lowercase love transformation."""
    # Set up mocks
    mock_llm_client = MagicMock()
    mock_llm_client.complete.return_value = {"content": "This is a TEST Response"}

    mock_llm_factory_instance = MagicMock()
    mock_llm_factory_instance.get_client.return_value = mock_llm_client
    mock_llm_factory.return_value = mock_llm_factory_instance

    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = ("gpt-3.5-turbo", "default", {})
    mock_router.return_value = mock_router_instance

    mock_covenant_enforcer_instance = MagicMock()
    mock_covenant_enforcer_instance.enforce.return_value = (True, "")
    mock_covenant_enforcer.return_value = mock_covenant_enforcer_instance

    # Create ChatEngine instance
    chat_engine = ChatEngine(settings=mock_config)

    # Process a message
    response = await chat_engine.process_message("This is a TEST Message")

    # Check that response is lowercase
    assert response == "this is a test response"

    # Verify that the message was processed
    mock_router_instance.route.assert_called_once()
    mock_llm_client.complete.assert_called_once()


@pytest.mark.asyncio
@patch("src.kortana.core.brain.text_analysis")
@patch("src.kortana.core.brain.PineconeMemoryManager")
@patch("src.kortana.core.brain.JsonLogMemoryManager")
@patch("src.kortana.core.brain.LLMClientFactory")
@patch("src.kortana.core.brain.SacredModelRouter")
@patch("src.kortana.core.brain.CovenantEnforcer")
async def test_chat_engine_text_analysis(
    mock_covenant_enforcer,
    mock_router,
    mock_llm_factory,
    mock_json_memory,
    mock_pinecone_memory,
    mock_text_analysis,
    mock_config,
):
    """Test that ChatEngine uses text analysis module."""
    # Set up mocks
    mock_llm_client = MagicMock()
    mock_llm_client.complete.return_value = {"content": "Test Response"}

    mock_llm_factory_instance = MagicMock()
    mock_llm_factory_instance.get_client.return_value = mock_llm_client
    mock_llm_factory.return_value = mock_llm_factory_instance

    mock_router_instance = MagicMock()
    mock_router_instance.route.return_value = ("gpt-3.5-turbo", "default", {})
    mock_router.return_value = mock_router_instance

    mock_covenant_enforcer_instance = MagicMock()
    mock_covenant_enforcer_instance.enforce.return_value = (True, "")
    mock_covenant_enforcer.return_value = mock_covenant_enforcer_instance

    # Set up text analysis mocks
    mock_text_analysis.identify_important_message_for_context.return_value = True
    mock_text_analysis.analyze_sentiment.return_value = 0.5
    mock_text_analysis.detect_emphasis_all_caps.return_value = False
    mock_text_analysis.detect_keywords.return_value = ["test"]

    # Create ChatEngine instance
    chat_engine = ChatEngine(settings=mock_config)

    # Process a message
    await chat_engine.process_message("Test message")

    # Verify text analysis functions were called
    mock_text_analysis.identify_important_message_for_context.assert_called_once_with(
        "Test message"
    )
    mock_text_analysis.analyze_sentiment.assert_called_once_with("Test message")
    mock_text_analysis.detect_emphasis_all_caps.assert_called_once_with("Test message")
    mock_text_analysis.detect_keywords.assert_called_once_with("Test message")
