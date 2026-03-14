"""
Secrets Management & Validation Module
Handles loading, validation, and testing of all API credentials
"""

from config import get_settings


class SecretsValidator:
    """Validates and tests connectivity for all configured secrets"""

    def __init__(self):
        self.settings = get_settings()
        self.results = {}

    def validate_gemini(self) -> tuple[bool, str]:
        """Validate Google Gemini API key"""
        try:
            import google.generativeai as genai

            if not self.settings.GEMINI_API_KEY:
                return False, "GEMINI_API_KEY not configured"

            genai.configure(api_key=self.settings.GEMINI_API_KEY)
            # Try to list models to verify the key works
            models = genai.list_tuned_models()
            return True, f"✅ Gemini API validated - Models available: {len(list(models))}"
        except ImportError:
            return None, "⚠️  google-generativeai not installed (optional)"
        except Exception as e:
            return False, f"❌ Gemini validation failed: {str(e)}"

    def validate_github(self) -> tuple[bool, str]:
        """Validate GitHub token"""
        try:
            if not self.settings.GITHUB_TOKEN:
                return False, "GITHUB_TOKEN not configured"

            import requests

            headers = {"Authorization": f"token {self.settings.GITHUB_TOKEN}"}
            resp = requests.get("https://api.github.com/user", headers=headers, timeout=5)

            if resp.status_code == 200:
                user = resp.json()
                return True, f"✅ GitHub token valid - Authenticated as: {user.get('login')}"
            else:
                return False, f"❌ GitHub token invalid: {resp.status_code}"
        except Exception as e:
            return False, f"❌ GitHub validation failed: {str(e)}"

    def validate_openai(self) -> tuple[bool, str]:
        """Validate OpenAI API key"""
        try:
            if not self.settings.OPENAI_API_KEY:
                return False, "OPENAI_API_KEY not configured"

            import openai

            openai.api_key = self.settings.OPENAI_API_KEY
            models = openai.Model.list()
            return True, f"✅ OpenAI API validated - Models available: {len(models['data'])}"
        except ImportError:
            return None, "⚠️  openai not installed (optional)"
        except Exception as e:
            return False, f"❌ OpenAI validation failed: {str(e)}"

    def validate_pinecone(self) -> tuple[bool, str]:
        """Validate Pinecone API key"""
        try:
            if not self.settings.PINECONE_API_KEY:
                return False, "PINECONE_API_KEY not configured"

            import requests

            headers = {"Api-Key": self.settings.PINECONE_API_KEY}
            resp = requests.get(
                "https://api.pinecone.io/indexes",
                headers=headers,
                timeout=5,
            )

            if resp.status_code == 200:
                indexes = resp.json()
                return True, f"✅ Pinecone API validated - Indexes: {indexes.get('indexes', [])}"
            else:
                return False, f"❌ Pinecone token invalid: {resp.status_code}"
        except Exception as e:
            return False, f"❌ Pinecone validation failed: {str(e)}"

    def validate_discord(self) -> tuple[bool, str]:
        """Validate Discord bot token"""
        try:
            if not self.settings.DISCORD_BOT_TOKEN:
                return False, "DISCORD_BOT_TOKEN not configured"

            import requests

            headers = {"Authorization": f"Bot {self.settings.DISCORD_BOT_TOKEN}"}
            resp = requests.get("https://discordapp.com/api/users/@me", headers=headers, timeout=5)

            if resp.status_code == 200:
                user = resp.json()
                return True, f"✅ Discord bot token valid - Bot: {user.get('username')}"
            else:
                return False, f"❌ Discord token invalid: {resp.status_code}"
        except Exception as e:
            return False, f"❌ Discord validation failed: {str(e)}"

    def validate_stripe(self) -> tuple[bool, str]:
        """Validate Stripe API keys"""
        try:
            if not self.settings.STRIPE_SECRET_KEY:
                return False, "STRIPE_SECRET_KEY not configured"

            import stripe

            stripe.api_key = self.settings.STRIPE_SECRET_KEY
            account = stripe.Account.retrieve()
            return True, f"✅ Stripe API valid - Account: {account.get('id')}"
        except ImportError:
            return None, "⚠️  stripe not installed (optional)"
        except Exception as e:
            return False, f"❌ Stripe validation failed: {str(e)}"

    def validate_database(self) -> tuple[bool, str]:
        """Validate database connection"""
        try:
            import sqlalchemy

            engine = sqlalchemy.create_engine(
                self.settings.DATABASE_URL,
                connect_args={"timeout": 5},
            )
            with engine.connect() as conn:
                conn.execute(sqlalchemy.text("SELECT 1"))
                return (
                    True,
                    f"✅ Database connection valid - {self.settings.DB_HOST}:{self.settings.DB_PORT}",
                )
        except ImportError:
            return None, "⚠️  sqlalchemy not installed (optional)"
        except Exception as e:
            return False, f"❌ Database connection failed: {str(e)}"

    def validate_all(self) -> dict[str, tuple[bool, str]]:
        """Validate all configured secrets"""
        print("\n" + "=" * 70)
        print("🔐 SECRETS VALIDATION REPORT")
        print("=" * 70)

        validators = [
            ("Gemini", self.validate_gemini),
            ("GitHub", self.validate_github),
            ("OpenAI", self.validate_openai),
            ("Pinecone", self.validate_pinecone),
            ("Discord", self.validate_discord),
            ("Stripe", self.validate_stripe),
            ("Database", self.validate_database),
        ]

        results = {}
        for name, validator in validators:
            status, message = validator()
            results[name] = (status, message)
            print(f"\n{name}:")
            print(f"  {message}")

        print("\n" + "=" * 70)

        # Summary
        valid = sum(1 for status, _ in results.values() if status is True)
        invalid = sum(1 for status, _ in results.values() if status is False)
        optional = sum(1 for status, _ in results.values() if status is None)

        print(f"\nSummary: ✅ {valid} valid | ❌ {invalid} invalid | ⚠️  {optional} optional")
        print("=" * 70 + "\n")

        return results


def validate_secrets():
    """Quick validation function for CLI use"""
    validator = SecretsValidator()
    return validator.validate_all()


if __name__ == "__main__":
    validate_secrets()
