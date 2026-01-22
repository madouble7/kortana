# KOR'TANA

Kor'tana is a highly autonomous AI agent and sacred companion with memory, ethical discernment, and context-aware responses.

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
├── logs/             # Active log files
├── scripts/          # Utility scripts
│   ├── tests/        # Test scripts
│   ├── checks/       # System check scripts
│   ├── monitoring/   # System monitoring scripts
│   ├── launchers/    # Application launchers
│   └── utilities/    # General utility scripts
├── archive/          # Archive of old files
│   ├── logs/         # Old log files
│   ├── reports/      # Old reports and outputs
│   ├── batches/      # Batch processing results
│   └── obsolete/     # Deprecated code
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

- **Memory System**: Stores and retrieves memories with semantic search capabilities
- **Ethical Discernment**: Evaluates responses for algorithmic arrogance and uncertainty
- **Context-Aware Responses**: Integrates memory and ethical considerations in responses
- **LLM Integration**: Uses OpenAI's GPT models for natural language processing
- **LobeChat Frontend Support**: Seamlessly integrates with LobeChat for a user-friendly interface
- **Dify Platform Integration**: Connect with Dify for no-code prompt engineering and workflow automation

## Frontend Integrations

Kor'tana supports multiple frontend options for flexible deployment:

### LobeChat Integration

Kor'tana integrates with [LobeChat](https://github.com/lobehub/lobe-chat) to provide an intuitive chat interface.

#### Setting Up LobeChat Connection

1. Follow the guide in `docs/LOBECHAT_CONNECTION.md` to configure LobeChat.
2. Set your API key in the `.env` file.
3. Run the Kor'tana API server.

For troubleshooting, see `docs/LOBECHAT_TROUBLESHOOTING.md`.

### Dify Platform Integration

Kor'tana integrates with [Dify](https://dify.ai) for advanced no-code LLM application development.

#### Key Dify Features

- **No-code prompt engineering** - Design and test prompts visually
- **Workflow automation** - Build complex AI workflows
- **Multi-model support** - Switch between LLM providers easily
- **Agent orchestration** - Create autonomous AI agents

#### Quick Start with Dify

1. Add Dify configuration to your `.env` file (see `.env.example`)
2. Start Kor'tana server: `python -m uvicorn src.kortana.main:app --reload`
3. Configure Dify to use Kor'tana as a custom model provider
4. For detailed setup: `docs/DIFY_INTEGRATION.md`

## Documentation

- Full API documentation: `docs/API_ENDPOINTS.md`
- Architecture overview: `docs/ARCHITECTURE.md`
- Memory Core details: `docs/MEMORY_CORE.md`
- LobeChat integration: `docs/LOBECHAT_CONNECTION.md`
- LobeChat troubleshooting: `docs/LOBECHAT_TROUBLESHOOTING.md`
- Dify platform integration: `docs/DIFY_INTEGRATION.md`

## Development

### Running Tests
```bash
python -m pytest tests
```

### Code Style
This project uses Black for formatting and Pylint for linting.

## Core Components

- **Memory Core**: Stores, retrieves, and manages memories
- **Reasoning Core**: Processes user queries and generates responses
- **Ethical Discernment Module**: Ensures responses are ethical and reflective
- **API Adapters**: Connect to frontend interfaces (including LobeChat)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Directory Structure

This section describes the main directories in the project.

### Core Directories

- **`/src`**: Contains the main Kor'tana source code.
- **`/data`**: Contains runtime data generated by Kor'tana.
- **`/tests`**: Contains dedicated unit and integration tests.
- **`/docs`**: Project documentation.
- **`/config`**: Configuration files.

### Utility Directories

- **`/scripts`**: Contains all utility scripts organized as follows:
  - **`/scripts/tests`**: Test scripts and runners
  - **`/scripts/checks`**: System check and validation scripts
  - **`/scripts/monitoring`**: System monitoring scripts
  - **`/scripts/launchers`**: Application launchers
  - **`/scripts/utilities`**: General utility scripts including PS1/BAT files

### Storage & Runtime Directories

- **`/archive`**: Stores old files organized as follows:
  - **`/archive/logs`**: Old log files
  - **`/archive/reports`**: Old reports, outputs, and status files
  - **`/archive/batches`**: Batch processing results
  - **`/archive/obsolete`**: Deprecated code
- **`/logs`**: Active log files (recent only)
- **`/state`**: Runtime state information.
- **`/vault`**: Sensitive configuration or data (if applicable).

### Database & Development Directories

- **`/alembic`**: Database migration scripts.
- **`/notebooks`**: Jupyter notebooks for exploration and analysis.
- **`/venv`**: Python virtual environment.

### Frontend Directories

- **`/node_modules`**: Frontend dependencies (for LobeChat frontend).
- **`/lobechat-frontend`**: LobeChat frontend source code.

## File Organization Guidelines

1. **Root Directory**: Keep the root directory clean. Do not add new scripts, logs, or temporary files here.
2. **New Scripts**: All new utility scripts should be placed in the appropriate subdirectory under `/scripts`.
3. **One-off Files**: If creating a temporary file or one-off script, place it in the appropriate subdirectory.
4. **Core Application Code**: Should only go in `/src`.
5. **Logs & Reports**: These should be stored in `/logs` while active, then moved to `/archive/logs` or `/archive/reports` when no longer needed.
