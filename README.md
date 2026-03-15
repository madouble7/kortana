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

- **Cost-Aware Model Routing**: Intelligent AI model selection prioritizing free models (87% cost reduction)
  - 6+ free models via OpenRouter with automatic fallbacks
  - Smart task-based routing (reasoning, coding, creative, vision)
  - Real-time cost tracking and budget management
  - Response caching to eliminate redundant API calls
### Core Features
- **Memory System**: Stores and retrieves memories with semantic search capabilities
- **Ethical Discernment**: Evaluates responses for algorithmic arrogance and uncertainty
- **Context-Aware Responses**: Integrates memory and ethical considerations in responses
- **LLM Integration**: Uses OpenAI's GPT models for natural language processing
- **CopilotKit Frontend**: Modern React-based chat interface with AI assistance
- **LobeChat Frontend**: Modern, intuitive chat interface with OpenAI-compatible API
- **Multi-Model Support**: Intelligent routing between OpenAI, Anthropic, and Google AI models
- **LLM Integration**: Supports multiple AI providers (OpenAI, Google, Anthropic, xAI, OpenRouter)
- **LobeChat Frontend Support**: Seamlessly integrates with LobeChat for a user-friendly interface
- **Dify Platform Integration**: Connect with Dify for no-code prompt engineering and workflow automation

## Frontend Integrations

Kor'tana supports multiple frontend options for flexible deployment:

### LobeChat Integration
- **Open WebUI Integration**: Modern, feature-rich frontend with MCP (Model Context Protocol) support
- **MCP Protocol**: Extends LLM functionality with memory, goals, and context tools
- **AR/VR Exploration**: Comprehensive augmented and virtual reality capabilities for immersive simulations, real-world overlays, and spatial object management
- **Multimodal AI Capabilities**: Support for text, voice, images, video, and simulation-based queries
  - Text processing with context awareness
  - Voice/audio transcription and analysis
  - Image understanding with GPT-4 Vision
  - Video content processing
  - Simulation-based scenario analysis
  - Mixed multimodal prompts
- **AI-Powered Decision-Making**: ML-driven strategies for real-time autonomous decision-making
  - Neural network-based decision engine
  - Time-sensitive dataset analysis and trend detection
  - Outcome prediction with confidence scoring
  - Multi-objective optimization for optimal solutions
- **Advanced Security Module**: Comprehensive cybersecurity features including:
  - Real-time threat detection and prevention
  - Security alerts and monitoring
  - Vulnerability scanning and management
  - Advanced encryption utilities
  - Secure API communication
  - Security analytics dashboard

### New Features (2026)

1. **Multilingual Support**: Real-time translation and language detection for 10+ languages
2. **Emotional Intelligence**: Sentiment analysis and emotion detection to adapt responses
3. **Adaptive Content Generation**: Summarize, elaborate, or rewrite text in various styles
4. **Dynamic API Integration**: Plugin framework with built-in Weather, Stock, and Task Management plugins
5. **Ethical Transparency Dashboard**: Real-time logging and reporting of ethical decisions with user feedback
6. **Gaming Expansion**: Interactive storytelling engine and RPG assistant with dice rolling and NPC generation
7. **Community-Driven Marketplace**: Module discovery, submission, installation, and rating system

📚 **See [NEW_FEATURES.md](docs/NEW_FEATURES.md) for detailed documentation**  
🚀 **See [QUICK_START_NEW_FEATURES.md](docs/QUICK_START_NEW_FEATURES.md) for quick examples**

## Frontend Options

Kor'tana supports multiple frontend interfaces:

### Open WebUI (Recommended)
Modern, self-hosted UI with advanced features and MCP support.
- **Setup Guide**: [`docs/OPENWEBUI_INTEGRATION.md`](docs/OPENWEBUI_INTEGRATION.md)
- **Quick Start**: `./scripts/start_openwebui.sh` (Linux/Mac) or `scripts\start_openwebui.bat` (Windows)
- **Features**: MCP tools, memory access, goal management, streaming responses

### LobeChat Integration

Kor'tana also integrates with [LobeChat](https://github.com/lobehub/lobe-chat) to provide an intuitive chat interface.
Kor'tana seamlessly integrates with [LobeChat](https://github.com/lobehub/lobe-chat), providing a modern, feature-rich chat interface.

### Quick Start with LobeChat

**Using Docker Compose (Recommended)**:
```bash
# Copy environment template and add your API keys
cp .env.template .env
# Edit .env with your API keys

# Start both Kor'tana backend and LobeChat frontend
docker-compose up -d

# Access LobeChat at http://localhost:3210
# Access Kor'tana API at http://localhost:8000
```

**Or use the convenience script**:
```bash
# Linux/Mac
./start-lobechat-integration.sh

# Windows
start-lobechat-integration.bat
```

## Frontend Options

Kor'tana supports multiple frontend options to suit different needs:

### CopilotKit Integration (Recommended)

Kor'tana includes a built-in React frontend powered by CopilotKit, providing:
- Modern, customizable AI chat interface
- Seamless integration with Kor'tana's backend
- Real-time communication
- Easy deployment alongside the backend

**Quick Start:**
```bash
# Start the backend
python -m uvicorn src.kortana.main:app --reload

# In a new terminal, start the frontend
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` to access the CopilotKit interface.

For detailed setup and configuration, see [`docs/COPILOTKIT_INTEGRATION.md`](docs/COPILOTKIT_INTEGRATION.md).

### LobeChat Integration

Kor'tana also integrates with [LobeChat](https://github.com/lobehub/lobe-chat) for an alternative chat interface.

**Setting Up LobeChat Connection:**
### Configuration

#### Setting Up LobeChat Connection
1. Open LobeChat at http://localhost:3210
2. Go to Settings → Language Model
3. Add custom provider:
   - **Name**: Kor'tana
   - **Base URL**: `http://localhost:8000/v1`
   - **API Key**: (from your `.env` file)
4. Select model: `kortana-default` (recommended)

📋 **Quick Reference**: See [`LOBECHAT_QUICK_START.md`](LOBECHAT_QUICK_START.md) for commands and troubleshooting

For detailed setup instructions, troubleshooting, and advanced configuration, see:
- **Complete Guide**: [`docs/LOBECHAT_INTEGRATION_GUIDE.md`](docs/LOBECHAT_INTEGRATION_GUIDE.md)
- **Frontend Setup**: [`lobechat-frontend/README.md`](lobechat-frontend/README.md)
- **Legacy Connection Guide**: [`docs/LOBECHAT_CONNECTION.md`](docs/LOBECHAT_CONNECTION.md)
- **Troubleshooting**: [`docs/LOBECHAT_TROUBLESHOOTING.md`](docs/LOBECHAT_TROUBLESHOOTING.md)

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

- **LobeChat Integration** (Primary): [`docs/LOBECHAT_INTEGRATION_GUIDE.md`](docs/LOBECHAT_INTEGRATION_GUIDE.md)
- Full API documentation: `docs/API_ENDPOINTS.md`
- Architecture overview: `docs/ARCHITECTURE.md`
- Memory Core details: `docs/MEMORY_CORE.md`
- LobeChat legacy guide: `docs/LOBECHAT_CONNECTION.md`
- **Cost Optimization Guide**: `docs/COST_OPTIMIZATION.md` - Save up to 87% on AI costs
- **New Features**: `docs/NEW_FEATURES.md` - Comprehensive guide to all new features
- **Quick Start**: `docs/QUICK_START_NEW_FEATURES.md` - Quick examples and tutorials
- Full API documentation: `docs/API_ENDPOINTS.md`
- Architecture overview: `docs/ARCHITECTURE.md`
- Memory Core details: `docs/MEMORY_CORE.md`
- **Open WebUI integration**: `docs/OPENWEBUI_INTEGRATION.md`
- AR/VR Exploration: `docs/AR_VR_EXPLORATION.md`
- AI Decision-Making: `docs/AI_DECISION_MAKING.md`
- Security Module: `docs/SECURITY_MODULE.md`
- LobeChat integration: `docs/LOBECHAT_CONNECTION.md`
- LobeChat troubleshooting: `docs/LOBECHAT_TROUBLESHOOTING.md`
- Dify platform integration: `docs/DIFY_INTEGRATION.md`
- **Multimodal Capabilities**: `docs/MULTIMODAL_CAPABILITIES.md`
- **Multimodal Usage Examples**: `docs/MULTIMODAL_USAGE_EXAMPLES.md`
- **Multimodal API Reference**: `docs/MULTIMODAL_API_REFERENCE.md`
- **Multimodal Integration Guide**: `docs/MULTIMODAL_INTEGRATION_GUIDE.md`
- Multilingual support: `docs/MULTILINGUAL_SUPPORT.md`

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
- **AR/VR Exploration Module**: Provides immersive simulations and spatial interaction capabilities
- **Security Module**: Advanced cybersecurity features for system protection
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
