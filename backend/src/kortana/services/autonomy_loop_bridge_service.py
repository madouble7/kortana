import json
import logging
import os
import subprocess
from typing import Any, Dict

from src.kortana.config import get_settings

logger = logging.getLogger(__name__)


class AutonomyLoopBridgeService:
    """
    Acts as the secure perimeter bridge between the Python active runtime
    and the sandboxed, deterministic Typescript execution layer in autonomy_loop.
    """

    @classmethod
    def run_dry_run(cls, task_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes a task completely within the autonomy_loop sandbox in dry-run mode.
        Communicates via JSON stdin/stdout using the CLI adapter boundary.
        Guarantees no external side effects such as repository mutations or live deploys.
        """
        workspace_root = os.environ.get("KORTANA_WORKSPACE_ROOT")
        if workspace_root:
            sandbox_dir = os.path.join(workspace_root, "autonomy_loop")
        else:
            sandbox_dir = os.path.join(
                os.path.dirname(
                    os.path.dirname(
                        os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                    )
                ),
                "autonomy_loop",
            )
        cli_path = os.path.join(sandbox_dir, "cli_adapter.ts")

        if not os.path.exists(cli_path):
            return {
                "ok": False,
                "status": "failed",
                "error": f"Sandbox CLI layer completely missing at {cli_path}",
            }

        # Normalize execution payload ensuring valid Task format
        if "id" not in task_payload:
            task_payload["id"] = "live-bridge-" + os.urandom(4).hex()

        # Determine executable mapping gracefully across environments
        npx_bin = "npx.cmd" if os.name == "nt" else "npx"
        process = None
        stdout = None
        timeout_seconds = get_settings().AUTONOMY_LOOP_SHADOW_TIMEOUT_SECONDS

        try:
            logger.info(
                f"Invoking autonomy_loop sandbox bridge for task '{task_payload.get('id')}'"
            )
            process = subprocess.Popen(
                [npx_bin, "tsx", "cli_adapter.ts"],
                cwd=sandbox_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            input_str = json.dumps(task_payload)
            stdout, stderr = process.communicate(
                input=input_str, timeout=timeout_seconds
            )

            if stderr:
                logger.warning(f"Sandbox Diagnostic Emitted:\n{stderr.strip()}")

            return json.loads(stdout)

        except subprocess.TimeoutExpired:
            if process is not None:
                process.kill()
            logger.error(f"Sandbox execution exceeded {timeout_seconds}s limit")
            return {
                "ok": False,
                "status": "failed",
                "error": f"Sandbox execution took longer than {timeout_seconds}s timeout",
            }
        except json.JSONDecodeError as e:
            raw_out = stdout if stdout is not None else "None"
            logger.error(f"Failed to decode sandbox output: {e}\nRaw Output: {raw_out}")
            return {
                "ok": False,
                "status": "failed",
                "error": f"Invalid JSON received from sandbox: {e}",
            }
        except Exception as e:
            logger.error(f"Unexpected error interfacing with the TS boundary: {e}")
            return {
                "ok": False,
                "status": "failed",
                "error": f"Unexpected integration error: {e}",
            }
