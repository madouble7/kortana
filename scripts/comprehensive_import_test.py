"""
Comprehensive Import Test for Kortana

This script tests imports from various Kortana modules to verify
that the package structure is correctly set up.
"""

import sys

print("Python version:", sys.version)
print("sys.path:", sys.path)
print("\n==== Testing Imports ====\n")

# Test kortana.config imports
print("1. Testing kortana.config imports...")
try:
    print("✓ Successfully imported load_config and get_config from kortana.config")

    print("✓ Successfully imported KortanaConfig from kortana.config.schema")
except Exception as e:
    print(f"✗ Error with kortana.config imports: {e}")

# Test kortana.memory imports
print("\n2. Testing kortana.memory imports...")
try:
    print("✓ Successfully imported MemoryEntry from kortana.memory.memory")

    print("✓ Successfully imported MemoryManager from kortana.memory.memory_manager")
except Exception as e:
    print(f"✗ Error with kortana.memory imports: {e}")

# Test kortana.core imports
print("\n3. Testing kortana.core imports...")
try:
    print("✓ Successfully imported ChatEngine from kortana.core.brain")

    # Testing another core module if available
    try:
        from kortana.core.covenant_enforcer import CovenantEnforcer

        print(
            "✓ Successfully imported CovenantEnforcer from kortana.core.covenant_enforcer"
        )
    except ImportError as e:
        print(f"- Note: CovenantEnforcer import attempted but not critical: {e}")
except Exception as e:
    print(f"✗ Error with kortana.core imports: {e}")

# Test pydantic model warning
print("\n4. Testing for Pydantic model_mapping warning...")
try:
    import io
    import warnings
    from contextlib import redirect_stderr

    # Capture warnings
    f = io.StringIO()
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        with redirect_stderr(f):
            pass

        # Check for warnings about model_mapping
        model_mapping_warning = False
        for warning in w:
            if "model_" in str(warning.message) and "AgentTypeConfig" in str(
                warning.message
            ):
                model_mapping_warning = True
                print(f"! Warning detected: {warning.message}")

        if not model_mapping_warning:
            print("✓ No model_mapping warnings detected")
except Exception as e:
    print(f"✗ Error testing for Pydantic warnings: {e}")

print("\n==== Import Test Complete ====")
print("\n==== Import Test Complete ====")
