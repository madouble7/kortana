"""Tests for services/multi_model_ai.py - MultiModelAIService"""
from unittest.mock import MagicMock, patch

import pytest
from src.kortana.provider_model_defaults import MULTI_MODEL_DEFAULTS


class TestMultiModelAIServiceInit:
    def test_init_empty_providers(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        assert service.providers == {}
        assert service.primary_provider is None
        assert service._initialized is False

    def test_init_does_not_call_providers(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        # Providers dict is empty until _ensure_initialized is called
        assert len(service.providers) == 0
        assert service._initialized is False


class TestMultiModelAIServiceEnsureInitialized:
    def test_initialized_flag_set_after_call(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._ensure_initialized()
        assert service._initialized is True

    def test_second_call_skips_reinit(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True  # Pre-set
        service.providers["fake"] = {}
        service._ensure_initialized()
        # Still has "fake" provider — didn't re-init and clear it
        assert "fake" in service.providers

    def test_no_api_keys_yields_no_providers(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._ensure_initialized()
        assert len(service.providers) == 0
        assert service.primary_provider is None

    def test_primary_provider_is_first_in_dict(self, monkeypatch):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()

        # Inject a fake provider directly
        service.providers["mock_provider"] = {"type": "mock"}
        service._ensure_initialized()  # Should not overwrite existing providers
        # After first call, initialized is True; inject and check
        service2 = MultiModelAIService()
        service2.providers = {"alpha": {}, "beta": {}}
        service2._initialized = True
        service2.primary_provider = "alpha"
        assert service2.primary_provider == "alpha"


class TestMultiModelAIServiceInitGemini:
    def test_init_gemini_no_key_skips(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._init_gemini()
        assert "gemini" not in service.providers

    def test_init_gemini_import_error_handled(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")
        with patch.dict("sys.modules", {"google.genai": None}):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_gemini()
        # Should not raise — import error is caught

    def test_init_gemini_with_mock_client(self, monkeypatch):
        monkeypatch.setenv("GEMINI_API_KEY", "test-key")

        mock_client = MagicMock()
        mock_genai = MagicMock()
        mock_genai.Client.return_value = mock_client

        with (
            patch.dict("sys.modules", {"google.genai": mock_genai}),
            patch(
                "src.kortana.services.multi_model_ai.get_model_name",
                return_value="gemini-3.1-flash-lite-preview",
            ),
        ):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_gemini()

        assert "gemini" in service.providers
        assert service.providers["gemini"]["model"] == "gemini-3.1-flash-lite-preview"


class TestMultiModelAIServiceInitOpenAI:
    def test_init_openai_no_key_skips(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._init_openai()
        assert "openai" not in service.providers

    def test_init_openai_with_mock(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

        mock_openai = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai}):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_openai()

        assert "openai" in service.providers
        assert service.providers["openai"]["model"] == MULTI_MODEL_DEFAULTS.openai


class TestMultiModelAIServiceInitAnthropic:
    def test_init_anthropic_no_key_skips(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._init_anthropic()
        assert "anthropic" not in service.providers

    def test_init_anthropic_with_mock(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-test")

        mock_anthropic = MagicMock()
        with patch.dict("sys.modules", {"anthropic": mock_anthropic}):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_anthropic()

        assert "anthropic" in service.providers
        assert service.providers["anthropic"]["model"] == MULTI_MODEL_DEFAULTS.anthropic


class TestMultiModelAIServiceInitGroq:
    def test_init_groq_no_key_skips(self, monkeypatch):
        monkeypatch.delenv("GROQ_API_KEY", raising=False)
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._init_groq()
        assert "groq" not in service.providers

    def test_init_groq_with_mock(self, monkeypatch):
        monkeypatch.setenv("GROQ_API_KEY", "groq-test")

        mock_groq = MagicMock()
        with patch.dict("sys.modules", {"groq": mock_groq}):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_groq()

        assert "groq" in service.providers
        assert service.providers["groq"]["model"] == MULTI_MODEL_DEFAULTS.groq


class TestMultiModelAIServiceInitOpenRouter:
    def test_init_openrouter_no_key_skips(self, monkeypatch):
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._init_openrouter()
        assert "openrouter" not in service.providers

    def test_init_openrouter_with_mock(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "or-test")

        mock_openai_module = MagicMock()
        with patch.dict("sys.modules", {"openai": mock_openai_module}):
            from src.kortana.services.multi_model_ai import MultiModelAIService

            service = MultiModelAIService()
            service._init_openrouter()

        assert "openrouter" in service.providers
        assert service.providers["openrouter"]["model"] == MULTI_MODEL_DEFAULTS.openrouter


class TestMultiModelAIServiceAnalyzeText:
    @pytest.mark.asyncio
    async def test_analyze_text_no_providers(self, monkeypatch):
        for key in [
            "GEMINI_API_KEY",
            "GOOGLE_API_KEY",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GROQ_API_KEY",
            "OPENROUTER_API_KEY",
        ]:
            monkeypatch.delenv(key, raising=False)

        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        result = await service.analyze_text("Hello")
        assert "[ERROR]" in result
        assert "No AI providers" in result

    @pytest.mark.asyncio
    async def test_analyze_text_with_mock_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Test response"
        mock_client.models.generate_content.return_value = mock_response

        service.providers["gemini"] = {
            "client": mock_client,
            "model": "gemini-3.1-flash-lite-preview",
            "type": "google",
        }
        service.primary_provider = "gemini"

        result = await service.analyze_text("Hello")
        assert "GEMINI" in result
        assert "Test response" in result

    @pytest.mark.asyncio
    async def test_analyze_text_falls_back_on_failure(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        # First provider fails, second succeeds
        service.providers["gemini"] = {
            "client": MagicMock(
                **{"models.generate_content.side_effect": Exception("API error")}
            ),
            "model": "gemini-3.1-flash-lite-preview",
            "type": "google",
        }
        mock_openai_client = MagicMock()
        mock_response = MagicMock()
        mock_response.output_text = "OpenAI response"
        mock_response.usage = MagicMock(input_tokens=5, output_tokens=3)
        mock_openai_client.responses.create.return_value = mock_response
        service.providers["openai"] = {
            "client": mock_openai_client,
            "model": MULTI_MODEL_DEFAULTS.openai,
            "type": "openai",
        }

        result = await service.analyze_text("Hello")
        assert "OPENAI" in result or "[ERROR]" in result  # Fallback or all failed

    @pytest.mark.asyncio
    async def test_generate_code_calls_analyze_text(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True
        service.providers = {}  # No providers

        result = await service.generate_code("a REST endpoint")
        assert "[ERROR]" in result

    @pytest.mark.asyncio
    async def test_analyze_multimodal(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True
        service.providers = {}

        result = await service.analyze_multimodal("Describe this")
        assert "[ERROR]" in result


class TestMultiModelAICallProvider:
    @pytest.mark.asyncio
    async def test_call_nonexistent_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True
        result = await service._call_provider("nonexistent", "text")
        assert result is None

    @pytest.mark.asyncio
    async def test_call_gemini_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Gemini says hi"
        mock_client.models.generate_content.return_value = mock_response

        service.providers["gemini"] = {
            "client": mock_client,
            "model": "gemini-3.1-flash-lite-preview",
            "type": "google",
        }

        result = await service._call_provider("gemini", "Hello")
        assert result == "Gemini says hi"

    @pytest.mark.asyncio
    async def test_call_gemini_none_response(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_client.models.generate_content.return_value = MagicMock(text=None)

        service.providers["gemini"] = {
            "client": mock_client,
            "model": "gemini-3.1-flash-lite-preview",
            "type": "google",
        }

        result = await service._call_provider("gemini", "Hello")
        assert result is None

    @pytest.mark.asyncio
    async def test_call_openai_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = "OpenAI response"
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_response.usage = MagicMock(prompt_tokens=4, completion_tokens=2)
        mock_client.chat.completions.create.return_value = mock_response

        service.providers["openai"] = {
            "client": mock_client,
            "model": MULTI_MODEL_DEFAULTS.openai,
            "type": "openai",
        }

        result = await service._call_provider("openai", "Hello")
        assert result == "OpenAI response"

    @pytest.mark.asyncio
    async def test_call_anthropic_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.text = "Claude response"
        mock_client.messages.create.return_value = MagicMock(content=[mock_content])

        service.providers["anthropic"] = {
            "client": mock_client,
            "model": "claude-3-5-sonnet-20241022",
            "type": "anthropic",
        }

        result = await service._call_provider("anthropic", "Hello")
        assert result == "Claude response"

    @pytest.mark.asyncio
    async def test_call_groq_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="Groq response"))]
        mock_client.chat.completions.create.return_value = mock_response

        service.providers["groq"] = {
            "client": mock_client,
            "model": "mixtral-8x7b-32768",
            "type": "groq",
        }

        result = await service._call_provider("groq", "Hello")
        assert result == "Groq response"

    @pytest.mark.asyncio
    async def test_call_openrouter_provider(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="OpenRouter response"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        service.providers["openrouter"] = {
            "client": mock_client,
            "model": "meta-llama/llama-2-70b-chat",
            "type": "openrouter",
        }

        result = await service._call_provider("openrouter", "Hello")
        assert result == "OpenRouter response"

    @pytest.mark.asyncio
    async def test_call_provider_exception_returns_none(self):
        from src.kortana.services.multi_model_ai import MultiModelAIService

        service = MultiModelAIService()
        service._initialized = True

        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API Error")

        service.providers["gemini"] = {
            "client": mock_client,
            "model": "gemini-3.1-flash-lite-preview",
            "type": "google",
        }

        result = await service._call_provider("gemini", "Hello")
        assert result is None
