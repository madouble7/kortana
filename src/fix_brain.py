"""
Fix Brain Script

This script fixes the brain.py file to handle both dictionary and object-based configurations.
"""

import os


def fix_brain_configuration():
    """Fix the brain.py file to handle configurations correctly."""
    brain_path = "src/kortana/core/brain.py"

    if not os.path.exists(brain_path):
        print(f"Error: {brain_path} not found.")
        return False

    # Read the current file
    with open(brain_path) as f:
        content = f.read()

    # Apply modification for monitoring_config
    if "self.settings.agents.types.monitoring" in content:
        print("Applying fix for monitoring_config...")

        new_content = content.replace(
            "        # Get monitoring config (handle both dict and model types)",
            """        # Handle agent types configuration for both dict and object
        agent_types = {}
        if hasattr(self.settings.agents, "types"):
            if isinstance(self.settings.agents.types, dict):
                agent_types = self.settings.agents.types
            else:
                # Convert to dict if it's a Pydantic model
                agent_types = {
                    "coding": getattr(self.settings.agents.types, "coding", {}),
                    "planning": getattr(self.settings.agents.types, "planning", {}),
                    "testing": getattr(self.settings.agents.types, "testing", {}),
                    "monitoring": getattr(self.settings.agents.types, "monitoring", {})
                }

        # Get monitoring config""",
        )

        new_content = new_content.replace(
            '        monitoring_config = {}\n        if hasattr(self.settings.agents.types, "monitoring"):\n            monitoring_config = self.settings.agents.types.monitoring\n        elif isinstance(self.settings.agents.types, dict) and "monitoring" in self.settings.agents.types:\n            monitoring_config = self.settings.agents.types["monitoring"]',
            """        # Get monitoring config
        monitoring_config = agent_types.get("monitoring", {})""",
        )

        # Write the fixed file
        with open(brain_path, "w") as f:
            f.write(new_content)

        print("Fix applied successfully!")
        return True
    else:
        print(
            "The file doesn't need fixing or has a different structure than expected."
        )
        return False


def fix_indentation_issue():
    """Fix any indentation issues in the file."""
    brain_path = "src/kortana/core/brain.py"

    if not os.path.exists(brain_path):
        print(f"Error: {brain_path} not found.")
        return False

    # Read the current file
    with open(brain_path) as f:
        lines = f.readlines()

    # Look for indentation issues
    fixed_lines = []

    for line in lines:
        # Check for specific indentation issue in the PlanningAgent section
        if ")        self.ade_tester" in line:
            fixed_lines.append("        )\n")
            fixed_lines.append("\n")
            fixed_lines.append("        self.ade_tester")
            continue

        fixed_lines.append(line)

    # Write the fixed file
    with open(brain_path, "w") as f:
        f.writelines(fixed_lines)

    print("Indentation fix attempted.")
    return True


if __name__ == "__main__":
    print("Fixing brain.py configuration handling...")

    fixed_indentation = fix_indentation_issue()
    fixed_config = fix_brain_configuration()

    if fixed_indentation or fixed_config:
        print("\nFixes applied. You can now try running:")
        print("python -m src.kortana.core.brain")
    else:
        print("\nNo fixes were applied.")

    input("Press Enter to continue...")
