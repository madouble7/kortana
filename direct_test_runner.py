#!/usr/bin/env python
"""Direct pytest runner without shell dependency."""
import subprocess
import sys
import os

os.chdir('c:\\kortana')

# Directly call pytest through Python
env = os.environ.copy()
env['PYTHONPATH'] = 'c:\\kortana\\src'
env['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Use the exact Python executable from the venv
python_exe = 'c:\\kortana\\.kortana_config_test_env\\Scripts\\python.exe'

result = subprocess.run(
    [python_exe, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
    env=env,
    capture_output=True,
    text=True
)

output = result.stdout + '\n' + result.stderr  

print(output)

# Save to file
with open('final_test_results.txt', 'w') as f:
    f.write(output)

print(f"\nTest run completed with exit code: {result.returncode}")
