# Kor'tana Examples

This directory contains example scripts demonstrating how to use Kor'tana's various features and integrations.

## Available Examples

### AutoGen Integration

**File:** `autogen_example.py`

Demonstrates how to use Kor'tana's AutoGen-compatible adapter for multi-agent interactions.

**Usage:**
```bash
# Make sure the Kor'tana server is running first
python -m uvicorn src.kortana.main:app --reload

# In another terminal, run the example
python examples/autogen_example.py
```

**What it shows:**
- Simple chat interactions
- Multi-agent collaboration
- Agent status checks
- Error handling

## Prerequisites

All examples require:
- Python 3.11+
- Kor'tana server running
- Dependencies installed: `pip install -e .`

## Adding New Examples

When adding new examples:
1. Create a descriptive filename (e.g., `memory_usage_example.py`)
2. Include docstring with usage instructions
3. Add error handling for common issues
4. Update this README with example description
5. Make scripts executable: `chmod +x examples/your_example.py`

## Running Examples

Most examples can be run directly:
```bash
python examples/example_name.py
```

Some examples may require additional setup or configuration. Check the docstring at the top of each file for specific requirements.
