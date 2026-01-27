import os
import re

def replace_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replace from kortana with from kortana
    # Handle both from kortana and import kortana
    new_content = re.sub(r'from src\.kortana', 'from kortana', content)
    new_content = re.sub(r'import src\.kortana', 'import kortana', new_content)
    
    if content != new_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False

def process_directory(directory, log):
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                if replace_in_file(os.path.join(root, file)):
                    count += 1
    log.write(f"Updated {count} files in {directory}\n")

if __name__ == "__main__":
    with open('c:/kortana/unify_log.txt', 'w') as log:
        log.write("Starting unification...\n")
        process_directory('c:/kortana/src/kortana', log)
        process_directory('c:/kortana/tests', log)
        log.write("Finished unification.\n")
