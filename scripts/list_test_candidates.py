"""
Simple script to list public classes and methods from key modules.
"""

import importlib
import inspect
import os
import sys

# Add paths for imports
sys.path.append(os.path.abspath("."))
sys.path.append(os.path.abspath("src"))

# Key modules/files to check
modules_to_check = [
    "kortana.config.schema",
    "kortana.core.brain",
    "kortana.memory.memory",
    "kortana.memory.memory_manager",
    "kortana.memory.memory_store",
    "kortana.agents.coding_agent",
    "kortana.agents.monitoring_agent",
    "kortana.agents.planning_agent",
    "kortana.agents.testing_agent",
    "kortana.llm_clients.google_genai_client",
    "kortana.llm_clients.llama_client",
    "kortana.llm_clients.openrouter_client",
    "kortana.llm_clients.xai_grok_client",
    "kortana.utils.text_analysis",
    "kortana.utils.timestamp_utils",
]

# Placeholder for test candidate list
test_candidates = []


def is_public(name):
    """Check if name is a public member (not starting with underscore)."""
    return not name.startswith("_") or (name.startswith("__") and name.endswith("__"))


def scan_module(module_name):
    """Scan a module for public classes and functions."""
    try:
        print(f"Loading module: {module_name}")
        module = importlib.import_module(module_name)

        # Track candidates for this module
        module_candidates = []

        # Find classes
        for cls_name, cls in inspect.getmembers(module, inspect.isclass):
            # Check if it's defined in this module (not imported)
            if hasattr(cls, "__module__") and cls.__module__ == module_name:
                if is_public(cls_name):
                    # Add class to candidates
                    module_candidates.append(f"{module_name}.{cls_name}")
                    print(f"  Class: {cls_name}")

                    # Find methods
                    for method_name, method in inspect.getmembers(
                        cls, inspect.isfunction
                    ):
                        if is_public(method_name):
                            module_candidates.append(
                                f"{module_name}.{cls_name}.{method_name}"
                            )
                            print(f"    Method: {method_name}")

        # Find module-level functions
        for func_name, func in inspect.getmembers(module, inspect.isfunction):
            if hasattr(func, "__module__") and func.__module__ == module_name:
                if is_public(func_name):
                    module_candidates.append(f"{module_name}.{func_name}")
                    print(f"  Function: {func_name}")

        return module_candidates

    except Exception as e:
        print(f"Error scanning module {module_name}: {e}")
        return []


def main():
    """Main function to scan modules and list test candidates."""
    all_candidates = []

    for module_name in modules_to_check:
        candidates = scan_module(module_name)
        all_candidates.extend(candidates)

    print(f"\nTotal test candidates found: {len(all_candidates)}")

    # Save to file
    with open("test_candidates.txt", "w") as f:
        f.write("# Test candidates for unit test stubs\n")
        for candidate in all_candidates:
            f.write(f"{candidate}\n")

    print("Candidates written to test_candidates.txt")


if __name__ == "__main__":
    main()
