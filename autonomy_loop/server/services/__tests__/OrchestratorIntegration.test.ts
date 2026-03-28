import { beforeEach, describe, expect, it, jest } from '@jest/globals';
import type { Task } from '../../../src/types.ts';
import { MergeService } from '../MergeService.ts';
import { OrchestratorService } from '../OrchestratorService.ts';
import { PlanningService } from '../PlanningService.ts';
import { ReviewService } from '../ReviewService.ts';
import { TestRunnerService } from '../TestRunnerService.ts';
import { WorkspaceService } from '../WorkspaceService.ts';

describe('Thin Orchestration Integration', () => {
    const MOCK_AI = {};

    beforeEach(() => {
        jest.restoreAllMocks();
    });

    const createFreshTask = (): Task => ({
        id: "orch-task-1",
        status: "new",
        description: "End to end trial",
        priority: "normal",
        created_at: new Date().toISOString(),
    });

    it('stops the chain early if planning fails', async () => {
        jest.spyOn(PlanningService, 'planTask').mockResolvedValue({
            ok: false,
            status: "blocked",
            error: "Task escalated by Governance"
        });

        const workspaceSpy = jest.spyOn(WorkspaceService, 'executePlan');
        const mergeSpy = jest.spyOn(MergeService, 'mergeTask');

        const result = await OrchestratorService.executeLoop(createFreshTask(), MOCK_AI);

        expect(result.ok).toBe(false);
        expect(result.error).toContain("escalated");
        expect(workspaceSpy).not.toHaveBeenCalled();
        expect(mergeSpy).not.toHaveBeenCalled();
    });

    it('stops if tests fail and review correctly rejects the merge', async () => {
        jest.spyOn(PlanningService, 'planTask').mockResolvedValue({
            ok: true,
            status: "passed",
            artifacts: { steps: [], files_to_change: [], tests_to_run: [], expected_behavior: "", rollback_points: [] }
        });

        jest.spyOn(WorkspaceService, 'executePlan').mockResolvedValue({
            ok: true,
            status: "passed",
            artifacts: { files_changed: ["src/app.ts"], diff: "+code" }
        });

        // Test runner returns non-zero code. ok=false, but we have artifacts.
        jest.spyOn(TestRunnerService, 'runTests').mockResolvedValue({
            ok: false,
            status: "failed",
            artifacts: { command: "npm test", exit_code: 1, stdout: "", stderr: "FAIL" }
        });

        // Review service analyzes the failed tests and rejects
        jest.spyOn(ReviewService, 'reviewTask').mockResolvedValue({
            ok: true,
            status: "passed",
            artifacts: { approved: false, blocking_issues: ["Tests failed"], non_blocking_notes: [], risk_reassessment: 1 }
        });

        const mergeSpy = jest.spyOn(MergeService, 'mergeTask');
        const result = await OrchestratorService.executeLoop(createFreshTask(), MOCK_AI);

        expect(result.ok).toBe(true); // Review completed successfully, but returned approved=false
        expect(result.artifacts?.approved).toBe(false);
        expect(mergeSpy).not.toHaveBeenCalled(); // Merge was protected due to !approved
    });

    it('runs the full chain uninterrupted when all gates pass', async () => {
        jest.spyOn(PlanningService, 'planTask').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { steps: [], files_to_change: [], tests_to_run: [], expected_behavior: "", rollback_points: [] }
        });
        jest.spyOn(WorkspaceService, 'executePlan').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { files_changed: ["src/app.ts"], diff: "+code" }
        });
        jest.spyOn(TestRunnerService, 'runTests').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { command: "npm test", exit_code: 0, stdout: "PASS", stderr: "" }
        });
        jest.spyOn(ReviewService, 'reviewTask').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { approved: true, blocking_issues: [], non_blocking_notes: [], risk_reassessment: 1 }
        });
        jest.spyOn(MergeService, 'mergeTask').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { merge_sha: "abc1234", merged_at: new Date().toISOString() }
        });

        const result = await OrchestratorService.executeLoop(createFreshTask(), MOCK_AI);

        expect(result.ok).toBe(true);
        expect(result.status).toBe("passed");
        expect(PlanningService.planTask).toHaveBeenCalled();
        expect(WorkspaceService.executePlan).toHaveBeenCalled();
        expect(TestRunnerService.runTests).toHaveBeenCalled();
        expect(ReviewService.reviewTask).toHaveBeenCalled();
        expect(MergeService.mergeTask).toHaveBeenCalled();
    });

    it('blocks side effects when dryRun is true', async () => {
        jest.spyOn(PlanningService, 'planTask').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { steps: [], files_to_change: [], tests_to_run: [], expected_behavior: "", rollback_points: [] }
        });
        jest.spyOn(WorkspaceService, 'executePlan').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { files_changed: ["src/app.ts"], diff: "+code" }
        });
        jest.spyOn(TestRunnerService, 'runTests').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { command: "npm test", exit_code: 0, stdout: "PASS", stderr: "" }
        });
        jest.spyOn(ReviewService, 'reviewTask').mockResolvedValue({
            ok: true, status: "passed",
            artifacts: { approved: true, blocking_issues: [], non_blocking_notes: [], risk_reassessment: 1 }
        });

        const mergeSpy = jest.spyOn(MergeService, 'mergeTask');

        // Use a real task for safe passing
        const task = createFreshTask();

        const result = await OrchestratorService.executeLoop(task, MOCK_AI, { dryRun: true });

        // dryRun should intercept before merge
        expect(result.ok).toBe(true);
        expect(result.status).toBe("passed");

        // Assert Merge was NOT called
        expect(mergeSpy).not.toHaveBeenCalled();

        // Assert the artifact matches the mutated task including the dryRun manifest
        const outTask = result.artifacts as Task;
        expect(outTask.deployment_manifest).toBeDefined();
        expect(outTask.deployment_manifest?.dryRun).toBe(true);
        expect(outTask.deployment_manifest?.status).toBe("success");
    });
});
