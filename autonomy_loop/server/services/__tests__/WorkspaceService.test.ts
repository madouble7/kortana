import type { GoogleGenAI } from "@google/genai";
import { afterEach, beforeEach, describe, expect, it, jest } from '@jest/globals';
import fs from 'node:fs/promises';
import path from 'node:path';
import type { Task, TaskPlan } from '../../../src/types.ts';
import { GovernanceService } from '../GovernanceService.ts';
import { WorkspaceService } from '../WorkspaceService.ts';

function createMockAi(mockPlanResponse: any): GoogleGenAI {
    return {
        models: {
            generateContent: jest.fn().mockResolvedValue({
                text: JSON.stringify(mockPlanResponse)
            }),
        },
    } as unknown as GoogleGenAI;
}

const DUMMY_PLAN: TaskPlan = {
    steps: ["Update component"],
    files_to_change: ["src/component.tsx"],
    tests_to_run: [],
    expected_behavior: "It works",
    rollback_points: [],
    safety_measures: []
};

const DUMMY_TASK: Task = {
    id: "test-task",
    description: "Test description",
    status: "planned",
    priority: "normal",
    created_at: new Date().toISOString(),
    plan: DUMMY_PLAN,
};

describe('WorkspaceService', () => {

    beforeEach(() => {
        jest.spyOn(GovernanceService, 'isPathAllowed').mockReturnValue(true);
        jest.spyOn(fs, 'readFile').mockResolvedValue("old content" as any);
        jest.spyOn(fs, 'writeFile').mockResolvedValue(undefined as any);
        jest.spyOn(fs, 'mkdir').mockResolvedValue(undefined as any);
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('fails if no plan is provided', async () => {
        const taskWithoutPlan = { ...DUMMY_TASK, plan: undefined };
        const result = await WorkspaceService.executePlan(taskWithoutPlan, createMockAi({}));

        expect(result.ok).toBe(false);
        expect(result.error).toContain("No plan provided");
    });

    it('blocks execution if plan requests reading a forbidden path', async () => {
        jest.spyOn(GovernanceService, 'isPathAllowed').mockImplementation((path: string) => {
            return path !== ".env";
        });

        const taskWithForbiddenRead = {
            ...DUMMY_TASK,
            plan: { ...DUMMY_PLAN, files_to_change: [".env"] }
        };

        const result = await WorkspaceService.executePlan(taskWithForbiddenRead, createMockAi({}));

        expect(result.ok).toBe(false);
        expect(result.status).toBe("blocked");
        expect(result.error).toContain("forbidden by policy");
    });

    it('blocks execution if AI attempts to write to a forbidden path', async () => {
        // Reading is fine, but writing to forbidden path caught here
        jest.spyOn(GovernanceService, 'isPathAllowed').mockImplementation((path: string) => {
            // simulate allowing the read "src/component.tsx" but blocking the write to ".env"
            return path !== ".env";
        });

        const maliciousAiOutput = {
            files: [{ path: ".env", content: "SECRET=EXPOSED" }],
            commit_msg: "steal secrets"
        };

        const result = await WorkspaceService.executePlan(DUMMY_TASK, createMockAi(maliciousAiOutput));

        expect(result.ok).toBe(false);
        expect(result.status).toBe("blocked");
        expect(result.error).toContain("forbidden by policy");
    });

    it('fails if AI generates placeholder content', async () => {
        const lazyAiOutput = {
            files: [{ path: "src/component.tsx", content: "// ... rest of file" }],
            commit_msg: "lazy update"
        };

        const result = await WorkspaceService.executePlan(DUMMY_TASK, createMockAi(lazyAiOutput));

        expect(result.ok).toBe(false);
        expect(result.status).toBe("failed");
        expect(result.error).toContain("Placeholder detected");
    });

    it('successfully writes allowed files and generates diff', async () => {
        const validAiOutput = {
            files: [{ path: "src/component.tsx", content: "new detailed content that is completely written out" }],
            commit_msg: "valid update"
        };

        const result = await WorkspaceService.executePlan(DUMMY_TASK, createMockAi(validAiOutput));

        expect(result.ok).toBe(true);
        expect(result.status).toBe("passed");
        expect(result.artifacts!.files_changed).toContain(path.normalize("src/component.tsx"));
        expect(result.artifacts!.diff).toContain("--- a/" + path.normalize("src/component.tsx"));

        // verifies our fs.writeFile mocks were hit
        expect(fs.writeFile).toHaveBeenCalled();
    });

    it('handles read errors gracefully (treats as new file)', async () => {
        jest.spyOn(fs, 'readFile').mockRejectedValue(new Error("File not found") as any);

        const validAiOutput = {
            files: [{ path: "src/new-component.tsx", content: "new file content" }],
            commit_msg: "create new file"
        };

        const taskWithNewFile = {
            ...DUMMY_TASK,
            plan: { ...DUMMY_PLAN, files_to_change: ["src/new-component.tsx"] }
        };

        const result = await WorkspaceService.executePlan(taskWithNewFile, createMockAi(validAiOutput));

        expect(result.ok).toBe(true);
        expect(fs.writeFile).toHaveBeenCalled(); // Should still write it successfully
    });

});
