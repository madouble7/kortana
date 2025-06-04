import sys

sys.path.insert(0, ".")

from config import load_config

print("\n=== COVENANT RULES TEST ===")
settings = load_config()

print("\nCovenant Rules:")
print(f"* Has covenant_rules attribute: {hasattr(settings, 'covenant_rules')}")

if hasattr(settings, "covenant_rules"):
    print(f"* covenant_rules is None: {settings.covenant_rules is None}")
    print(f"* covenant_rules type: {type(settings.covenant_rules)}")
    print(
        f"* covenant_rules empty: {len(settings.covenant_rules) == 0 if settings.covenant_rules else 'N/A (None)'}"
    )

print("\n=== CONFIG PATHS ===")
print("covenant.yaml path:", settings.paths.covenant_file_path)

# Try to read the covenant file directly
try:
    from pathlib import Path

    import yaml

    covenant_path = Path(settings.paths.covenant_file_path)
    if not covenant_path.is_absolute():
        potential_paths = [Path("config") / covenant_path, Path(covenant_path)]
        for path in potential_paths:
            print(f"Checking {path} (exists: {path.exists()})")
            if path.exists():
                print(f"Found covenant at: {path}")
                with open(path, "r") as f:
                    data = yaml.safe_load(f)
                print(f"Direct load successful: {bool(data)}")
                print(f"Direct load data type: {type(data)}")
                print(
                    f"Direct load data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
                )
                break
    else:
        print(
            f"Checking absolute path {covenant_path} (exists: {covenant_path.exists()})"
        )
        if covenant_path.exists():
            print(f"Found covenant at: {covenant_path}")
            with open(covenant_path, "r") as f:
                data = yaml.safe_load(f)
            print(f"Direct load successful: {bool(data)}")
            print(f"Direct load data type: {type(data)}")
            print(
                f"Direct load data keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}"
            )
except Exception as e:
    print(f"Error directly accessing covenant file: {e}")
