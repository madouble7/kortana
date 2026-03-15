"""Test script for Google GenAI client"""

import os

import pytest
from dotenv import load_dotenv

# Import the Google GenAI client from your project structure
from kortana.llm_clients.genai_client import GoogleGenAIClient


@pytest.fixture(scope="module")
def google_api_key():
    """Load and validate Google API key from environment."""
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY not found in environment variables")
    return api_key


@pytest.fixture(scope="module")
def genai_client(google_api_key):
    """Create GoogleGenAIClient instance for testing."""
    return GoogleGenAIClient(
        api_key=google_api_key, model_name="gemini-1.5-flash-latest"
    )


def test_google_genai_client_creation(google_api_key):
    """Test that GoogleGenAIClient can be instantiated successfully."""
    client = GoogleGenAIClient(
        api_key=google_api_key, model_name="gemini-1.5-flash-latest"
    )
    assert client is not None


def test_basic_api_call(genai_client):
    """Test basic API call functionality."""
    system_prompt = "You are a helpful assistant."
    messages = [
        {
            "role": "user",
            "content": "Say 'Hello, this is a test response from Google GenAI!' in exactly those words.",
        }
    ]

    response = genai_client.generate_response(system_prompt, messages)

    assert response is not None
    assert isinstance(response, dict)
    # Check for standard OpenAI-like response structure
    if "choices" in response:
        assert len(response["choices"]) > 0
        assert "message" in response["choices"][0]
        assert "content" in response["choices"][0]["message"]


def test_custom_parameters(genai_client):
    """Test API call with custom generation parameters."""
    test_params = {"temperature": 0.7, "max_output_tokens": 150, "top_p": 0.9}

    response = genai_client.generate_response(
        system_prompt="You are a creative assistant.",
        messages=[
            {
                "role": "user",
                "content": "Write a very short creative story about a robot.",
            }
        ],
        **test_params,
    )

    assert response is not None
    assert isinstance(response, dict)
    if "choices" in response and len(response["choices"]) > 0:
        content = response["choices"][0]["message"]["content"]
        assert isinstance(content, str)
        assert len(content) > 0
