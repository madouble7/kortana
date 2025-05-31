#!/usr/bin/env python3
"""
Gemini Integration for Kor'tana
==============================

Provides AI-powered summarization using Google's Gemini 2.0 Flash model.
Handles token counting, context management, and API integration.

Usage:
    from gemini_integration import GeminiSummarizer
    summarizer = GeminiSummarizer(api_key="your_key")
    summary = summarizer.summarize(text, max_tokens=1000)
"""

from datetime import datetime
from typing import Any, Dict, Optional

import tiktoken

try:
    import google.generativeai as genai

    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    print("⚠️  google-generativeai not installed. Using mock summarization.")


class GeminiSummarizer:
    """AI-powered summarization using Gemini 2.0 Flash"""

    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"
    ):
        """Initialize Gemini summarizer"""
        self.api_key = api_key
        self.model_name = model_name
        self.encoding = tiktoken.get_encoding("cl100k_base")

        if GENAI_AVAILABLE and api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
            self.available = True
            print(f"✅ Gemini {model_name} initialized")
        else:
            self.available = False
            print("⚠️  Gemini not available - using mock summarization")

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))

    def summarize(self, text: str, max_tokens: int = 1000, context: str = "") -> str:
        """Summarize text using Gemini or fallback to mock"""
        if self.available and self.api_key:
            return self._summarize_with_gemini(text, max_tokens, context)
        else:
            return self._mock_summarize(text, max_tokens, context)

    def _summarize_with_gemini(self, text: str, max_tokens: int, context: str) -> str:
        """Actual Gemini API summarization"""
        try:
            prompt = self._build_summarization_prompt(text, max_tokens, context)

            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=0.1,  # Low temperature for consistent summaries
                ),
            )

            summary = response.text.strip()

            # Verify token count
            actual_tokens = self.count_tokens(summary)
            if actual_tokens > max_tokens * 1.2:  # 20% tolerance
                print(f"⚠️  Summary exceeded token limit: {actual_tokens}/{max_tokens}")
                # Truncate if needed
                words = summary.split()
                while self.count_tokens(" ".join(words)) > max_tokens and words:
                    words.pop()
                summary = " ".join(words) + "..."

            print(
                f"✅ Gemini summarization: {len(text)} → {len(summary)} chars ({actual_tokens} tokens)"
            )
            return summary

        except Exception as e:
            print(f"⚠️  Gemini API error: {e}")
            return self._mock_summarize(text, max_tokens, context)

    def _build_summarization_prompt(
        self, text: str, max_tokens: int, context: str
    ) -> str:
        """Build an effective summarization prompt"""
        prompt = f"""You are an AI assistant helping with agent communication summarization in the Kor'tana autonomous system.

TASK: Summarize the following agent communication history into exactly {max_tokens} tokens or less.

CONTEXT: {context if context else "General agent communication history"}

REQUIREMENTS:
- Preserve key decisions, actions, and outcomes
- Maintain chronological flow of important events
- Include any error states or critical issues
- Focus on actionable information and results
- Use concise, technical language
- Structure as bullet points for clarity

HISTORY TO SUMMARIZE:
{text}

SUMMARY (max {max_tokens} tokens):"""

        return prompt

    def _mock_summarize(self, text: str, max_tokens: int, context: str) -> str:
        """Fallback mock summarization"""
        lines = text.split("\n")

        # Extract timestamps and key patterns
        key_events = []
        for line in lines:
            line = line.strip()
            if any(
                keyword in line.lower()
                for keyword in ["error", "complete", "started", "failed", "success"]
            ):
                if len(line) > 100:
                    line = line[:97] + "..."
                key_events.append(line)

        # Build summary
        summary = f"MOCK SUMMARY ({context}):\n"
        summary += f"Period: {lines[0][:19] if lines else 'Unknown'} to {lines[-1][:19] if lines else 'Unknown'}\n"
        summary += f"Total messages: {len(lines)}\n"
        summary += f"Key events: {len(key_events)}\n\n"

        summary += "Key Events:\n"
        for event in key_events[-10:]:  # Last 10 key events
            summary += f"• {event}\n"

        # Ensure we don't exceed max_tokens
        while self.count_tokens(summary) > max_tokens and "\n" in summary:
            lines = summary.split("\n")
            summary = "\n".join(lines[:-1])

        actual_tokens = self.count_tokens(summary)
        print(
            f"🤖 Mock summarization: {len(text)} → {len(summary)} chars ({actual_tokens} tokens)"
        )

        return summary

    def summarize_agent_context(
        self, agent_name: str, messages: list, max_tokens: int = 1000
    ) -> Dict[str, Any]:
        """Summarize agent context with metadata"""

        # Combine messages into text
        text = "\n".join(
            [
                f"{msg.get('timestamp', '')}: {msg.get('content', str(msg))}"
                for msg in messages
            ]
        )

        context = f"Agent {agent_name} communication history"
        summary = self.summarize(text, max_tokens, context)

        return {
            "agent_name": agent_name,
            "summary": summary,
            "original_tokens": self.count_tokens(text),
            "summary_tokens": self.count_tokens(summary),
            "compression_ratio": round(
                self.count_tokens(text) / self.count_tokens(summary), 2
            ),
            "message_count": len(messages),
            "timestamp": datetime.now().isoformat(),
        }


def test_gemini_integration():
    """Test the Gemini integration"""
    print("🧪 Testing Gemini Integration...")

    # Create test data
    test_history = """
2025-05-30 14:00:00: Claude agent started task analysis
2025-05-30 14:01:15: Flash agent provided quick status check
2025-05-30 14:02:30: Weaver agent initiated coordination sequence
2025-05-30 14:03:45: Claude completed analysis with 3 recommendations
2025-05-30 14:04:00: Error in Flash agent - timeout occurred
2025-05-30 14:05:15: Weaver agent recovered from error state
2025-05-30 14:06:30: All agents synchronized successfully
2025-05-30 14:07:45: Task handoff completed to next cycle
"""

    # Test with mock (no API key)
    summarizer = GeminiSummarizer()
    summary = summarizer.summarize(
        test_history, max_tokens=200, context="Test agent coordination"
    )

    print("\n📝 Test Summary:")
    print(summary)
    print(f"\n📊 Tokens: {summarizer.count_tokens(summary)}")


if __name__ == "__main__":
    test_gemini_integration()
