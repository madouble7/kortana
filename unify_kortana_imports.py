import os
import re

def unify_imports(root_dir):
    # Pattern to match both 'from kortana' and 'from src' (if referring to internal modules)
    # We also need to handle 'import kortana'
    
    # Specific patterns to replace
    replacements = [
        (r'from src\.kortana', r'from kortana'),
        (r'import src\.kortana', r'import kortana'),
        (r'from src\.', r'from kortana.'),
        (r'import src\.', r'import kortana.'),
        # Handle cases where someone might have used just 'from kortana import ...'
        (r'from kortana import', r'from kortana import'),
    ]

    for subdir, dirs, files in os.walk(root_dir):
        # Skip .venv and other hidden dirs
        if '.kortana_config_test_env' in subdir or '.git' in subdir:
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(subdir, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = content
                    for pattern, replacement in replacements:
                        new_content = re.sub(pattern, replacement, new_content)
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Updated: {filepath}")
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")

if __name__ == "__main__":
    unify_imports(os.getcwd())
    print("Import unification complete.")