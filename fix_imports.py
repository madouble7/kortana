# Check and fix the kortana module imports
import os

# First, determine if we need to modify the __init__.py file
init_path = os.path.join("src", "kortana", "__init__.py")

with open(init_path, "r") as f:
    content = f.read()

if "from .config import" in content:
    # Fix the import error by modifying the __init__.py
    fixed_content = content.replace(
        "from .config import",
        "# Import from config module\ntry:\n    from .config import",
    )
    fixed_content = fixed_content.replace(
        "ModuleNotFoundError: No module named",
        "except ModuleNotFoundError:\n    # External config module\n    from config import load_config, get_config, get_api_key\n# End of config import fix",
    )

    # Write the fixed content back to the file
    with open(init_path, "w") as f:
        f.write(fixed_content)

    print(f"Fixed import issue in {init_path}")
else:
    print(
        f"The file {init_path} doesn't contain the problematic import or was already fixed"
    )
