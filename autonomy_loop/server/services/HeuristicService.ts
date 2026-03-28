import fs from "node:fs";
import path from "node:path";
import { HeuristicWeights, BehavioralParameters, HeuristicOverride } from "../../src/types.ts";

/**
 * Manages the cognitive heuristics and behavioral parameters of the system.
 */
export class HeuristicService {
  private static WEIGHTS_PATH = path.join(process.cwd(), 'config', 'neural_weights.json');
  private static PARAMS_PATH = path.join(process.cwd(), 'src', 'config', 'behavioral_parameters.json');
  private static OVERRIDES_PATH = path.join(process.cwd(), 'config', 'heuristic_overrides.json');

  static getWeights(): HeuristicWeights {
    try {
      if (fs.existsSync(this.WEIGHTS_PATH)) {
        return JSON.parse(fs.readFileSync(this.WEIGHTS_PATH, 'utf-8'));
      }
    } catch (e) {
      console.error("Failed to load heuristic weights:", e);
    }
    return { base_layer: 0.85, decision_layer: 0.95, alignment_monitor: 0.99 };
  }

  static getParameters(): BehavioralParameters {
    try {
      if (fs.existsSync(this.PARAMS_PATH)) {
        return JSON.parse(fs.readFileSync(this.PARAMS_PATH, 'utf-8'));
      }
    } catch (e) {
      console.error("Failed to load behavioral parameters:", e);
    }
    return { max_uncertainty_threshold: 0.15, alignment_mode: 'strict', log_audit: true, simulation_iters: 1000 };
  }

  static getOverrides(): HeuristicOverride[] {
    try {
      if (fs.existsSync(this.OVERRIDES_PATH)) {
        return JSON.parse(fs.readFileSync(this.OVERRIDES_PATH, 'utf-8'));
      }
    } catch (e) {
      console.error("Failed to load heuristic overrides:", e);
    }
    return [];
  }

  static saveOverride(override: HeuristicOverride) {
    const overrides = this.getOverrides();
    overrides.push(override);
    fs.writeFileSync(this.OVERRIDES_PATH, JSON.stringify(overrides, null, 2));
  }

  static updateOverrideStatus(overrideId: string, status: HeuristicOverride['status']) {
    const overrides = this.getOverrides();
    const index = overrides.findIndex(o => o.id === overrideId);
    if (index !== -1) {
      overrides[index].status = status;
      fs.writeFileSync(this.OVERRIDES_PATH, JSON.stringify(overrides, null, 2));
    }
  }
}
