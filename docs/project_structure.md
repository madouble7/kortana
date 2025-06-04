# Kor'tana Project Structure

This document outlines the structure of the Kor'tana project.

## Directory Structure

```
kortana/
├── config/           # Configuration files
├── data/             # Data files
├── docs/             # Documentation
├── logs/             # Log files
├── scripts/          # Utility scripts
├── src/              # Source code
│   ├── kortana/      # Main Kor'tana package
│   │   ├── agents/   # Autonomous agents
│   │   ├── core/     # Core functionality
│   │   └── memory/   # Memory systems
│   └── llm_clients/  # LLM API clients
└── tests/            # Test suite
    ├── integration/  # Integration tests
    └── unit/         # Unit tests
```

## Key Components

### Configuration System

- **`config/default.yaml`**: Base configuration settings
- **`config/development.yaml`**: Development environment settings
- **`config/persona.json`**: Kor'tana's persona settings
- **`config/identity.json`**: Core identity settings
- **`config/models_config.json`**: LLM model configurations
- **`config/covenant.yaml`**: Guidelines and boundaries

The configuration system uses a layered approach, with default settings in `default.yaml` that can be overridden by environment-specific settings in `development.yaml` or `production.yaml`. Environment variables with the prefix `KORTANA_` can also override settings.

### Core Components

- **ChatEngine (`src/kortana/core/brain.py`)**: The central component that processes conversations
- **Memory System (`src/kortana/memory/`)**: Manages conversation history and important information
- **LLM Clients (`src/llm_clients/`)**: Interfaces with language models like GPT-4
- **Autonomous Agents (`src/kortana/agents/`)**: Specialized agents for specific tasks

### Autonomous Agents

- **CodingAgent**: Assists with coding tasks
- **PlanningAgent**: Helps with planning and organization
- **TestingAgent**: Supports testing and quality assurance
- **MonitoringAgent**: Monitors system health and performance

## Key Features

### Lowercase Love

All inputs and outputs are transformed to lowercase as part of Kor'tana's aesthetic. This is implemented in the `process_message` method of the `ChatEngine` class.

### Memory System

Kor'tana has both short-term and long-term memory:

- **Short-term memory**: Conversation context within a session
- **Long-term memory**: Important information stored across sessions

### Covenant Enforcement

All responses are checked against the covenant to ensure they align with Kor'tana's values and principles. This is handled by the `CovenantEnforcer` class.

## Development Workflow

1. **Setup**: Create a virtual environment and install dependencies
2. **Development**: Make changes to the codebase
3. **Testing**: Run unit and integration tests
4. **Running**: Start Kor'tana and interact with it

## Future Improvements

- **Enhanced Memory**: Implement more sophisticated memory retrieval
- **Additional Agents**: Create more specialized agents
- **Web Interface**: Add a web-based user interface
- **Voice Integration**: Add speech recognition and synthesis
