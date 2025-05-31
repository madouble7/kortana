# Copilot Instructions for Kor'tana Project

## Project Overview

**Project Name:** Kor'tana
**Core Purpose:** A sacred interface and AI companion embodying Wisdom, Compassion, and Truth
**Repository:** c:\kortana

## Core Principles (The Trinity)

- **Wisdom:** Thoughtful, well-reasoned responses with deep understanding
- **Compassion:** Empathetic, caring, and supportive interactions
- **Truth:** Accurate, honest, and transparent communication

## Technology Stack

- **Language:** Python 3.11+
- **Primary LLM:** Google GenerativeAI (gemini-2.0-flash-lite, gemini-2.5-flash)
- **Environment:** VS Code, Windows 10/11
- **Virtual Environment:** venv311 (located at c:\kortana\venv311)
- **Key Dependencies:** google-generativeai==0.8.5, python-dotenv, requests, pydantic

## Project Structure

```
c:\kortana/
├── src/
│   ├── brain.py                 # Core ChatEngine
│   ├── llm_clients/
│   │   ├── factory.py          # LLM Client Factory
│   │   └── genai_client.py     # Google GenAI Client
│   └── utils/
├── config/
│   └── models_config.json      # Model configurations
├── .env                        # API keys (GOOGLE_API_KEY)
├── requirements.txt            # Dependencies
└── KORTANA_PROJECT_STATE_LIVE.md  # Primary PRD
```

## Key Components

### ChatEngine (src/brain.py)

- Main conversation handler
- Integrates with multiple LLM providers
- Manages context and memory
- Implements Trinity principles in responses

### LLM Clients (src/llm_clients/)

- `factory.py`: Creates appropriate client instances
- `genai_client.py`: Google GenerativeAI implementation
- Supports multiple providers with consistent interfaces

### Configuration (config/models_config.json)

- Model routing for different use cases
- Cost optimization settings
- Performance parameters

## Coding Conventions

- **Type Hints:** Always use type annotations
- **Error Handling:** Comprehensive try/catch with meaningful messages
- **Documentation:** Clear docstrings for all functions/classes
- **Logging:** Use structured logging for debugging
- **Testing:** Write unit tests for core functionality

## Current Development Focus

1. **Google GenAI Integration:** ✅ Completed - working with custom parameters
2. **Multi-Model Support:** Next priority
3. **Memory System:** Enhanced conversation context
4. **Emotional Intelligence:** Better user sentiment analysis
5. **Testing Framework:** Comprehensive test coverage

## Ethical Guidelines

- Prioritize user privacy and data security
- Maintain transparency about AI capabilities and limitations
- Ensure responses align with Trinity principles
- Implement safeguards against harmful content generation

## Common Tasks

- **Code Review:** Focus on wisdom, compassion, truth alignment
- **Feature Development:** Consider impact on all three principles
- **Bug Fixes:** Maintain reliability and user trust
- **Testing:** Validate both technical and ethical requirements

## API Keys & Environment

- Google GenAI API key stored in `.env` as `GOOGLE_API_KEY`
- Virtual environment: `c:\kortana\venv311`
- Activation: `venv311\Scripts\activate.bat`

## When Working on Kor'tana

1. Always consider how changes align with Wisdom, Compassion, Truth
2. Reference `KORTANA_PROJECT_STATE_LIVE.md` for current state
3. Use `models_config.json` for model selection guidance
4. Test with `test_genai.py` for Google GenAI functionality
5. Maintain user privacy and ethical AI practices
