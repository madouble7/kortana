from unittest.mock import patch

import pytest

from src.kortana.services.embedding_service import EmbeddingService, settings


# Test with a valid API key scenario
@patch.object(
    settings, "OPENAI_API_KEY", "fake_api_key"
)  # Mock settings to have the API key
@patch("langchain_openai.OpenAIEmbeddings")  # Mock the actual OpenAI client
def test_embedding_service_initialization_success(MockOpenAIEmbeddings):
    """Test successful initialization of EmbeddingService when API key is present."""
    mock_client_instance = MockOpenAIEmbeddings.return_value
    service = EmbeddingService()
    MockOpenAIEmbeddings.assert_called_once_with(
        model="text-embedding-3-small", openai_api_key="fake_api_key"
    )
    assert service.client == mock_client_instance
    # print("EmbeddingService initialized with OpenAI text-embedding-3-small.") # To match constructor print


# Test with missing API key scenario
@patch.object(settings, "OPENAI_API_KEY", None)  # Mock settings to have NO API key
def test_embedding_service_initialization_failure_no_key():
    """Test EmbeddingService initialization failure when API key is missing."""
    with pytest.raises(ValueError) as excinfo:
        EmbeddingService()
    assert "OPENAI_API_KEY must be set" in str(excinfo.value)


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embedding_for_text_success(MockOpenAIEmbeddings):
    """Test generating embedding for a single text successfully."""
    mock_client_instance = MockOpenAIEmbeddings.return_value
    mock_client_instance.embed_query.return_value = [0.1, 0.2, 0.3]
    service = EmbeddingService()

    test_text = "Hello Kor'tana"
    embedding = service.get_embedding_for_text(test_text)

    mock_client_instance.embed_query.assert_called_once_with(test_text)
    assert embedding == [0.1, 0.2, 0.3]


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embedding_for_text_empty_input(MockOpenAIEmbeddings):
    """Test get_embedding_for_text with empty or whitespace-only input."""
    service = EmbeddingService()
    assert service.get_embedding_for_text("") == []
    assert service.get_embedding_for_text("   ") == []
    MockOpenAIEmbeddings.return_value.embed_query.assert_not_called()


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embeddings_for_texts_success(MockOpenAIEmbeddings):
    """Test generating embeddings for a batch of texts successfully."""
    mock_client_instance = MockOpenAIEmbeddings.return_value
    mock_client_instance.embed_documents.return_value = [[0.1, 0.2], [0.3, 0.4]]
    service = EmbeddingService()

    test_texts = ["First text", "Second text"]
    embeddings = service.get_embeddings_for_texts(test_texts)

    mock_client_instance.embed_documents.assert_called_once_with(test_texts)
    assert embeddings == [[0.1, 0.2], [0.3, 0.4]]


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embeddings_for_texts_empty_input_list(MockOpenAIEmbeddings):
    """Test get_embeddings_for_texts with an empty list of texts."""
    service = EmbeddingService()
    assert service.get_embeddings_for_texts([]) == []
    MockOpenAIEmbeddings.return_value.embed_documents.assert_not_called()


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embeddings_for_texts_with_empty_strings_in_list(MockOpenAIEmbeddings):
    """Test get_embeddings_for_texts filters out empty strings from the list."""
    mock_client_instance = MockOpenAIEmbeddings.return_value
    # mock_client_instance.embed_documents.return_value = [[0.1, 0.2]] # Only one valid text
    service = EmbeddingService()

    test_texts = ["Valid text", "", "   ", "Another valid"]
    # Expected call to embed_documents should only contain non-empty strings
    expected_call_texts = ["Valid text", "Another valid"]
    mock_client_instance.embed_documents.return_value = [
        [0.1, 0.2],
        [0.3, 0.4],
    ]  # two valid texts

    embeddings = service.get_embeddings_for_texts(test_texts)

    mock_client_instance.embed_documents.assert_called_once_with(expected_call_texts)
    assert len(embeddings) == 2  # Expecting two embeddings for the two valid texts


@patch.object(settings, "OPENAI_API_KEY", "fake_api_key")
@patch("langchain_openai.OpenAIEmbeddings")
def test_get_embeddings_for_texts_all_empty_or_whitespace_strings(
    mock_openai_embeddings,
):
    """Test get_embeddings_for_texts returns empty list and does not call client if all inputs are empty/whitespace."""
    service = EmbeddingService()
    test_texts = ["", "   ", "  "]
    embeddings = service.get_embeddings_for_texts(test_texts)
    assert embeddings == []
    mock_openai_embeddings.return_value.embed_documents.assert_not_called()
