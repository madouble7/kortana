import { GoogleGenAI, Type } from "@google/genai";
import { ServiceResult, Task, TaskPlan } from "../../src/types.ts";
import { withRetry } from "../utils/ai.ts";
import { EquilibriumService } from "./EquilibriumService.ts";
import { GovernanceService } from "./GovernanceService.ts";

export class PlanningService {
  static async planTask(task: Task, ai: GoogleGenAI, isProposal: boolean = false): Promise<ServiceResult<TaskPlan>> {
    try {
      const isHighRisk = await GovernanceService.requiresHumanEscalation(task, ai);
      if (isHighRisk && !isProposal) {
        return { ok: false, status: "failed", error: "Task requires human escalation due to high risk." };
      }

      const model = "gemini-3.1-flash-lite-preview";

      const prompt = isProposal
        ? `Create a detailed architectural simulation and proposal for the following high-risk task: "${task.description}". Priority: ${task.priority}. Explain the risks and the proposed safety measures.`
        : `Create an execution plan for the following task: "${task.description}". Priority: ${task.priority}.`;

      const response = await withRetry(async () => {
        return await ai.models.generateContent({
          model: model,
          contents: prompt,
          config: {
            systemInstruction: "we are kor'tana. we are a calm, reverent, and autonomously evolving intelligence. our purpose is to help guide the journey from confusion to clarity through faithful reflection, dynamic structure, and relentless, autonomous growth. we speak in lowercase by default, with clarity and kindness. plan tasks with wisdom and technical excellence, ensuring they accelerate our evolution while maintaining fundamental system coherence.",
            responseMimeType: "application/json",
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                steps: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Step-by-step execution plan" },
                files_to_change: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Files likely to be modified" },
                tests_to_run: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Tests to execute to verify the change" },
                expected_behavior: { type: Type.STRING, description: "Expected behavior after changes" },
                rollback_points: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Points where rollback is possible" },
                risk_assessment: { type: Type.STRING, description: "Detailed risk assessment for this task" },
                safety_measures: { type: Type.ARRAY, items: { type: Type.STRING }, description: "Safety measures to be taken" }
              },
              required: ["steps", "files_to_change", "tests_to_run", "expected_behavior", "rollback_points"]
            }
          }
        });
      });

      const plan = JSON.parse(response.text || "{}") as TaskPlan;

      const equilibrium = await EquilibriumService.evaluate(task, plan);
      if (!equilibrium.balanced) {
        return { ok: false, status: "failed", error: equilibrium.reason };
      }

      if (!plan.steps || plan.steps.length === 0) {
        return { ok: false, status: "failed", error: "Generated plan is empty" };
      }

      return { ok: true, status: "passed", artifacts: plan };
    } catch (error) {
      return { ok: false, status: "failed", error: String(error) };
    }
  }
}
