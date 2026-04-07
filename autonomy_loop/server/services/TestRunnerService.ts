import { exec } from "node:child_process";
import { promisify } from "node:util";
import { Task, ServiceResult, TestReport } from "../../src/types.ts";

const execAsync = promisify(exec);

const ALLOWED_COMMANDS = [
  "npm run lint",
  "npm run build",
  "npm test",
  "tsc"
];

export class TestRunnerService {
  static async runTests(task: Task): Promise<ServiceResult<TestReport>> {
    // Default to linting as a basic verification step
    let commandToRun = "npm run lint";

    if (task.plan?.tests_to_run && task.plan.tests_to_run.length > 0) {
      const requestedCmd = task.plan.tests_to_run[0];
      // Only allow safe, predefined commands
      if (ALLOWED_COMMANDS.includes(requestedCmd)) {
        commandToRun = requestedCmd;
      } else {
        console.warn(`[Tester] Command '${requestedCmd}' not in allowlist. Falling back to '${commandToRun}'.`);
      }
    }

    try {
      // Execute with a 30-second timeout to prevent hung processes
      const { stdout, stderr } = await execAsync(commandToRun, { timeout: 30000 });
      
      return {
        ok: true,
        status: "passed",
        artifacts: {
          command: commandToRun,
          exit_code: 0,
          stdout: stdout.slice(-2000), // Keep logs reasonable
          stderr: stderr.slice(-2000)
        }
      };
    } catch (error: any) {
      const isTimeout = error.killed && error.signal === 'SIGTERM';
      
      return {
        ok: false,
        status: "failed",
        artifacts: {
          command: commandToRun,
          exit_code: error.code || (isTimeout ? 124 : 1),
          stdout: (error.stdout || "").slice(-2000),
          stderr: (error.stderr || String(error)).slice(-2000)
        },
        error: isTimeout ? "Test execution timed out after 30s" : "Tests failed"
      };
    }
  }
}
