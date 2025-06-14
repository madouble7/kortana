"""
Check for Pydantic warnings in the schema models.
"""

import warnings

# Enable all warnings
warnings.filterwarnings("always")


# Redirect warnings to stdout
def warning_on_one_line(message, category, filename, lineno, file=None, line=None):
    return f"WARNING: {category.__name__}: {message}\n"


warnings.formatwarning = warning_on_one_line

print("Testing for Pydantic model_mapping warnings...")

# Import the relevant class
from kortana.config.schema import AgentTypeConfig, KortanaConfig

# Create instances
print("\nCreating AgentTypeConfig instance...")
agent_config = AgentTypeConfig()
print(f"AgentTypeConfig fields: {list(agent_config.__fields__.keys())}")

print("\nCreating KortanaConfig instance...")
config = KortanaConfig()
print(f"Configuration has agents: {hasattr(config, 'agents')}")
print(f"Agent types config: {config.agents.types}")

print(
    "\nTest completed. If no warnings appeared above, then no Pydantic warnings were triggered."
)
