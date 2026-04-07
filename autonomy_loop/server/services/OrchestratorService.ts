import fs from 'node:fs';
import type { ServiceResult, Task } from '../../src/types.ts';
import { AuthorizationService } from './AuthorizationService.ts';
import { DeploymentService } from './DeploymentService.ts';
import { MergeService } from './MergeService.ts';
import { PlanningService } from './PlanningService.ts';
import { ReviewService } from './ReviewService.ts';
import { TestRunnerService } from './TestRunnerService.ts';
import { WorkspaceService } from './WorkspaceService.ts';

export class OrchestratorService {
    /**
     * Executes the autonomy loop for a given task.
     * @param task The task to execute
     * @param ai The AI provider injection
     * @param opts Orchestration options, notably dryRun to block external side-effects
     * @returns ServiceResult encapsulating the end state
     */
    static async executeLoop(task: Task, ai: any, opts: { dryRun?: boolean } = {}): Promise<ServiceResult> {
        const planResult = await PlanningService.planTask(task, ai);
        if (!planResult.ok) return planResult;
        task.plan = planResult.artifacts!;

        const workspaceResult = await WorkspaceService.executePlan(task, ai);
        if (!workspaceResult.ok) return workspaceResult;
        task.changeset = workspaceResult.artifacts!;

        const testResult = await TestRunnerService.runTests(task);
        task.test_report = testResult.artifacts; // Store artifacts regardless of ok
        if (!testResult.ok && !testResult.artifacts) {
            return testResult; // Catastrophic failure
        }
        // Even if tests fail (exit_code != 0), we usually want ReviewService to see it

        const reviewResult = await ReviewService.reviewTask(task, ai);
        task.review_summary = reviewResult.artifacts!;
        if (!reviewResult.ok || !reviewResult.artifacts?.approved) return reviewResult;

        // If dryRun, we simulate deployment manifesting and abort the real merge/deploy
        if (opts.dryRun) {
            // Guarantee authorization is present in test environment for dryRun manifest extraction
            if (!AuthorizationService.isTaskAuthorized(task.id)) {
                AuthorizationService.authorizeTask(task.id, 'dry-run-system', 'Orchestrator dry run pre-auth');
            }

            try {
                // Determine staging subdir or mock it safely for dry run
                const stagingSubDir = task.id;
                // Ensure a dummy dir exists ifWorkspaceService didn't build it (sandbox)
                const dummyPath = `core/staging/${stagingSubDir}`;
                if (!fs.existsSync(dummyPath)) {
                    fs.mkdirSync(dummyPath, { recursive: true });
                }

                const deployManifest = await DeploymentService.deploy(task.id, stagingSubDir, { dryRun: true });
                task.deployment_manifest = deployManifest;
            } catch (e: any) {
                // If the dummy staging logic fails, we return a deployment failure
                return { ok: false, status: 'failed', error: `Dry-run deployment failed: ${e.message}`, artifacts: task };
            }

            // Return early: Block real merges & physical side-effects
            return {
                ok: true,
                status: 'passed',
                artifacts: task
            };
        }

        // Full operational path (Merge -> Deploy)
        const mergeResult = await MergeService.mergeTask(task);
        if (!mergeResult.ok) return mergeResult;
        task.merge_result = mergeResult.artifacts!;

        return {
            ok: true,
            status: 'passed',
            artifacts: task
        };
    }
}
