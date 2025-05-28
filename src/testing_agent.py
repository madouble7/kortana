import subprocess

class TestingAgent:
    def run_tests(self):
        res = subprocess.run(["pytest", "-q"], capture_output=True, text=True)
        return {"success": res.returncode == 0, "output": res.stdout + res.stderr} 