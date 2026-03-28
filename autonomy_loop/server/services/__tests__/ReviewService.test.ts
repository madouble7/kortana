import type { GoogleGenAI } from "@google/genai";
import { describe, expect, it, jest } from "@jest/globals";

import type { ReviewSummary, Task, TaskPlan } from "../../../src/types.ts";
import { ReviewService } from "../ReviewService.ts";

function createMockAi(review: ReviewSummary): GoogleGenAI {
  return {
    models: {
      generateContent: jest.fn(async () => ({
        text: JSON.stringify(review),
      })),
    },
  } as unknown as GoogleGenAI;
}

function createTask(overrides: Partial<Task> = {}): Task {
  const plan: TaskPlan = {
    steps: ["apply targeted change", "run verification"],
    files_to_change: ["src/App.tsx"],
    tests_to_run: ["npm test"],
    expected_behavior: "feature behaves correctly",
    rollback_points: ["git revert HEAD"],
    risk_assessment: "low",
    safety_measures: ["run test suite"],
  };

  return {
    id: "review-task",
    description: "Review autonomous code changes",
    priority: "normal",
    status: "tested",
    created_at: new Date().toISOString(),
    risk_score: 25,
    plan,
    changeset: {
      files_changed: ["src/App.tsx"],
      diff: "@@ -1,3 +1,3 @@\n-console.log('old')\n+console.log('new')",
    },
    test_report: {
      command: "npm test",
      exit_code: 0,
      stdout: "all tests passed",
      stderr: "",
    },
    ...overrides,
  };
}

describe("ReviewService", () => {
  it("fails immediately when required artifacts are missing", async () => {
    const task = createTask({ plan: undefined });
    const ai = createMockAi({
      approved: true,
      blocking_issues: [],
      non_blocking_notes: [],
      risk_reassessment: 10,
    });

    const result = await ReviewService.reviewTask(task, ai);

    expect(result.ok).toBe(false);
    expect(result.error).toContain("Missing required artifacts for review");
    expect(ai.models.generateContent).not.toHaveBeenCalled();
  });

  it("returns a structured approved review when artifacts and tests are healthy", async () => {
    const expectedReview: ReviewSummary = {
      approved: true,
      blocking_issues: [],
      non_blocking_notes: ["diff is coherent"],
      risk_reassessment: 18,
    };
    const task = createTask();
    const ai = createMockAi(expectedReview);

    const result = await ReviewService.reviewTask(task, ai);

    expect(result.ok).toBe(true);
    expect(result.status).toBe("passed");
    expect(result.artifacts).toEqual(expectedReview);
    expect(ai.models.generateContent).toHaveBeenCalledTimes(1);
  });

  it("forces rejection when the test report exit code is non-zero", async () => {
    const task = createTask({
      test_report: {
        command: "npm test",
        exit_code: 1,
        stdout: "1 failing test",
        stderr: "AssertionError",
      },
    });
    const ai = createMockAi({
      approved: true,
      blocking_issues: [],
      non_blocking_notes: ["looks good at a glance"],
      risk_reassessment: 40,
    });

    const result = await ReviewService.reviewTask(task, ai);

    expect(result.ok).toBe(true);
    expect(result.artifacts?.approved).toBe(false);
    expect(result.artifacts?.blocking_issues).toContain(
      "Hard Gate: Tests failed (exit code != 0)",
    );
  });

  it("returns a failed service result when the AI call throws", async () => {
    const task = createTask();
    const ai = {
      models: {
        generateContent: jest.fn(async () => {
          throw new Error("review model unavailable");
        }),
      },
    } as unknown as GoogleGenAI;

    const result = await ReviewService.reviewTask(task, ai);

    expect(result.ok).toBe(false);
    expect(result.status).toBe("failed");
    expect(result.error).toContain("review model unavailable");
  });
});
