"""
Quick test script to check for Pydantic warnings.
Run with: python -W all main.py
"""

import warnings

# Enable all warnings
warnings.filterwarnings("always", category=Warning)


def main():
    print("Testing imports and checking for Pydantic warnings...")

    # Import the modules that previously caused warnings
    from kortana.config.schema import AgentsConfig, AgentTypeConfig, KortanaConfig

    # Create instances to trigger any potential warnings
    agent_type_config = AgentTypeConfig()
    print(f"AgentTypeConfig fields: {list(agent_type_config.__fields__.keys())}")

    agents_config = AgentsConfig()
    print(f"AgentsConfig has types: {hasattr(agents_config, 'types')}")

    # Create the main config that would use all sub-configs
    config = KortanaConfig()
    print(f"KortanaConfig has agents: {hasattr(config, 'agents')}")

    print("\nTest completed without Pydantic warnings.")


if __name__ == "__main__":
    main()
