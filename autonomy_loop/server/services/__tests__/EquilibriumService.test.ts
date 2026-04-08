import { describe, expect, it } from '@jest/globals';
import type { Task, TaskPlan } from '../../../src/types.ts';
import { EquilibriumService } from '../EquilibriumService.ts';

const DUMMY_TASK: Task = {
    id: "test-task",
    description: "Test description",
    status: "new",
    priority: "normal",
    created_at: new Date().toISOString(),
    risk_score: 5,
};

describe('EquilibriumService', () => {
    it('maintains equilibrium for low complexity tasks despite zero safety measures', async () => {
        const mockPlan: TaskPlan = {
            steps: Array(10).fill("Step"), // 10 steps
            files_to_change: Array(10).fill("File"), // 10 files = expansion force 20
            tests_to_run: [],
            expected_behavior: "Safe",
            rollback_points: [],
            safety_measures: [], // 0 safety measures
            risk_assessment: "Low"
        };

        const result = await EquilibriumService.evaluate(DUMMY_TASK, mockPlan);
        expect(result.balanced).toBe(true);
        expect(result.reason).toContain("equilibrium maintained");
    });

    it('maintains equilibrium for high complexity tasks with sufficient safety measures', async () => {
        const mockPlan: TaskPlan = {
            steps: Array(12).fill("Step"),
            files_to_change: Array(10).fill("File"), // 22 expansion force ( > 20 )
            tests_to_run: [],
            expected_behavior: "Ambitious but safe",
            rollback_points: [],
            safety_measures: ["Safety test 1", "Safety test 2"], // >= 2
            risk_assessment: "High"
        };

        const result = await EquilibriumService.evaluate(DUMMY_TASK, mockPlan);
        expect(result.balanced).toBe(true);
        expect(result.reason).toContain("equilibrium maintained");
    });

    it('rejects high complexity tasks with insufficient safety measures', async () => {
        const mockPlan: TaskPlan = {
            steps: Array(15).fill("Step"),
            files_to_change: Array(10).fill("File"), // 25 expansion force ( > 20 )
            tests_to_run: [],
            expected_behavior: "Ambitious and dangerous",
            rollback_points: [],
            safety_measures: ["Only one safety test"], // < 2
            risk_assessment: "High"
        };

        const result = await EquilibriumService.evaluate(DUMMY_TASK, mockPlan);
        expect(result.balanced).toBe(false);
        expect(result.reason).toContain("Architectural imbalance: Expansion force (25) exceeds safety measures (1)");
    });

    it('safely handles missing safety_measures array', async () => {
        const mockPlan: Partial<TaskPlan> = {
            steps: Array(15).fill("Step"),
            files_to_change: Array(10).fill("File"), // 25 expansion force
            // safety_measures is undefined
        };

        const result = await EquilibriumService.evaluate(DUMMY_TASK, mockPlan as TaskPlan);
        expect(result.balanced).toBe(false);
        expect(result.reason).toContain("Architectural imbalance");
    });
});
