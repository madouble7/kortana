"""
Content Generator for Kor'tana
Provides summarization, elaboration, and rewriting capabilities
"""

from enum import StrEnum


class ContentStyle(StrEnum):
    FORMAL = "formal"
    CASUAL = "casual"
    TECHNICAL = "technical"
    CREATIVE = "creative"
    PROFESSIONAL = "professional"


class ContentGenerator:
    """
    Service for adaptive content generation

    Note: This implementation uses simplified text processing.
    For production use, consider integrating NLP libraries or LLM-based
    generation for better quality results.
    """

    def summarize(self, text: str, max_length: int = 100) -> str:
        """
        Summarize text to specified maximum length

        Note: Uses simple sentence splitting. May not handle abbreviations
        or complex punctuation correctly.

        Args:
            text: Text to summarize
            max_length: Maximum length of summary in characters

        Returns:
            Summarized text
        """
        if not text or len(text) <= max_length:
            return text

        # Simple summarization: take first sentences up to max_length
        sentences = text.split(". ")
        summary = ""
        for sentence in sentences:
            if len(summary) + len(sentence) + 2 <= max_length:
                summary += sentence + ". "
            else:
                break

        if not summary:
            summary = text[:max_length] + "..."

        return summary.strip()

    def elaborate(self, text: str, target_length: int = 200) -> str:
        """
        Elaborate on text to reach target length

        Args:
            text: Text to elaborate
            target_length: Target length in characters

        Returns:
            Elaborated text
        """
        if not text:
            return text

        if len(text) >= target_length:
            return text

        # Simple elaboration: add context and explanation
        elaborated = (
            f"{text} This concept can be further understood by considering its "
            f"implications and applications in various contexts. "
            f"The underlying principles suggest a comprehensive approach "
            f"that takes into account multiple perspectives."
        )

        if len(elaborated) > target_length:
            return elaborated[:target_length]
        return elaborated

    def rewrite(
        self, text: str, style: ContentStyle = ContentStyle.PROFESSIONAL
    ) -> str:
        """
        Rewrite text in specified style

        Args:
            text: Text to rewrite
            style: Target writing style

        Returns:
            Rewritten text
        """
        if not text:
            return text

        # Simple style transformations
        if style == ContentStyle.FORMAL:
            return f"In formal terms: {text}"
        elif style == ContentStyle.CASUAL:
            return f"Simply put: {text}"
        elif style == ContentStyle.TECHNICAL:
            return f"From a technical perspective: {text}"
        elif style == ContentStyle.CREATIVE:
            return f"Imagine this: {text}"
        else:  # PROFESSIONAL
            return f"Professionally speaking: {text}"

    def adjust_for_industry(self, text: str, industry: str) -> str:
        """
        Adjust text for specific industry context

        Args:
            text: Text to adjust
            industry: Target industry (e.g., 'healthcare', 'finance', 'education')

        Returns:
            Industry-adjusted text
        """
        if not text:
            return text

        industry_contexts = {
            "healthcare": "In a healthcare context",
            "finance": "From a financial perspective",
            "education": "In educational terms",
            "technology": "From a technology standpoint",
            "legal": "In legal terms",
        }

        prefix = industry_contexts.get(
            industry.lower(), "In the context of " + industry
        )
        return f"{prefix}: {text}"

    def transform(
        self,
        text: str,
        operation: str = "summarize",
        **kwargs
    ) -> str:
        """
        Perform content transformation based on operation

        Args:
            text: Text to transform
            operation: Type of transformation ('summarize', 'elaborate', 'rewrite')
            **kwargs: Additional parameters for the operation

        Returns:
            Transformed text
        """
        if operation == "summarize":
            return self.summarize(text, kwargs.get("max_length", 100))
        elif operation == "elaborate":
            return self.elaborate(text, kwargs.get("target_length", 200))
        elif operation == "rewrite":
            style = kwargs.get("style", ContentStyle.PROFESSIONAL)
            if isinstance(style, str):
                style = ContentStyle(style)
            return self.rewrite(text, style)
        else:
            return text
