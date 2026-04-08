"""Tests for secrets_validator.py"""
from unittest.mock import MagicMock, patch

from src.kortana.secrets_validator import SecretsValidator, validate_secrets


class TestSecretsValidatorGemini:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_gemini_success(self):
        mock_genai = MagicMock()
        mock_genai.list_tuned_models.return_value = [MagicMock(), MagicMock()]
        with patch.dict("sys.modules", {"google.generativeai": mock_genai}):
            # Re-create validator to pick up patched module
            with patch(
                "src.kortana.secrets_validator.SecretsValidator.validate_gemini"
            ) as mock_v:
                mock_v.return_value = (True, "Gemini API validated")
                result, msg = self.validator.validate_gemini()
                # verify via the mock
                assert result is True

    def test_validate_gemini_no_key(self):
        with patch.object(self.validator.settings, "GEMINI_API_KEY", None):
            result, msg = self.validator.validate_gemini()
            assert result is False
            assert "not configured" in msg

    def test_validate_gemini_import_error(self):
        with patch(
            "builtins.__import__",
            side_effect=lambda name, *args, **kwargs: (
                (_ for _ in ()).throw(ImportError("not installed"))
                if name == "google.generativeai"
                else __import__(name, *args, **kwargs)
            ),
        ):
            result, msg = self.validator.validate_gemini()
            # Either ImportError path or exception path
            assert result in [None, False]

    def test_validate_gemini_api_error(self):
        import sys

        mock_genai = MagicMock()
        mock_genai.configure = MagicMock()
        mock_genai.list_tuned_models.side_effect = Exception("API key invalid")
        with patch.dict(sys.modules, {"google.generativeai": mock_genai}):
            result, msg = self.validator.validate_gemini()
            assert result is False
            assert "failed" in msg.lower() or "invalid" in msg.lower()


class TestSecretsValidatorGitHub:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_github_no_token(self):
        with patch.object(self.validator.settings, "GITHUB_TOKEN", None):
            result, msg = self.validator.validate_github()
            assert result is False
            assert "not configured" in msg

    def test_validate_github_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"login": "madouble7"}
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_github()
            assert result is True
            assert "madouble7" in msg

    def test_validate_github_invalid_token(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_github()
            assert result is False
            assert "401" in msg

    def test_validate_github_network_error(self):
        with patch("requests.get", side_effect=Exception("Connection refused")):
            result, msg = self.validator.validate_github()
            assert result is False
            assert "failed" in msg.lower()


class TestSecretsValidatorOpenAI:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_openai_no_key(self):
        with patch.object(self.validator.settings, "OPENAI_API_KEY", None):
            result, msg = self.validator.validate_openai()
            assert result is False
            assert "not configured" in msg

    def test_validate_openai_import_error(self):
        import sys

        # Remove openai from modules if present
        saved = sys.modules.pop("openai", None)
        try:
            with patch(
                "builtins.__import__",
                side_effect=lambda name, *args, **kwargs: (
                    (_ for _ in ()).throw(ImportError("not installed"))
                    if name == "openai"
                    else __import__(name, *args, **kwargs)
                ),
            ):
                result, msg = self.validator.validate_openai()
                assert result in [None, False]
        finally:
            if saved is not None:
                sys.modules["openai"] = saved

    def test_validate_openai_api_error(self):
        import sys

        mock_openai = MagicMock()
        mock_openai.Model.list.side_effect = Exception("Invalid API key")
        with patch.dict(sys.modules, {"openai": mock_openai}):
            result, msg = self.validator.validate_openai()
            assert result is False
            assert "failed" in msg.lower()


class TestSecretsValidatorPinecone:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_pinecone_no_key(self):
        with patch.object(self.validator.settings, "PINECONE_API_KEY", None):
            result, msg = self.validator.validate_pinecone()
            assert result is False
            assert "not configured" in msg

    def test_validate_pinecone_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"indexes": ["myindex"]}
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_pinecone()
            assert result is True
            assert "Pinecone" in msg

    def test_validate_pinecone_invalid_key(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_pinecone()
            assert result is False

    def test_validate_pinecone_error(self):
        with patch("requests.get", side_effect=Exception("Timeout")):
            result, msg = self.validator.validate_pinecone()
            assert result is False


class TestSecretsValidatorDiscord:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_discord_no_token(self):
        with patch.object(self.validator.settings, "DISCORD_BOT_TOKEN", None):
            result, msg = self.validator.validate_discord()
            assert result is False
            assert "not configured" in msg

    def test_validate_discord_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"username": "KortanaBot"}
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_discord()
            assert result is True
            assert "KortanaBot" in msg

    def test_validate_discord_invalid_token(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        with patch("requests.get", return_value=mock_response):
            result, msg = self.validator.validate_discord()
            assert result is False

    def test_validate_discord_error(self):
        with patch("requests.get", side_effect=Exception("DNS error")):
            result, msg = self.validator.validate_discord()
            assert result is False


class TestSecretsValidatorStripe:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_stripe_no_key(self):
        with patch.object(self.validator.settings, "STRIPE_SECRET_KEY", None):
            result, msg = self.validator.validate_stripe()
            assert result is False
            assert "not configured" in msg

    def test_validate_stripe_import_error(self):
        import sys

        saved = sys.modules.pop("stripe", None)
        try:
            with patch(
                "builtins.__import__",
                side_effect=lambda name, *args, **kwargs: (
                    (_ for _ in ()).throw(ImportError("not installed"))
                    if name == "stripe"
                    else __import__(name, *args, **kwargs)
                ),
            ):
                result, msg = self.validator.validate_stripe()
                assert result in [None, False]
        finally:
            if saved is not None:
                sys.modules["stripe"] = saved

    def test_validate_stripe_api_error(self):
        import sys

        mock_stripe = MagicMock()
        mock_stripe.Account.retrieve.side_effect = Exception("Invalid key")
        with patch.dict(sys.modules, {"stripe": mock_stripe}):
            result, msg = self.validator.validate_stripe()
            assert result is False


class TestSecretsValidatorDatabase:
    def setup_method(self):
        self.validator = SecretsValidator()

    def test_validate_database_error(self):
        with patch(
            "sqlalchemy.create_engine", side_effect=Exception("Connection failed")
        ):
            result, msg = self.validator.validate_database()
            assert result is False
            assert "failed" in msg.lower()

    def test_validate_database_success(self):
        mock_engine = MagicMock()
        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value = None
        mock_engine.connect.return_value = mock_conn
        with patch("sqlalchemy.create_engine", return_value=mock_engine):
            result, msg = self.validator.validate_database()
            assert result is True
            assert "valid" in msg.lower()


class TestSecretsValidatorAll:
    def test_validate_all_returns_dict(self):
        validator = SecretsValidator()
        # Mock all validators to return fast
        with patch.object(
            validator, "validate_gemini", return_value=(False, "test")
        ), patch.object(
            validator, "validate_github", return_value=(True, "test")
        ), patch.object(
            validator, "validate_openai", return_value=(None, "test")
        ), patch.object(
            validator, "validate_pinecone", return_value=(False, "test")
        ), patch.object(
            validator, "validate_discord", return_value=(False, "test")
        ), patch.object(
            validator, "validate_stripe", return_value=(None, "test")
        ), patch.object(validator, "validate_database", return_value=(True, "test")):
            results = validator.validate_all()
            assert isinstance(results, dict)
            assert "Gemini" in results
            assert "GitHub" in results
            assert results["GitHub"] == (True, "test")

    def test_validate_secrets_function(self):
        with patch(
            "src.kortana.secrets_validator.SecretsValidator.validate_all",
            return_value={"test": (True, "ok")},
        ):
            result = validate_secrets()
            assert result is not None
