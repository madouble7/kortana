from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session  # Assuming Session is used for type hinting

# Adjust the import path based on your project structure
from src.kortana.core.orchestrator import KorOrchestrator

# Mocked service and evaluator classes for dependency injection
# These would typically be imported if they were real classes,
# but for testing KorOrchestrator in isolation, we can mock them directly.


@pytest.fixture
def mock_llm_client():
    """Fixture to mock LLM client from llm_clients module."""
    client = AsyncMock()
    client.generate_response.return_value = {
        "content": "This is a mocked LLM response for testing.",
        "model_id_used": "gpt-4.1-nano",
        "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
        "error": None,
    }
    return client


@pytest.fixture
def mock_llm_factory():
    """Fixture to mock LLMClientFactory."""
    factory = MagicMock()
    factory.get_client.return_value = mock_llm_client(AsyncMock())
    return factory


@pytest.fixture
def mock_db_session():
    """Fixture to mock the SQLAlchemy DB session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_memory_core_service():
    """Fixture to mock MemoryCoreService."""
    service = MagicMock()
    # Simulate search_memories_semantic returning a list of dicts as per orchestrator usage
    service.search_memories_semantic.return_value = [
        {"memory": MagicMock(content="Test memory 1"), "score": 0.9},
        {"memory": MagicMock(content="Test memory 2"), "score": 0.8},
    ]
    return service


@pytest.fixture
def mock_arrogance_evaluator():
    """Fixture to mock AlgorithmicArroganceEvaluator."""
    evaluator = AsyncMock()  # Use AsyncMock for async methods
    evaluator.evaluate_response.return_value = {
        "arrogance_score": 0.1,
        "feedback": "Looks good.",
    }
    return evaluator


@pytest.fixture
def mock_uncertainty_handler():
    """Fixture to mock UncertaintyHandler."""
    handler = AsyncMock()  # Use AsyncMock for async methods
    handler.manage_uncertainty.return_value = (
        "Final response after handling uncertainty."
    )
    return handler


@pytest.mark.asyncio
async def test_kor_orchestrator_init(
    mock_db_session,
    mock_memory_core_service,
    mock_arrogance_evaluator,
    mock_uncertainty_handler,
    mock_llm_factory,
):
    """Test KorOrchestrator initialization."""
    with (
        patch(
            "src.kortana.core.orchestrator.MemoryCoreService",
            return_value=mock_memory_core_service,
        ),
        patch(
            "src.kortana.core.orchestrator.AlgorithmicArroganceEvaluator",
            return_value=mock_arrogance_evaluator,
        ),
        patch(
            "src.kortana.core.orchestrator.UncertaintyHandler",
            return_value=mock_uncertainty_handler,
        ),
        patch(
            "src.kortana.core.orchestrator.LLMClientFactory",
            return_value=mock_llm_factory,
        ),
        patch(
            "src.kortana.core.orchestrator.KorOrchestrator._load_models_config",
            return_value={
                "default": {"model": "gpt-4.1-nano"},
                "models": {"gpt-4.1-nano": {}},
            },
        ),
    ):
        orchestrator = KorOrchestrator(db=mock_db_session)

        assert orchestrator.db == mock_db_session
        assert orchestrator.memory_service == mock_memory_core_service
        assert orchestrator.arrogance_evaluator == mock_arrogance_evaluator
        assert orchestrator.uncertainty_handler == mock_uncertainty_handler
        assert orchestrator.default_model_id == "gpt-4.1-nano"
        print("KorOrchestrator initialized successfully with mocked dependencies.")


@pytest.mark.asyncio
async def test_process_query(
    mock_db_session,
    mock_memory_core_service,
    mock_arrogance_evaluator,
    mock_uncertainty_handler,
    mock_llm_client,
    mock_llm_factory,
):
    """Test the main process_query loop of KorOrchestrator."""
    with (
        patch(
            "src.kortana.core.orchestrator.MemoryCoreService",
            return_value=mock_memory_core_service,
        ),
        patch(
            "src.kortana.core.orchestrator.AlgorithmicArroganceEvaluator",
            return_value=mock_arrogance_evaluator,
        ),
        patch(
            "src.kortana.core.orchestrator.UncertaintyHandler",
            return_value=mock_uncertainty_handler,
        ),
        patch(
            "src.kortana.core.orchestrator.LLMClientFactory",
            return_value=mock_llm_factory,
        ),
        patch(
            "src.kortana.core.orchestrator.KorOrchestrator._load_models_config",
            return_value={
                "default": {"model": "gpt-4.1-nano"},
                "models": {"gpt-4.1-nano": {}},
            },
        ),
    ):
        # Set up the mock LLM client
        mock_llm_factory.get_client.return_value = mock_llm_client

        orchestrator = KorOrchestrator(db=mock_db_session)
        query = "Tell me about Kor'tana."

        response = await orchestrator.process_query(query)

        # 1. Check memory search
        mock_memory_core_service.search_memories_semantic.assert_called_once_with(
            query, top_k=3
        )

        # 2. Check LLM client call
        mock_llm_factory.get_client.assert_called_once_with("gpt-4.1-nano")
        mock_llm_client.generate_response.assert_called_once()
        call_args = mock_llm_client.generate_response.call_args[0]
        assert len(call_args) == 0  # Should be using keyword args
        call_kwargs = mock_llm_client.generate_response.call_args[1]
        assert "system_prompt" in call_kwargs
        assert "messages" in call_kwargs
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

        # 3. Check ethical evaluation call
        expected_llm_response = "This is a mocked LLM response for testing."
        expected_llm_metadata = {
            "model": "gpt-4.1-nano",
            "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
        }
        mock_arrogance_evaluator.evaluate_response.assert_called_once_with(
            response_text=expected_llm_response,
            metadata=expected_llm_metadata,
            query_context=query,
        )  # 4. Check uncertainty handling call
        mock_uncertainty_handler.manage_uncertainty.assert_called_once_with(
            original_query=query,
            llm_response=expected_llm_response,
            evaluation_results=await mock_arrogance_evaluator.evaluate_response.return_value,
        )

        # Check final response structure (based on updated implementation)
        assert response["original_query"] == query
        assert (
            len(response["context_from_memory"]) == 2
        )  # Based on mock_memory_core_service
        assert response["context_from_memory"][0] == "Test memory 1"
        assert response["raw_llm_response"] == expected_llm_response
        assert "prompt_sent_to_llm" in response
        assert response["llm_metadata"] == expected_llm_metadata
        assert (
            response["ethical_evaluation"]
            == await mock_arrogance_evaluator.evaluate_response.return_value
        )
        assert (
            response["final_kortana_response"]
            == await mock_uncertainty_handler.manage_uncertainty.return_value
        )
        print(f"process_query returned: {response}")


@pytest.mark.asyncio
async def test_process_query_with_empty_memories(
    mock_db_session,
    mock_memory_core_service,
    mock_arrogance_evaluator,
    mock_uncertainty_handler,
    mock_llm_client,
    mock_llm_factory,
):
    """Test process_query when no memories are found by semantic search."""
    # Override the return value for this specific test case
    mock_memory_core_service.search_memories_semantic.return_value = []

    with (
        patch(
            "src.kortana.core.orchestrator.MemoryCoreService",
            return_value=mock_memory_core_service,
        ),
        patch(
            "src.kortana.core.orchestrator.AlgorithmicArroganceEvaluator",
            return_value=mock_arrogance_evaluator,
        ),
        patch(
            "src.kortana.core.orchestrator.UncertaintyHandler",
            return_value=mock_uncertainty_handler,
        ),
        patch(
            "src.kortana.core.orchestrator.LLMClientFactory",
            return_value=mock_llm_factory,
        ),
        patch(
            "src.kortana.core.orchestrator.KorOrchestrator._load_models_config",
            return_value={
                "default": {"model": "gpt-4.1-nano"},
                "models": {"gpt-4.1-nano": {}},
            },
        ),
    ):
        orchestrator = KorOrchestrator(db=mock_db_session)
        query = "An obscure query for which no memories exist."

        response = await orchestrator.process_query(query)

        # Verify memory search was called
        mock_memory_core_service.search_memories_semantic.assert_called_with(
            query, top_k=3
        )

        # Verify context from memory is empty
        assert (
            response["context_from_memory"] == []
        )  # Verify the rest of the flow still happens (LLM and evaluators are called)
        mock_llm_client.generate_response.assert_called_once()
        mock_arrogance_evaluator.evaluate_response.assert_called_once()
        mock_uncertainty_handler.manage_uncertainty.assert_called_once()

        expected_llm_response = "This is a mocked LLM response for testing."
        assert response["original_query"] == query
        assert response["raw_llm_response"] == expected_llm_response
        assert "prompt_sent_to_llm" in response
        assert (
            response["ethical_evaluation"]
            == await mock_arrogance_evaluator.evaluate_response.return_value
        )
        assert (
            response["final_kortana_response"]
            == await mock_uncertainty_handler.manage_uncertainty.return_value
        )
        print(f"process_query (no memories) returned: {response}")


@pytest.mark.asyncio
async def test_process_query_llm_failure(
    mock_db_session,
    mock_memory_core_service,
    mock_arrogance_evaluator,
    mock_uncertainty_handler,
    mock_llm_client,
    mock_llm_factory,
):
    """Test process_query handling when the LLM client returns an error."""
    # Override the return value of the mock to simulate a failure
    mock_llm_client.generate_response.return_value = {
        "content": None,
        "error": "Simulated LLM client error for testing",
    }

    with (
        patch(
            "src.kortana.core.orchestrator.MemoryCoreService",
            return_value=mock_memory_core_service,
        ),
        patch(
            "src.kortana.core.orchestrator.AlgorithmicArroganceEvaluator",
            return_value=mock_arrogance_evaluator,
        ),
        patch(
            "src.kortana.core.orchestrator.UncertaintyHandler",
            return_value=mock_uncertainty_handler,
        ),
        patch(
            "src.kortana.core.orchestrator.LLMClientFactory",
            return_value=mock_llm_factory,
        ),
        patch(
            "src.kortana.core.orchestrator.KorOrchestrator._load_models_config",
            return_value={
                "default": {"model": "gpt-4.1-nano"},
                "models": {"gpt-4.1-nano": {}},
            },
        ),
    ):
        # Set up the mock LLM client
        mock_llm_factory.get_client.return_value = mock_llm_client

        orchestrator = KorOrchestrator(db=mock_db_session)
        query = "This should trigger an LLM error."

        response = await orchestrator.process_query(query)

        # Check that we get the expected error response
        assert "error" in response
        assert response["error"] == "Failed to get response from reasoning core."
        assert response["error_detail"] == "Simulated LLM client error for testing"
        assert response["original_query"] == query
        assert "prompt_sent_to_llm" in response
        assert (
            "I'm having trouble connecting to my reasoning core"
            in response["final_kortana_response"]
        )

        # Verify the LLM client was called but not the evaluator (since there's no response to evaluate)
        mock_llm_client.generate_response.assert_called_once()
        mock_arrogance_evaluator.evaluate_response.assert_not_called()
        mock_uncertainty_handler.manage_uncertainty.assert_not_called()


@pytest.mark.asyncio
async def test_process_query_client_initialization_failure(
    mock_db_session,
    mock_memory_core_service,
    mock_arrogance_evaluator,
    mock_uncertainty_handler,
    mock_llm_factory,
):
    """Test process_query handling when the LLM client factory fails to create a client."""
    # Set the get_client method to return None to simulate initialization failure
    mock_llm_factory.get_client.return_value = None

    with (
        patch(
            "src.kortana.core.orchestrator.MemoryCoreService",
            return_value=mock_memory_core_service,
        ),
        patch(
            "src.kortana.core.orchestrator.AlgorithmicArroganceEvaluator",
            return_value=mock_arrogance_evaluator,
        ),
        patch(
            "src.kortana.core.orchestrator.UncertaintyHandler",
            return_value=mock_uncertainty_handler,
        ),
        patch(
            "src.kortana.core.orchestrator.LLMClientFactory",
            return_value=mock_llm_factory,
        ),
        patch(
            "src.kortana.core.orchestrator.KorOrchestrator._load_models_config",
            return_value={
                "default": {"model": "gpt-4.1-nano"},
                "models": {"gpt-4.1-nano": {}},
            },
        ),
    ):
        orchestrator = KorOrchestrator(db=mock_db_session)
        query = "This should trigger a client initialization failure."

        response = await orchestrator.process_query(query)

        # Check that we get the expected error response
        assert "error" in response
        assert response["error"] == "Failed to initialize LLM service."
        assert "Failed to initialize LLM client for model" in response["error_detail"]
        assert response["original_query"] == query
        assert "prompt_sent_to_llm" in response
        assert (
            "I'm having trouble connecting to my reasoning core"
            in response["final_kortana_response"]
        )

        # Verify the factory was called but not the evaluator (since there's no client)
        mock_llm_factory.get_client.assert_called_once_with("gpt-4.1-nano")
        mock_arrogance_evaluator.evaluate_response.assert_not_called()
        mock_uncertainty_handler.manage_uncertainty.assert_not_called()
