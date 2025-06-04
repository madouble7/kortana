import sys
import os

print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print(f"Current Working Directory: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
print("\nPython Path:")
for path in sys.path:
    print(f"  - {path}")
