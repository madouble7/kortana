"""
AI-Assisted Development Helper for Kor'tana
Use local AI models from AI Toolkit to help with development tasks
"""


class AIAssistedDevelopment:
    """
    Helper class to structure prompts for AI models to assist with Kor'tana development
    Copy these prompts to your AI Toolkit Playground to get help with specific tasks
    """

    @staticmethod
    def get_code_review_prompt(code_snippet: str, file_path: str = "") -> str:
        """Generate prompt for AI to review Kor'tana code"""
        return f"""
You are a senior Python developer reviewing code for Kor'tana, an AI assistant that embodies wisdom, compassion, and truth.

File: {file_path}
Code to review:
```python
{code_snippet}
```

Please review this code for:
1. **Bugs or potential issues**
2. **Performance optimizations**
3. **Code quality improvements**
4. **Alignment with Kor'tana's principles** (wisdom, compassion, truth)
5. **Security considerations**

Provide specific, actionable feedback with code examples where helpful.
"""

    @staticmethod
    def get_feature_design_prompt(feature_description: str) -> str:
        """Generate prompt for AI to help design new Kor'tana features"""
        return f"""
You are an AI architecture consultant helping design features for Kor'tana.

Kor'tana's Core Principles:
- **Wisdom**: Thoughtful, well-reasoned responses
- **Compassion**: Empathetic and caring interactions
- **Truth**: Accurate, honest, and transparent

Feature Request: {feature_description}

Please provide:
1. **High-level architecture** for this feature
2. **Key components/classes** needed
3. **Integration points** with existing Kor'tana systems
4. **Potential challenges** and solutions
5. **How this aligns** with Kor'tana's principles

Format as a detailed technical design document.
"""

    @staticmethod
    def get_debugging_prompt(error_message: str, code_context: str = "") -> str:
        """Generate prompt for AI to help debug Kor'tana issues"""
        return f"""
You are debugging an issue in Kor'tana, an AI assistant system.

Error Message:
{error_message}

Code Context:
```python
{code_context}
```

Please help by:
1. **Explaining the likely cause** of this error
2. **Providing a step-by-step solution**
3. **Suggesting preventive measures** to avoid this in the future
4. **Recommending testing strategies** to catch similar issues

Focus on solutions that maintain Kor'tana's reliability and user trust.
"""

    @staticmethod
    def get_documentation_prompt(code_snippet: str, purpose: str = "") -> str:
        """Generate prompt for AI to create documentation"""
        return f"""
Create comprehensive documentation for this Kor'tana component.

Purpose: {purpose}

Code:
```python
{code_snippet}
```

Please provide:
1. **Clear description** of what this code does
2. **Usage examples** with realistic scenarios
3. **Parameter explanations** for all functions/methods
4. **Return value descriptions**
5. **Integration notes** for other Kor'tana components

Write in a clear, professional style that helps other developers understand and use this code effectively.
"""


# Example usage prompts for different Kor'tana development tasks
DEVELOPMENT_PROMPTS = {
    "brain_enhancement": """
Help me improve Kor'tana's ChatEngine (brain.py) to better handle:
- Multi-turn conversations with context retention
- Emotional intelligence in responses
- Integration with multiple LLM providers
- Memory management for long conversations

What architectural patterns would you recommend?
""",
    "memory_system": """
Design a memory system for Kor'tana that can:
- Store conversation history efficiently
- Retrieve relevant context for current conversations
- Handle different types of memory (short-term, long-term, episodic)
- Scale with growing usage

Consider both technical implementation and privacy/security aspects.
""",
    "llm_integration": """
Help me create a robust LLM client system for Kor'tana that:
- Supports multiple providers (OpenAI, Google, Anthropic, local models)
- Handles failover between providers
- Manages rate limiting and costs
- Provides consistent interfaces regardless of provider

What design patterns would work best?
""",
    "testing_strategy": """
Design a comprehensive testing strategy for Kor'tana that covers:
- Unit tests for individual components
- Integration tests for LLM interactions
- End-to-end conversation testing
- Performance and reliability testing

How should we test AI components that have non-deterministic outputs?
""",
}

if __name__ == "__main__":
    # Example: Generate a code review prompt
    sample_code = """
def process_user_message(self, message: str) -> str:
    response = self.llm_client.generate_response(message)
    return response
"""

    helper = AIAssistedDevelopment()
    prompt = helper.get_code_review_prompt(sample_code, "src/brain.py")

    print("=" * 60)
    print("COPY THIS PROMPT TO YOUR AI TOOLKIT PLAYGROUND:")
    print("=" * 60)
    print(prompt)
