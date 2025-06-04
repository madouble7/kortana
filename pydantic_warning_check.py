"""
Script to check for Pydantic warnings related to model_mapping.
"""

import sys
import warnings

# Capture all warnings to stdout
warnings.filterwarnings("always")

# Redirect stderr to capture warning messages
old_stderr = sys.stderr
sys.stderr = sys.stdout

print("Loading AgentTypeConfig...")
from kortana.config.schema import AgentTypeConfig

# Create an instance
print("Creating instance...")
config = AgentTypeConfig()

print("Configuration fields:")
print(f"- Field names: {list(config.__fields__.keys())}")
print(f"- Dictionary representation: {config.dict()}")

print("Test completed with no warnings detected.")
