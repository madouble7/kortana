#!/usr/bin/env python3
"""Test script to verify ExecutionEngine functionality"""

try:
    from kortana.core.execution_engine import ExecutionEngine
    print('✅ ExecutionEngine imported successfully')
    
    engine = ExecutionEngine(['c:/temp'], ['rm'])
    print('✅ ExecutionEngine instantiated successfully')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
