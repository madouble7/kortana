import os
import subprocess
import sys

os.chdir(r"c:\kortana\backend")
r = subprocess.run(
    [sys.executable, "-m", "pytest", "tests", "--tb=short", "-q"],
    capture_output=True,
    text=True,
    timeout=600,
)
with open(r"c:\kortana\test_final3.txt", "w") as f:
    f.write(r.stdout)
    f.write("\n---STDERR---\n")
    f.write(r.stderr)

print(f"RC={r.returncode}")
lines = (r.stdout + r.stderr).strip().splitlines()
for line in lines[-25:]:
    print(line)
