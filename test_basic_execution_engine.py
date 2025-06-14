#!/usr/bin/env python3

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("🔍 Starting simple code scanning test...")

try:
    from src.kortana.core.execution_engine import ExecutionEngine
    print("✅ ExecutionEngine imported successfully")

    # Create execution engine
    allowed_dirs = [str(Path.cwd())]
    blocked_commands = ['rm', 'del', 'format', 'sudo']
    execution_engine = ExecutionEngine(allowed_dirs=allowed_dirs, blocked_commands=blocked_commands)
    print("✅ ExecutionEngine created successfully")

    print("🎉 Basic test passed - ready for async testing")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
