# Kor'tana VS Code Configuration Guide

## Overview
This document outlines the enhanced VS Code configuration for autonomous agent development in Project Kor'tana. The settings balance code quality, security, performance, and developer experience for AI agent collaboration.

## Configuration Structure

### 1. Global Settings
Located in your user settings, these provide the foundation for Python development.

### 2. Workspace Settings (`c:\kortana\.vscode\settings.json`)
Project-specific settings optimized for autonomous agent development.

### 3. Module-Specific Settings
- `src/agents/.vscode/settings.json` - Strict type checking for agent logic
- `src/core/.vscode/settings.json` - Enhanced safety for core components

## Key Enhancements for Agent Development

### 🧠 AI Agent/Autonomy Features

```json
{
    "python.analysis.memory.keepLibraryAst": true,
    "python.analysis.useLibraryCodeForTypes": true,
    "python.envFile": "${workspaceFolder}/.env",
    "editor.formatOnPaste": true,
    "editor.stickyScroll.enabled": true
}
```

**Benefits:**
- Enhanced IntelliSense for agent-generated code
- Automatic formatting of LLM-generated snippets
- Secure environment variable management
- Better navigation in large agent-generated files

### 🚦 File Management for Agent Output

```json
{
    "files.exclude": {
        "agent_output/*": false,
        "logs/agent_traces/*": false
    },
    "files.watcherExclude": {
        "**/logs/agent_traces/**": false
    },
    "files.associations": {
        "*.agent_log": "log",
        "*.trace": "log",
        "*.memory": "json",
        "*.plan": "yaml"
    }
}
```

**Benefits:**
- Agent-generated files are visible and tracked
- Proper syntax highlighting for agent artifacts
- Optimized file watching for dynamic content

### 🛡️ Security & Environment Management

```bash
# .env.template provides secure configuration
OPENAI_API_KEY=your_key_here
PINECONE_API_KEY=your_key_here
AGENT_LOG_LEVEL=INFO
```

**Benefits:**
- All secrets in environment variables
- Template-based configuration
- No accidental secret commits

### ⚡ Performance Optimizations

```json
{
    "python.analysis.packageIndexDepths": [
        {"name": "openai", "depth": 3},
        {"name": "langchain", "depth": 3},
        {"name": "pinecone", "depth": 3}
    ],
    "terminal.integrated.scrollback": 20000
}
```

**Benefits:**
- Deep IntelliSense for AI libraries
- Extended terminal history for agent traces
- Optimized indexing for large codebases

### 🔍 Enhanced Type Checking

Core modules (`src/agents/`, `src/core/`) use strict type checking:

```json
{
    "python.analysis.typeCheckingMode": "strict",
    "python.linting.mypyEnabled": true
}
```

**Benefits:**
- Maximum safety for critical agent logic
- Early detection of type errors
- Better code documentation

## Directory Structure

```
c:\kortana\
├── .vscode\
│   └── settings.json          # Workspace settings
├── src\
│   ├── agents\
│   │   └── .vscode\
│   │       └── settings.json  # Strict typing for agents
│   └── core\
│       └── .vscode\
│           └── settings.json  # Strict typing for core
├── logs\
│   ├── agent_traces\          # Agent execution logs
│   └── memory_traces\         # Memory system logs
├── agent_output\              # Agent-generated files
├── .env.template              # Environment configuration template
└── .env                       # Your actual environment (git-ignored)
```

## Setup Instructions

1. **Copy Environment Template:**
   ```cmd
   copy .env.template .env
   ```

2. **Fill in API Keys:**
   Edit `.env` with your actual API keys and configuration.

3. **Install Python Dependencies:**
   ```cmd
   pip install mypy ruff pytest-cov
   ```

4. **Verify Configuration:**
   - Open VS Code in the `c:\kortana` directory
   - Check that Python interpreter points to `venv311/Scripts/python.exe`
   - Verify that intellisense works in agent files

## Agent Development Workflow

### 1. Agent Logging
Agents automatically log to `logs/agent_traces/` with structured format:

```python
import logging
logger = logging.getLogger(__name__)
logger.info("Agent decision: %s", decision_data)
```

### 2. Memory Tracing
Memory operations are tracked in `logs/memory_traces/`:

```python
from src.core.memory import save_decision
save_decision({"content": "Important choice"})
```

### 3. Code Generation
Agent-generated code is automatically formatted and type-checked:

- Format on paste handles LLM output
- Strict typing catches errors early
- File associations provide proper highlighting

## Troubleshooting

### Common Issues

1. **Import Errors:**
   - Verify `python.analysis.extraPaths` includes `./src`
   - Check that virtual environment is activated

2. **Type Checking Too Strict:**
   - Adjust `typeCheckingMode` from "strict" to "standard" in module settings
   - Use `# type: ignore` comments for legitimate edge cases

3. **Performance Issues:**
   - Reduce `packageIndexDepths` values
   - Exclude large directories in `files.watcherExclude`

4. **Agent Output Not Visible:**
   - Check `files.exclude` settings
   - Verify agent output directories exist

### Performance Monitoring

Monitor VS Code performance with agent development:

```cmd
# Check Python extension logs
code --list-extensions --show-versions | findstr python

# Monitor file watchers
# VS Code Developer Tools > Help > Toggle Developer Tools > Performance
```

## Best Practices

1. **Security:**
   - Never commit `.env` files
   - Use environment variables for all secrets
   - Regular API key rotation

2. **Code Quality:**
   - Let strict typing catch errors in core modules
   - Use format-on-save for consistency
   - Review agent-generated code carefully

3. **Performance:**
   - Monitor file watcher performance
   - Clean up old agent traces periodically
   - Use appropriate logging levels

4. **Agent Development:**
   - Structure agent output in dedicated directories
   - Use consistent logging formats
   - Document agent decision processes

## Future Enhancements

Planned improvements for agent development:

- [ ] Automated agent performance dashboards
- [ ] Real-time agent collaboration visualization
- [ ] Enhanced memory system observability
- [ ] CI/CD integration for agent testing
- [ ] Multi-workspace agent orchestration

---

This configuration provides a robust foundation for autonomous agent development while maintaining code quality and security standards.
