# Kor'tana

The Warchief's AI companion.

## 🔒 Infrastructure Status: LOCKED & READY ✅

**Database Infrastructure**: Fully operational and locked for feature development
**Migration Head**: df8dc2b048ef
**Validation Status**: All checks passed (5/5)
**Last Validated**: June 4, 2025

```cmd
# Quick validation check
python validate_infrastructure.py
```

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

## 🚀 Quick Setup

### Prerequisites
- Python 3.11+
- Git
- Virtual environment support

### Installation Steps

1. **Clone and Setup Environment**:
   ```cmd
   git clone <repository-url>
   cd project-kortana
   python -m venv venv311
   ```

2. **Activate Virtual Environment**:
   ```cmd
   # Windows
   venv311\Scripts\activate.bat

   # Linux/Mac
   source venv311/bin/activate
   ```

3. **Install Dependencies**:
   ```cmd
   pip install -e .
   ```

4. **Initialize Database**:
   ```cmd
   # Upgrade to latest schema
   C:\project-kortana\venv311\Scripts\alembic.exe upgrade head

   # Verify setup
   C:\project-kortana\venv311\Scripts\alembic.exe current
   ```

5. **Configure Environment**:
   Create `.env` file:
   ```env
   APP_NAME=kortana
   LOG_LEVEL=INFO
   MEMORY_DB_URL=sqlite:///./kortana_memory_dev.db
   OPENAI_API_KEY=your_key_here
   ANTHROPIC_API_KEY=your_key_here
   ```

6. **Start the Application**:
   ```cmd
   C:\project-kortana\venv311\Scripts\python.exe -m uvicorn src.kortana.main:app --reload
   ```

7. **Verify Installation**:
   - Visit `http://127.0.0.1:8000/health` for health check
   - Visit `http://127.0.0.1:8000/docs` for API documentation

> 📚 **Full Setup Guide**: See [`docs/GETTING_STARTED.md`](docs/GETTING_STARTED.md) for detailed instructions.

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
