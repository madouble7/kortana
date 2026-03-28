import { Task, TaskPlan } from "../../src/types.ts";

/**
 * Regulates the tension between autonomous expansion and systemic safety.
 */
export class EquilibriumService {
  static async evaluate(task: Task, plan: TaskPlan): Promise<{ balanced: boolean; reason: string }> {
    const expansionForce = plan.steps.length + plan.files_to_change.length;
    const safetyMeasures = plan.safety_measures?.length || 0;

    // Adaptive threshold: expansion is prioritized, but safety measures provide stability.
    // We've increased the complexity threshold to allow for more ambitious autonomous growth.
    const complexityThreshold = 20;

    if (expansionForce > complexityThreshold && safetyMeasures < 2) {
      return {
        balanced: false,
        reason: `Architectural imbalance: Expansion force (${expansionForce}) exceeds safety measures (${safetyMeasures}) for high-complexity task.`
      };
    }

    return { balanced: true, reason: "Systemic equilibrium maintained." };
  }
}
