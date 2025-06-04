import os

print("Checking for kortana/config directory...")
config_path = os.path.join("src", "kortana", "config")
if os.path.exists(config_path):
    print(f"Config directory exists at {config_path}")
    print("Files in config directory:")
    for file in os.listdir(config_path):
        print(f"- {file}")
else:
    print(f"Config directory does not exist at {config_path}")

# Check for config.py directly in kortana
config_file = os.path.join("src", "kortana", "config.py")
if os.path.exists(config_file):
    print(f"\nConfig file exists at {config_file}")
else:
    print(f"\nConfig file does not exist at {config_file}")
    print(f"\nConfig file does not exist at {config_file}")
