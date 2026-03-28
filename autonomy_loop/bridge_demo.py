import json
import os
import subprocess


def run_dry_run_task_in_sandbox(task_payload: dict) -> dict:
    """
    Executes a task completely within the autonomy_loop sandbox.
    Communicates via JSON stdin/stdout using the CLI adapter boundary.
    Guaranteed no external side effects (dry_run mode enforced by default).
    """
    sandbox_dir = os.path.dirname(os.path.abspath(__file__))

    # We use npx tsx to execute the typescript file directly.
    # In a production environment, you might transpile first and run node cli_adapter.js
    process = subprocess.Popen(
        ["npx.cmd", "tsx", "cli_adapter.ts"],
        cwd=sandbox_dir,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    input_str = json.dumps(task_payload)

    try:
        stdout, stderr = process.communicate(input=input_str, timeout=120)

        # Log sandbox diagnostic info which is routed to stderr
        if stderr:
            print("--- Sandbox Logs ---")
            print(stderr.strip())
            print("--------------------")

        return json.loads(stdout)
    except subprocess.TimeoutExpired:
        process.kill()
        return {
            "ok": False,
            "status": "failed",
            "error": "Sandbox execution took longer than 120s",
        }
    except json.JSONDecodeError as e:
        return {
            "ok": False,
            "status": "failed",
            "error": f"Invalid JSON received from sandbox: {e}",
        }


if __name__ == "__main__":
    test_task = {
        "id": "bridge-task-999",
        "description": "Prove Python to Node boundary extraction strategy works.",
        "priority": "critical",
        "status": "new",
        "created_at": "2026-03-29T10:00:00Z",
    }

    sandbox_dir = os.path.dirname(os.path.abspath(__file__))
    mock_file = os.path.join(sandbox_dir, "src", "mock.ts")
    if os.path.exists(mock_file):
        os.remove(mock_file)

    print("Sending Task to Sandbox:")
    print(json.dumps(test_task, indent=2))
    print("\nExecuting...\n")

    result = run_dry_run_task_in_sandbox(test_task)

    print("\nReceived Extracted ServiceResult:")
    print(f"Status: {result.get('status')}")
    print(f"OK: {result.get('ok')}")
    print(
        f"Has Deployment Manifest: {'deployment_manifest' in result.get('artifacts', {})}"
    )
