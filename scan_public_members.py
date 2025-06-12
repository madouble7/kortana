"""
Scan for public members in the kortana codebase.
This script identifies public classes and their public methods,
as well as public functions at the module level.
"""

import importlib
import inspect
import json
import os
import pkgutil
import sys

# Add src to path for imports
sys.path.append(os.path.abspath("src"))


def is_public_member(name: str) -> bool:
    """Check if a name represents a public member."""
    # Public members don't start with underscore,
    # but __dunder__ methods are considered public
    return not name.startswith("_") or (name.startswith("__") and name.endswith("__"))


def get_public_members_from_module(module_name: str) -> dict[str, list[str]]:
    """
    Get all public members from a module.

    Returns:
        Dict with keys: 'functions', 'classes', and 'class_methods'
    """
    result = {
        "functions": [],  # Module-level functions
        "classes": [],  # Classes
        "class_methods": {},  # Methods by class
    }

    try:
        # Import the module
        module = importlib.import_module(module_name)

        # Get all members from the module
        for name, obj in inspect.getmembers(module):
            # Skip imported items
            if hasattr(obj, "__module__") and obj.__module__ != module_name:
                continue

            # Check if it's a public member
            if is_public_member(name):
                if inspect.isfunction(obj):
                    result["functions"].append(name)
                elif inspect.isclass(obj):
                    result["classes"].append(name)
                    result["class_methods"][name] = []

                    # Get public methods of the class
                    for method_name, method in inspect.getmembers(obj):
                        if is_public_member(method_name) and (
                            inspect.isfunction(method) or inspect.ismethod(method)
                        ):
                            # Skip inherited methods from non-kortana parents
                            if (
                                hasattr(method, "__module__")
                                and method.__module__ == module_name
                            ):
                                result["class_methods"][name].append(method_name)

    except ImportError as e:
        print(f"Error importing {module_name}: {e}")
        return result
    except Exception as e:
        print(f"Error processing {module_name}: {e}")
        return result

    return result


def find_modules_in_package(package_name: str) -> list[str]:
    """Find all modules in a package recursively."""
    modules = []

    try:
        package = importlib.import_module(package_name)
        package_path = getattr(package, "__path__", [])

        for _, name, is_pkg in pkgutil.iter_modules(package_path):
            full_name = f"{package_name}.{name}"
            modules.append(full_name)

            if is_pkg:
                # Recursively handle subpackages
                modules.extend(find_modules_in_package(full_name))
    except ImportError:
        print(f"Package {package_name} not found")

    return modules


def main():
    """Scan the key modules and output public members."""
    # Define the key modules and packages to scan
    packages_to_scan = [
        "kortana.core",
        "kortana.memory",
        "kortana.agents",
        "kortana.llm_clients",
        "kortana.utils",
        "kortana.config",
    ]

    additional_modules = ["src.model_router", "src.sacred_trinity_router"]

    # Collect all modules from packages
    all_modules = []
    for package in packages_to_scan:
        all_modules.extend(find_modules_in_package(package))

    # Add individual modules
    all_modules.extend(additional_modules)

    # Dictionary to store all public members by module
    public_members_by_module = {}

    # Process each module
    for module_name in all_modules:
        print(f"Scanning module: {module_name}")
        public_members = get_public_members_from_module(module_name)
        public_members_by_module[module_name] = public_members

    # Output the results
    print("\n=== Public Members Summary ===")
    total_classes = 0
    total_functions = 0
    total_methods = 0

    for module_name, members in public_members_by_module.items():
        module_classes = len(members["classes"])
        module_functions = len(members["functions"])

        module_methods = 0
        for class_name, methods in members["class_methods"].items():
            module_methods += len(methods)

        total_classes += module_classes
        total_functions += module_functions
        total_methods += module_methods

        print(
            f"{module_name}: {module_classes} classes, {module_functions} functions, {module_methods} methods"
        )

    print(
        f"\nTotal: {total_classes} classes, {total_functions} functions, {total_methods} methods"
    )

    # Save to JSON file for further processing
    with open("public_members.json", "w") as f:
        json.dump(public_members_by_module, f, indent=2)

    print("Public members saved to public_members.json")


if __name__ == "__main__":
    main()
