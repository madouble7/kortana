"""Bulk fix all kortana imports to use src.kortana prefix."""
import os
import re
from pathlib import Path

def fix_imports_in_file(filepath):
    """Fix imports in a single Python file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
    
    original_content = content
    
    # Fix imports: "from kortana." -> "from src.kortana."
    content = re.sub(
        r'^from kortana\.(?!__)',
        'from src.kortana.',
        content,
        flags=re.MULTILINE
    )
    
    # Fix imports: "import kortana" -> "import src.kortana as kortana"
    content = re.sub(
        r'^import kortana(?:\s|$)',
        'import src.kortana as kortana',
        content,
        flags=re.MULTILINE
    )
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    """Fix all imports in the repository."""
    root = Path('/c/kortana')
    
    # Files to fix
    files_fixed = []
    files_skipped = []
    
    for py_file in root.rglob('*.py'):
        # Skip git, cache, and venv directories
        if any(part in py_file.parts for part in ['.git', '__pycache__', 'venv', '.venv', 'venv311']):
            continue
        
        try:
            if fix_imports_in_file(py_file):
                files_fixed.append(str(py_file))
                print("FIXED: {}".format(py_file.relative_to(root)))
            else:
                files_skipped.append(str(py_file))
        except Exception as e:
            print("ERROR: {}: {}".format(py_file, e))
    
    print("\nFixed {} files".format(len(files_fixed)))
    print("Skipped {} files (no changes needed)".format(len(files_skipped)))

if __name__ == '__main__':
    main()
