from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from kortana.main import app  # Your FastAPI app
from kortana.modules.memory_core import models as memory_models
from kortana.services.database import Base, get_db_sync
from kortana.services.embedding_service import embedding_service

# Use a separate in-memory SQLite database for testing API endpoints
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///./test_kortana_core_api.db"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# Override the dependency to use the test database
@pytest.fixture(scope="function")
def override_get_db_sync_test():
    db = None
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        if db:
            db.close()


@pytest.fixture(scope="function")
def client(override_get_db_sync_test):
    app.dependency_overrides[get_db_sync] = lambda: override_get_db_sync_test
    Base.metadata.create_all(bind=engine_test)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine_test)
    # Ensure the override is removed after the test to avoid interference
    if get_db_sync in app.dependency_overrides:
        del app.dependency_overrides[get_db_sync]


@pytest.mark.asyncio
@patch(
    "src.kortana.core.orchestrator.KorOrchestrator.process_query",
    new_callable=AsyncMock,
)
async def test_core_query_endpoint_success(mock_process_query, client: TestClient):
    """Test the /core/query endpoint with a successful mocked orchestrator response."""
    mock_response_data = {
        "original_query": "Test query",
        "context_from_memory": ["Some memory context"],
        "raw_llm_response": "LLM says hi.",
        "prompt_sent_to_llm": "Test prompt for LLM",
        "llm_metadata": {"model": "gpt-4o-mini", "tokens_used": 25},
        "ethical_evaluation": {"is_potentially_arrogant": False},
        "final_kortana_response": "Kor'tana says hi!",
    }
    mock_process_query.return_value = mock_response_data

    response = client.post("/core/query", json={"query": "Test query"})

    assert response.status_code == 200
    assert response.json() == mock_response_data
    mock_process_query.assert_called_once_with(query="Test query")


@pytest.mark.asyncio
async def test_core_query_endpoint_integration_with_dummy_embeddings(
    client: TestClient, override_get_db_sync_test: Session
):
    """Test /core/query with actual orchestrator but mocked embeddings and DB interaction."""
    db = override_get_db_sync_test
    dummy_embedding = [0.1] * 1536  # OpenAI text-embedding-3-small dimension
    test_memory_content = "Kor'tana remembers the first greeting."
    new_memory = memory_models.CoreMemory(
        title="First Greeting",
        content=test_memory_content,
        memory_type=memory_models.MemoryType.INTERACTION,
        embedding=dummy_embedding,
    )
    db.add(new_memory)
    db.commit()
    db.refresh(new_memory)

    query_text = "first greeting"
    # Mock embedding service and LLM client
    mock_llm_client = AsyncMock()
    mock_llm_client.generate_response.return_value = {
        "content": "Mocked LLM response for integration test",
        "model_id_used": "gpt-4.1-nano",
        "usage": {"prompt_tokens": 50, "completion_tokens": 25, "total_tokens": 75},
        "error": None,
    }

    mock_llm_factory = MagicMock()
    mock_llm_factory.get_client.return_value = mock_llm_client

    with (
        patch.object(
            embedding_service, "get_embedding_for_text", return_value=dummy_embedding
        ) as mock_get_embedding,
        patch(
            "kortana.llm_clients.factory.LLMClientFactory",
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
        response = client.post("/core/query", json={"query": query_text})

    assert response.status_code == 200
    data = response.json()

    mock_get_embedding.assert_called_once_with(query_text)
    mock_llm.assert_called_once()
    assert data["original_query"] == query_text
    assert test_memory_content in data["context_from_memory"]
    assert "raw_llm_response" in data
    assert "prompt_sent_to_llm" in data
    assert "llm_metadata" in data
    assert "ethical_evaluation" in data
    assert "final_kortana_response" in data


def test_core_query_invalid_input(client: TestClient):
    """Test /core/query with invalid (e.g., empty) input."""
    response = client.post("/core/query", json={"query": ""})
    assert response.status_code == 422

    response = client.post("/core/query", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_core_query_integration_no_relevant_memories(
    client: TestClient, override_get_db_sync_test: Session
):
    """Test /core/query with the orchestrator when no relevant memories are expected."""
    db = override_get_db_sync_test
    dummy_embedding_dim = 1536  # OpenAI text-embedding-3-small dimension

    # Seed a memory that is very different from the query
    seed_content = "This is a memory about apples and oranges."
    seed_embedding = [0.75] * dummy_embedding_dim  # Arbitrary embedding

    new_memory = memory_models.CoreMemory(
        title="Fruit Salad",
        content=seed_content,
        memory_type=memory_models.MemoryType.LEARNED_FACT,
        embedding=seed_embedding,
    )
    db.add(new_memory)
    db.commit()

    query_text = "Tell me about quantum mechanics"
    # Mock the embedding service to return an embedding for the query that is
    # intentionally different from the seeded memory's embedding.
    query_embedding = [0.01] * dummy_embedding_dim

    with (
        patch.object(
            embedding_service, "get_embedding_for_text", return_value=query_embedding
        ) as mock_get_embedding,
        patch(
            "src.kortana.services.llm_service.llm_service.generate_response",
            new_callable=AsyncMock,
            return_value={
                "response": "Mocked LLM response about quantum mechanics",
                "metadata": {"model": "gpt-4o-mini", "tokens_used": 45},
            },
        ) as mock_llm,
    ):
        response = client.post("/core/query", json={"query": query_text})

    assert response.status_code == 200
    data = response.json()

    mock_get_embedding.assert_called_once_with(query_text)
    mock_llm.assert_called_once()
    assert data["original_query"] == query_text
    # Based on the orchestrator logic, if no memories are scored high enough (due to dissimilar embeddings),
    # the context_from_memory list should be empty.
    assert data["context_from_memory"] == []
    assert "raw_llm_response" in data
    assert "prompt_sent_to_llm" in data
    assert "llm_metadata" in data
    assert "ethical_evaluation" in data
    assert "final_kortana_response" in data
