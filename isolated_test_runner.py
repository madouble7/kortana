#!/usr/bin/env python
"""Standalone test runner script."""
import os
import sys
import subprocess

# Change to the kortana directory
os.chdir('c:\\kortana')

# Set environment variables
env = os.environ.copy()
env['PYTHONPATH'] = os.path.join(os.getcwd(), 'src')
env['PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION'] = 'python'

# Run pytest
result = subprocess.Popen(
    [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
    env=env,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    universal_newlines=True
)

test_output = []
for line in result.stdout:
    test_output.append(line)
    print(line, end='')

result.wait()

# Write results to file
with open('c:\\kortana\\final_test_results.txt', 'w') as f:
    f.writelines(test_output)

sys.exit(result.returncode)
