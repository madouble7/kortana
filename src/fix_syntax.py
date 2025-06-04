"""
Fix Syntax Issues

This script fixes syntax issues in the brain.py file.
It reads the file line by line and fixes any syntax or indentation issues.
"""

import os
import re


def fix_syntax_issues():
    """Fix syntax issues in the brain.py file."""
    file_path = "src/kortana/core/brain.py"

    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found")
        return False

    # Read the file line by line
    with open(file_path, "r") as f:
        lines = f.readlines()

    # Look for specific issues
    fixed_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]

        # Check for the specific syntax error pattern
        if (
            i + 1 < len(lines)
            and line.strip().endswith(")")
            and lines[i + 1].strip().startswith("self.")
            and not line.strip().endswith(")")
        ):
            fixed_lines.append(line)
            fixed_lines.append("\n")  # Add a blank line
            i += 1
            continue

        # Fix CodingAgent initialization
        if "memory_accessor=self.pinecone_memory," in line and line.strip().endswith(
            ")"
        ):
            # This is part of the CodingAgent initialization
            if i + 1 < len(lines) and "self.ade_planner" in lines[i + 1]:
                fixed_lines.append(line)
                fixed_lines.append("\n")  # Add a blank line
                i += 1
                continue

        # General case - add the line as is
        fixed_lines.append(line)
        i += 1

    # Write the fixed file back
    with open(file_path, "w") as f:
        f.writelines(fixed_lines)

    print(f"Syntax fixes applied to {file_path}")
    return True


def complete_fix():
    """Make a complete fix to the brain.py file."""
    brain_path = "src/kortana/core/brain.py"

    if not os.path.exists(brain_path):
        print(f"Error: {brain_path} not found")
        return False

    # Read the file
    try:
        with open(brain_path, "r") as f:
            content = f.read()

        # Find each agent initialization
        coder_pattern = r"self\.ade_coder = CodingAgent\([^)]*\)"
        planner_pattern = r"self\.ade_planner = PlanningAgent\([^)]*\)"
        tester_pattern = r"self\.ade_tester = TestingAgent\([^)]*\)"

        # Replace using regex to ensure complete replacements with proper formatting

        # First, fix the CodingAgent
        coder_new = """        self.ade_coder = CodingAgent(
            memory_accessor=self.pinecone_memory,
            dev_agent_instance=self.dev_agent_instance,
            settings=self.settings,
            llm_client=self.ade_llm_client
        )

"""
        content = re.sub(coder_pattern, coder_new.strip(), content, flags=re.DOTALL)

        # Fix the PlanningAgent
        planner_new = """        self.ade_planner = PlanningAgent(
            chat_engine_instance=self,
            llm_client=self.ade_llm_client,
            covenant_enforcer=self.covenant_enforcer,
            settings=self.settings
        )

"""
        content = re.sub(planner_pattern, planner_new.strip(), content, flags=re.DOTALL)

        # Fix the TestingAgent
        tester_new = """        self.ade_tester = TestingAgent(
            chat_engine_instance=self,
            llm_client=self.ade_llm_client,
            covenant_enforcer=self.covenant_enforcer,
            settings=self.settings
        )

"""
        content = re.sub(tester_pattern, tester_new.strip(), content, flags=re.DOTALL)

        # Fix monitoring config section
        monitoring_old = "        # Get monitoring config (handle both dict and model types)\n        monitoring_config = {}"
        monitoring_new = """        # Handle agent types configuration
        monitoring_config = {}
        if hasattr(self.settings, 'agents') and hasattr(self.settings.agents, 'types'):
            if isinstance(self.settings.agents.types, dict):
                if 'monitoring' in self.settings.agents.types:
                    monitoring_config = self.settings.agents.types['monitoring']"""

        content = content.replace(monitoring_old, monitoring_new)

        # Write the fixed content back
        with open(brain_path, "w") as f:
            f.write(content)

        print(f"Complete fix applied to {brain_path}")
        return True

    except Exception as e:
        print(f"Error applying complete fix: {e}")
        return False


if __name__ == "__main__":
    print("Fixing syntax issues in brain.py...")

    # Apply the complete fix first
    complete_fix()

    # Then apply the line-by-line fix
    fix_syntax_issues()

    print("Syntax fixes complete!")
    input("Press Enter to continue...")
