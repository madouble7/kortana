import sys
from pathlib import Path

project_root = Path(__file__).parent
# Add both project root and src to path
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Import from the correct config location
from config import load_config

settings = load_config()

# Write results to file
with open("config_debug_output.txt", "w") as f:
    f.write("API Keys Debug:\n")
    f.write(f"settings.api_keys: {settings.api_keys}\n")
    f.write(f"Type: {type(settings.api_keys)}\n")

    if settings.api_keys:
        f.write(f"openai: '{settings.api_keys.openai}'\n")
        f.write(f"get_api_key result: '{settings.get_api_key('openai')}'\n")
    else:
        f.write("api_keys is None\n")

print("Debug output written to config_debug_output.txt")
