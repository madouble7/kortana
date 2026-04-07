import { describe, expect, it } from '@jest/globals';
import type { Task } from '../../../src/types.ts';
import { MergeService } from '../MergeService.ts';

const createBaseTask = (): Task => ({
    id: "test-task-123",
    status: "approved",
    description: "Test merge capabilities",
    priority: "normal",
    created_at: new Date().toISOString(),
});

describe('MergeService', () => {
    it('blocks merge if review is not approved', async () => {
        const task = createBaseTask();
        task.review_summary = {
            approved: false,
            blocking_issues: [],
            non_blocking_notes: ["Needs more work"],
            risk_reassessment: 1
        };
        task.test_report = {
            command: "npm test",
            exit_code: 0,
            stdout: "All tests passed",
            stderr: ""
        };

        const result = await MergeService.mergeTask(task);
        expect(result.ok).toBe(false);
        expect(result.status).toBe("blocked");
        expect(result.error).toContain("not approved for merge");
    });

    it('blocks merge if test_report exit_code is not 0', async () => {
        const task = createBaseTask();
        task.review_summary = {
            approved: true,
            blocking_issues: [],
            non_blocking_notes: ["LGTM"],
            risk_reassessment: 1
        };
        task.test_report = {
            command: "npm test",
            exit_code: 1,
            stdout: "Tests failed with errors",
            stderr: "Error details"
        };

        const result = await MergeService.mergeTask(task);
        expect(result.ok).toBe(false);
        expect(result.status).toBe("blocked");
        expect(result.error).toContain("Tests did not pass");
    });

    it('blocks merge if there are blocking review issues', async () => {
        const task = createBaseTask();
        task.review_summary = {
            approved: true,
            blocking_issues: ["Rename variable X to Y"],
            non_blocking_notes: ["LGTM"],
            risk_reassessment: 1
        };
        task.test_report = {
            command: "npm test",
            exit_code: 0,
            stdout: "All tests passed",
            stderr: ""
        };

        const result = await MergeService.mergeTask(task);
        expect(result.ok).toBe(false);
        expect(result.status).toBe("blocked");
        expect(result.error).toContain("Open blocking review comments exist");
    });

    it('successfully merges when all conditions are met', async () => {
        const task = createBaseTask();
        task.review_summary = {
            approved: true,
            blocking_issues: [],
            non_blocking_notes: ["Perfect!"],
            risk_reassessment: 1
        };
        task.test_report = {
            command: "npm test",
            exit_code: 0,
            stdout: "All tests passed",
            stderr: ""
        };

        const result = await MergeService.mergeTask(task);
        expect(result.ok).toBe(true);
        expect(result.status).toBe("passed");
        expect(result.artifacts).toBeDefined();
        expect(result.artifacts?.merge_sha).toMatch(/^sha_[a-z0-9]+$/);
        expect(result.artifacts?.pr_url).toContain("https://github.com/simulated-org/repo/pull/");
        expect(result.artifacts?.merged_at).toBeDefined();
    });
});
