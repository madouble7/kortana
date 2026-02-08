# 🗣️ Kor'tana Chat Functionality Testing Guide

## Overview

This guide provides comprehensive information on testing Kor'tana's chat functionality. Tests have been created to validate core chat features including message processing, memory integration, and conversation flows.

---

## 📋 Test Files Created

### 1. **test_chat_functionality.py**
**Location:** `tests/test_chat_functionality.py`

Comprehensive pytest-based test suite covering:
- ChatEngine initialization and configuration
- Development chat interface (`KortanaDevChat`)
- Memory system integration
- Conversation history tracking
- Multi-turn conversations
- Session management
- Persona configuration
- Autonomy features
- Covenant integration
- End-to-end chat flows

**Key Test Classes:**
- `TestChatFunctionality` - Core functionality tests
- `TestChatIntegration` - Integration tests

**Run with:**
```bash
pytest tests/test_chat_functionality.py -v
```

### 2. **test_chat_interactive.py**
**Location:** `test_chat_interactive.py`

Interactive test runner with detailed output and manual chat demo capability.

**Features:**
- Tests all major chat components
- Clear pass/fail indicators
- Session summary statistics
- Optional interactive demo mode

**Run with:**
```bash
python test_chat_interactive.py
```

---

## 🧪 Test Coverage

### Chat Engine Tests
- ✅ Initialization with proper configuration
- ✅ Session ID assignment and management
- ✅ Multiple session isolation
- ✅ Custom session ID support
- ✅ Mode management (default, autonomous, etc.)
- ✅ Persona data loading
- ✅ Configuration validation

### Memory Integration Tests
- ✅ Memory storage and retrieval
- ✅ Chat history persistence
- ✅ Memory metadata handling
- ✅ Multi-turn conversation memory tracking

### Development Chat Interface Tests
- ✅ Chat initialization
- ✅ Message history tracking
- ✅ Command processing
- ✅ Session export to JSON
- ✅ Status reporting

### Conversation Flow Tests
- ✅ Message sending and receiving
- ✅ Multi-turn conversation handling
- ✅ Conversation context preservation
- ✅ Message ordering and timestamps

### Service Integration Tests
- ✅ LLM client availability
- ✅ Memory manager integration
- ✅ Planning engine availability
- ✅ Execution engine integration
- ✅ Covenant enforcer integration

---

## 🚀 Running Tests

### Method 1: Using pytest (Recommended)

#### Run all chat tests:
```bash
pytest tests/test_chat_functionality.py -v
```

#### Run specific test:
```bash
pytest tests/test_chat_functionality.py::TestChatFunctionality::test_chat_engine_initialization -v
```

#### Run with coverage:
```bash
pytest tests/test_chat_functionality.py -v --cov=src/kortana/core
```

### Method 2: Using Interactive Test Runner

```bash
python test_chat_interactive.py
```

This provides:
- Detailed status for each test
- Overall summary statistics
- Optional interactive chat demo
- Human-readable output

### Method 3: Using Batch File

```bash
run_chat_test.bat
```

Windows batch file that:
- Sets up Python environment
- Runs interactive tests
- Keeps output visible

### Method 4: Direct Python Execution

```bash
python test_chat_interactive.py
```

---

## 📊 Expected Test Results

When all tests pass, you should see:

```
✅ Dev Chat Interface - Chat engine created, history initialized, running state set
✅ ChatEngine - Engine initialized, session ID assigned, default mode, persona loaded
✅ Memory System - Memory stored, ID generated, memories retrieved
✅ Conversation Flow - All messages stored in chat, messages retrievable from memory
✅ Session Management - Different session IDs, custom session ID accepted

Total: 5/5 passed (100%)
```

---

## 🔧 Chat Functionality Components Being Tested

### 1. **ChatEngine** (`src/kortana/core/brain.py`)
- Core conversational processing
- Session management
- Integration with LLM services
- Memory system coordination
- Autonomous agent coordination

### 2. **KortanaDevChat** (`src/dev_chat_simple.py`)
- Terminal-based chat interface
- Command processing
- Session export
- Message history tracking

### 3. **MemoryManager** (`src/memory_manager.py`)
- Message persistence
- Memory retrieval and context
- Conversation history
- Metadata management

### 4. **Supporting Services**
- LLM Client Factory
- Model Router
- Execution Engine
- Planning Engine
- Covenant Enforcer

---

## 📝 Test Examples

### Example 1: Testing Chat Initialization

```python
from kortana.core.brain import ChatEngine
from kortana.config import load_config

settings = load_config()
engine = ChatEngine(settings)

# Verify initialization
assert engine.session_id is not None
assert engine.mode == "default"
assert engine.persona_data is not None
```

### Example 2: Testing Message Storage

```python
from memory_manager import MemoryManager

mm = MemoryManager("data/test.jsonl")
mem_id = mm.store_memory(
    role="user",
    content="Hello Kor'tana",
    metadata={"type": "greeting"}
)

memories = mm.retrieve_memories(limit=5)
assert any("Hello" in m.get("content", "") for m in memories)
```

### Example 3: Testing Dev Chat

```python
from dev_chat_simple import KortanaDevChat

chat = KortanaDevChat()

# Simulate conversation
chat.history.append({
    "role": "user",
    "content": "Test message",
    "timestamp": datetime.now()
})

assert len(chat.history) > 0
assert chat.history[0]["role"] == "user"
```

---

## ⚙️ Configuration Requirements

Before running tests, ensure:

1. **Python Environment**: Virtual environment at `c:\kortana\.kortana_config_test_env`
2. **Dependencies**: All packages installed (pytest, python-dotenv, etc.)
3. **Environment Variables**: `.env` file configured with API keys
4. **PYTHONPATH**: Set to include `src/` directory
5. **Data Directories**: `data/` folder exists for memory storage

---

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'kortana'"

**Solution:**
```bash
set PYTHONPATH=c:\kortana\src
# or in Python:
import sys
sys.path.insert(0, 'c:\\kortana\\src')
```

### Issue: "No module named 'memory_manager'"

**Solution:**
Ensure memory_manager.py is in `src/` directory and PYTHONPATH is set correctly.

### Issue: Tests timeout or hang

**Solution:**
- Some tests may require external API calls
- Use `-k` flag to skip specific tests
- Run with `--tb=short` for shorter tracebacks

### Issue: Memory/JSON file conflicts

**Solution:**
Tests use separate test files (e.g., `data/test_chat_*.jsonl`). Remove old ones:
```bash
del data\test_chat_*.jsonl
```

---

## 📈 Test Execution Workflow

```
┌─────────────────────────────────────────┐
│  Choose Testing Method                  │
├─────────────────────────────────────────┤
│  1. pytest (Full automated)              │
│  2. Interactive (test_chat_interactive) │
│  3. Batch file (Windows)                │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Setup Environment Variables             │
├─────────────────────────────────────────┤
│  - PYTHONPATH=c:\kortana\src            │
│  - Load .env file                       │
│  - Initialize virtual environment       │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Run Selected Tests                     │
├─────────────────────────────────────────┤
│  - Module imports validated             │
│  - Components initialized               │
│  - Functions executed                   │
│  - Results collected                    │
└─────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────┐
│  Review Results Summary                 │
├─────────────────────────────────────────┤
│  - Passed/Failed count                  │
│  - Performance metrics                  │
│  - Error details (if any)               │
└─────────────────────────────────────────┘
```

---

## 🎯 Next Steps

1. **Run Initial Tests**: Execute `test_chat_interactive.py` to verify setup
2. **Review Results**: Check test output for any failures
3. **Interactive Demo**: Use dev chat interface for manual testing
4. **Integration Testing**: Test with actual LLM API calls
5. **Performance Testing**: Measure response times and memory usage

---

## 📚 Additional Resources

- **Chat Engine Documentation**: See `src/kortana/core/brain.py` docstrings
- **Memory Manager Guide**: Review `src/memory_manager.py` for API
- **Configuration Files**: Check `config/` directory for settings
- **Example Conversations**: Review `data/chat_history/` for examples

---

## ✨ Chat Features Available

### Core Features
- ✅ Real-time message processing
- ✅ Persistent memory and context
- ✅ Multi-turn conversation support
- ✅ Session management
- ✅ Autonomous operation modes

### Advanced Features
- ✅ Memory metadata and tagging
- ✅ Conversation export
- ✅ Covenant-based safety checks
- ✅ Autonomous agent coordination
- ✅ Model routing and selection

---

## 🏆 Test Success Criteria

Tests are considered successful when:

1. **All Core Tests Pass**: ChatEngine, DevChat, Memory system working
2. **No Import Errors**: All required modules importable
3. **Services Initialized**: LLM client, memory manager, execution engine ready
4. **Session Management Works**: Multiple sessions with isolation
5. **Memory Persistence**: Messages stored and retrievable

---

**Last Updated:** February 8, 2026  
**Status:** ✅ Complete - Ready for Testing
