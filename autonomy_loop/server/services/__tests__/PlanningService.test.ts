import type { GoogleGenAI } from "@google/genai";
import { afterEach, beforeEach, describe, expect, it, jest } from '@jest/globals';
import type { Task, TaskPlan } from '../../../src/types.ts';
import { EquilibriumService } from '../EquilibriumService.ts';
import { GovernanceService } from '../GovernanceService.ts';
import { PlanningService } from '../PlanningService.ts';

function createMockAi(mockPlanResponse: any): GoogleGenAI {
    return {
        models: {
            generateContent: jest.fn().mockResolvedValue({
                text: JSON.stringify(mockPlanResponse)
            }),
        },
    } as unknown as GoogleGenAI;
}

const DUMMY_TASK: Task = {
    id: "test-task",
    description: "Test description",
    status: "new",
    priority: "normal",
    created_at: new Date().toISOString(),
    risk_score: 5,
};

describe('PlanningService', () => {
    beforeEach(() => {
        jest.spyOn(GovernanceService, 'requiresHumanEscalation').mockResolvedValue(false);
        jest.spyOn(EquilibriumService, 'evaluate').mockResolvedValue({
            balanced: true,
            reason: "Balanced"
        });
    });

    afterEach(() => {
        jest.restoreAllMocks();
    });

    it('fails immediately if GovernanceService requires escalation', async () => {
        jest.spyOn(GovernanceService, 'requiresHumanEscalation').mockResolvedValue(true);

        const ai = createMockAi({});

        const result = await PlanningService.planTask(DUMMY_TASK, ai);

        expect(result.ok).toBe(false);
        expect(result.error).toContain('human escalation');
        expect((ai.models as any).generateContent).not.toHaveBeenCalled();
    });

    it('proceeds despite escalation if isProposal is true', async () => {
        jest.spyOn(GovernanceService, 'requiresHumanEscalation').mockResolvedValue(true);

        const mockPlan: TaskPlan = {
            steps: ["Analyze architecture", "Draft proposal"],
            files_to_change: [],
            tests_to_run: [],
            expected_behavior: "Proposal created",
            rollback_points: [],
            risk_assessment: "Low",
            safety_measures: []
        };

        const ai = createMockAi(mockPlan);

        const result = await PlanningService.planTask(DUMMY_TASK, ai, true); // isProposal = true

        expect(result.ok).toBe(true);
        expect((ai.models as any).generateContent).toHaveBeenCalled();
    });

    it('fails if EquilibriumService evaluates the plan as unbalanced', async () => {
        jest.spyOn(EquilibriumService, 'evaluate').mockResolvedValue({
            balanced: false,
            reason: "Expansion force exceeds safety"
        });

        const mockPlan: TaskPlan = {
            steps: ["Change everything immediately"],
            files_to_change: ["*"],
            tests_to_run: [],
            expected_behavior: "Complete rewrite",
            rollback_points: [],
            risk_assessment: "Catastrophic",
            safety_measures: []
        };

        const ai = createMockAi(mockPlan);

        const result = await PlanningService.planTask(DUMMY_TASK, ai);

        expect(result.ok).toBe(false);
        expect(result.error).toContain('Expansion force exceeds safety');
    });

    it('fails if the generated plan has no steps', async () => {
        const mockPlan: Partial<TaskPlan> = {
            steps: [], // empty steps
        };

        const ai = createMockAi(mockPlan);

        const result = await PlanningService.planTask(DUMMY_TASK, ai);

        expect(result.ok).toBe(false);
        expect(result.error).toContain('Generated plan is empty');
    });

    it('succeeds and returns artifacts for a well-formed balanced plan', async () => {
        const mockPlan: TaskPlan = {
            steps: ["Step 1", "Step 2"],
            files_to_change: ["src/index.ts"],
            tests_to_run: ["npm test"],
            expected_behavior: "It works",
            rollback_points: ["Commit abc"],
            risk_assessment: "None",
            safety_measures: ["Run tests"]
        };

        const ai = createMockAi(mockPlan);

        const result = await PlanningService.planTask(DUMMY_TASK, ai);

        expect(result.ok).toBe(true);
        expect(result.status).toBe('passed');
        expect(result.artifacts).toEqual(mockPlan);
    });
});
