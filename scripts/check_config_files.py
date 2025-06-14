import os

# Check for config.py file
config_file_path = os.path.join("src", "kortana", "config.py")
if os.path.exists(config_file_path):
    print(f"File exists: {config_file_path}")
else:
    print(f"File does not exist: {config_file_path}")

# Check for config directory
config_dir_path = os.path.join("src", "kortana", "config")
if os.path.isdir(config_dir_path):
    print(f"Directory exists: {config_dir_path}")

    # Check for __init__.py in the config directory
    init_file_path = os.path.join(config_dir_path, "__init__.py")
    if os.path.exists(init_file_path):
        print(f"File exists: {init_file_path}")
    else:
        print(f"File does not exist: {init_file_path}")

    # Check for schema.py in the config directory
    schema_file_path = os.path.join(config_dir_path, "schema.py")
    if os.path.exists(schema_file_path):
        print(f"File exists: {schema_file_path}")
    else:
        print(f"File does not exist: {schema_file_path}")

    # List all files in the config directory
    print("\nFiles in the config directory:")
    for file in os.listdir(config_dir_path):
        file_path = os.path.join(config_dir_path, file)
        print(f"- {file} {'(directory)' if os.path.isdir(file_path) else ''}")
else:
    print(f"Directory does not exist: {config_dir_path}")
