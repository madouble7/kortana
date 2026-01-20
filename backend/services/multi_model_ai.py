"""
Kor'tana Multi-Model AI Service
Supports: Gemini, OpenAI, Claude, OpenRouter, Groq with automatic fallback
"""

import os
from typing import Optional


class MultiModelAIService:
    """Service that intelligently selects from multiple AI providers"""

    def __init__(self):
        """Initialize all available AI services"""
        self.providers = {}
        self.primary_provider = None

        # Try to initialize each provider
        self._init_gemini()
        self._init_openai()
        self._init_anthropic()
        self._init_groq()
        self._init_openrouter()

        # Set primary (first available)
        if self.providers:
            self.primary_provider = list(self.providers.keys())[0]
            print("✅ Multi-Model Service initialized")
            print(f"   Available providers: {', '.join(self.providers.keys())}")
            print(f"   Primary: {self.primary_provider}")
        else:
            print("❌ No AI providers configured!")

    def _init_gemini(self):
        """Initialize Google Gemini"""
        try:
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            if not api_key:
                return

            from google.genai import Client

            client = Client(api_key=api_key)
            self.providers["gemini"] = {
                "client": client,
                "model": "gemini-2.0-flash-exp",
                "type": "google",
            }
            print("✅ Gemini provider initialized")
        except Exception as e:
            print(f"⚠️ Gemini initialization failed: {e}")

    def _init_openai(self):
        """Initialize OpenAI"""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return

            import openai

            openai.api_key = api_key
            self.providers["openai"] = {
                "client": openai,
                "model": "gpt-3.5-turbo",
                "type": "openai",
            }
            print("✅ OpenAI provider initialized")
        except Exception as e:
            print(f"⚠️ OpenAI initialization failed: {e}")

    def _init_anthropic(self):
        """Initialize Anthropic Claude"""
        try:
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                return

            import anthropic

            self.providers["anthropic"] = {
                "client": anthropic.Anthropic(api_key=api_key),
                "model": "claude-3-5-sonnet-20241022",
                "type": "anthropic",
            }
            print("✅ Anthropic Claude provider initialized")
        except Exception as e:
            print(f"⚠️ Anthropic initialization failed: {e}")

    def _init_groq(self):
        """Initialize Groq (fast inference)"""
        try:
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key:
                return

            import groq

            self.providers["groq"] = {
                "client": groq.Groq(api_key=api_key),
                "model": "mixtral-8x7b-32768",
                "type": "groq",
            }
            print("✅ Groq provider initialized")
        except Exception as e:
            print(f"⚠️ Groq initialization failed: {e}")

    def _init_openrouter(self):
        """Initialize OpenRouter (multi-model aggregator)"""
        try:
            api_key = os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                return

            import openai as openai_module

            self.providers["openrouter"] = {
                "client": openai_module.OpenAI(
                    api_key=api_key, base_url="https://openrouter.ai/api/v1"
                ),
                "model": "meta-llama/llama-2-70b-chat",
                "type": "openrouter",
            }
            print("✅ OpenRouter provider initialized")
        except Exception as e:
            print(f"⚠️ OpenRouter initialization failed: {e}")

    async def analyze_text(self, text: str, **kwargs) -> str:
        """Analyze text using best available provider with fallback"""
        if not self.providers:
            return "❌ No AI providers available"

        # Try each provider in order
        for provider_name in self.providers.keys():
            try:
                response = await self._call_provider(provider_name, text)
                if response:
                    return f"[{provider_name.upper()}] {response}"
            except Exception as e:
                print(f"⚠️ {provider_name} failed: {e}, trying next provider...")
                continue

        return "❌ All providers failed"

    async def _call_provider(self, provider_name: str, text: str) -> Optional[str]:
        """Call a specific provider"""
        provider = self.providers.get(provider_name)
        if not provider:
            return None

        try:
            # Gemini
            if provider_name == "gemini":
                response = provider["client"].models.generate_content(
                    model=f"models/{provider['model']}",
                    contents=text,
                )
                return response.text if response else None

            # OpenAI
            elif provider_name == "openai":
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": text}],
                    max_tokens=500
                )
                return response.choices[0].message.content if response.choices else None

            # Anthropic Claude
            elif provider_name == "anthropic":
                response = provider["client"].messages.create(
                    model=provider["model"],
                    max_tokens=500,
                    messages=[{"role": "user", "content": text}]
                )
                return response.content[0].text if response.content else None

            # Groq
            elif provider_name == "groq":
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": text}],
                    max_tokens=500
                )
                return response.choices[0].message.content if response.choices else None

            # OpenRouter
            elif provider_name == "openrouter":
                response = provider["client"].chat.completions.create(
                    model=provider["model"],
                    messages=[{"role": "user", "content": text}],
                    max_tokens=500
                )
                return response.choices[0].message.content if response.choices else None

        except Exception as e:
            print(f"Error calling {provider_name}: {e}")
            return None

        return None

    async def generate_code(self, description: str, **kwargs) -> str:
        """Generate code using best available provider"""
        prompt = f"Generate clean, production-ready code for: {description}"
        return await self.analyze_text(prompt, **kwargs)

    async def analyze_multimodal(self, text: str, files=None, **kwargs) -> str:
        """Analyze multimodal content"""
        return await self.analyze_text(text, **kwargs)


# Create global instance
try:
    ai_service = MultiModelAIService()
except Exception as e:
    print(f"❌ Failed to initialize MultiModelAIService: {e}")
    ai_service = None
