"""
Simple test to import a couple of modules and check their members.
"""

import sys

print(f"Python version: {sys.version}")
print(f"Sys path: {sys.path}")

# Add src to path
import os

sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("src"))
print(f"Updated path: {sys.path}")

try:
    import kortana.config.schema

    print("Successfully imported kortana.config.schema")

    for name in dir(kortana.config.schema):
        if not name.startswith("_"):
            print(f"  {name}")
except Exception as e:
    print(f"Error importing kortana.config.schema: {e}")

try:
    from kortana.agents.coding_agent import CodingAgent

    print("\nSuccessfully imported CodingAgent")

    for name in dir(CodingAgent):
        if not name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            print(f"  {name}")
except Exception as e:
    print(f"Error importing CodingAgent: {e}")

print("\nTest complete.")

print("\nTest complete.")
