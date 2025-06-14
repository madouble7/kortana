"""
Basic script to test importing a specific module and listing its contents.
"""

import inspect
import os
import sys

# Print Python version and environment info
print(f"Python version: {sys.version}")
print(f"Working directory: {os.getcwd()}")
print(f"Initial sys.path: {sys.path}")

# Add the src directory to the path
if os.path.exists("src"):
    sys.path.insert(0, os.path.abspath("src"))
    print(f"Added {os.path.abspath('src')} to sys.path")

# Print the updated path
print(f"Updated sys.path: {sys.path}")

# Try to import specific modules
modules_to_try = [
    "kortana.config.schema",
    "kortana.core.brain",
    "kortana.agents.coding_agent",
]

for module_name in modules_to_try:
    print(f"\nAttempting to import {module_name}...")
    try:
        # Import the module
        module = __import__(module_name, fromlist=["*"])
        print(f"Successfully imported {module_name}")

        # List the module's attributes
        print("Public attributes:")
        for name in dir(module):
            if not name.startswith("_"):
                attr = getattr(module, name)
                attr_type = (
                    "function"
                    if inspect.isfunction(attr)
                    else "class"
                    if inspect.isclass(attr)
                    else type(attr).__name__
                )
                print(f"  {name} ({attr_type})")

    except ImportError as e:
        print(f"ImportError: {e}")
    except Exception as e:
        print(f"Other error: {type(e).__name__}: {e}")

print("\nDiagnostic test completed.")
