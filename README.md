# Kor'tana

The Warchief's AI companion.

## Project Structure

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

## Setup and Installation

1. Create a virtual environment:
   ```bash
   python -m venv venv311
   ```

2. Activate the virtual environment:

   Windows:
   ```bash
   venv311\Scripts\activate
   ```

   Linux/Mac:
   ```bash
   source venv311/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install pyyaml apscheduler pydantic
   ```

4. Set up the directory structure and placeholder configs:
   ```bash
   python scripts/setup_and_run_batch1.py
   ```

## Running Kor'tana

Start the main system:
```bash
python -m src.kortana.core.brain
```

Or use the convenience scripts:

Windows:
```
run_kortana.bat
```

PowerShell:
```
.\Run-Kortana.ps1
```

## Features

- **Lowercase Love**: All inputs and outputs are transformed to lowercase
- **Memory System**: Conversation history and important information is stored for context
- **Autonomous Agents**: Specialized agents for coding, planning, testing, and monitoring
- **Covenant Enforcement**: Responses are checked against the covenant for alignment with values

## Development

### Running Tests
```bash
python -m pytest tests
```

### Code Style
This project uses Black for formatting and Pylint for linting.
