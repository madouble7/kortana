import fs from "node:fs";
import path from "node:path";
import { AuthorizationService } from "./AuthorizationService.ts";
import { GovernanceService } from "./GovernanceService.ts";

export interface DeploymentManifest {
  taskId: string;
  stagingSubDir: string;
  files: string[];
  timestamp: string;
  dryRun: boolean;
  status: "success" | "rolled_back" | "failed";
}

export interface DeployOptions {
  dryRun?: boolean;
}

export class DeploymentError extends Error {
  constructor(message: string, public manifest?: DeploymentManifest, public originalError?: unknown) {
    super(message);
    this.name = "DeploymentError";
  }
}

/**
 * Manages the deployment of authorized changes from staging to the live cognitive core.
 */
export class DeploymentService {
  static async deploy(taskId: string, stagingSubDir: string, options: DeployOptions = {}): Promise<DeploymentManifest> {
    if (!AuthorizationService.isTaskAuthorized(taskId)) {
      throw new DeploymentError(`Task ${taskId} is not authorized for deployment.`);
    }

    const stagingPath = path.join(process.cwd(), 'core', 'staging', stagingSubDir);
    const corePath = path.join(process.cwd(), 'core');

    if (!fs.existsSync(stagingPath)) {
      throw new DeploymentError(`Staging directory ${stagingPath} does not exist.`);
    }

    // Generate manifest
    const files = fs.readdirSync(stagingPath);
    const manifest: DeploymentManifest = {
      taskId,
      stagingSubDir,
      files,
      timestamp: new Date().toISOString(),
      dryRun: !!options.dryRun,
      status: "success"
    };

    if (options.dryRun) {
      console.log(`[DEPLOYMENT] Dry run for task ${taskId}:`, manifest);
      return manifest;
    }

    const successfulMoves: { src: string, dest: string }[] = [];

    try {
      // Move files from staging to core
      for (const file of files) {
        const src = path.join(stagingPath, file);
        const dest = path.join(corePath, file);
        fs.renameSync(src, dest);
        successfulMoves.push({ src, dest });
      }
    } catch (error) {
      console.error(`[DEPLOYMENT] Error during deployment of ${taskId}, initiating rollback.`, error);

      // Rollback successful moves in reverse order
      for (const move of successfulMoves.reverse()) {
        try {
          fs.renameSync(move.dest, move.src);
        } catch (rollbackError) {
          console.error(`[DEPLOYMENT] CRITICAL: Rollback failed for ${move.dest} -> ${move.src}`, rollbackError);
        }
      }

      manifest.status = "rolled_back";
      throw new DeploymentError(`Deployment failed during file copy. Rolled back successfully. Original error: ${error}`, manifest, error);
    }

    GovernanceService.logAuditEvent(taskId, 'CORE_DEPLOYMENT', { stagingSubDir, manifest });

    // Consume authorization to prevent replay attacks
    if (!options.dryRun) {
      AuthorizationService.consumeTask(taskId);
    }

    console.log(`[DEPLOYMENT] Task ${taskId} deployed successfully.`);

    return manifest;
  }
}
