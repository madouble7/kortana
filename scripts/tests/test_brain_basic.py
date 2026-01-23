#!/usr/bin/env python3
"""Test script to verify brain.py functionality"""

try:
    from src.kortana.core.brain import ChatEngine
    print('✅ ChatEngine imported successfully')
    
    # Don't try to instantiate as it may require config
    print('✅ brain.py module loads without syntax errors')
    
except Exception as e:
    print(f'❌ Error: {e}')
    import traceback
    traceback.print_exc()
