import type { GoogleGenAI } from "@google/genai";
import { describe, expect, it, jest } from "@jest/globals";

import { GovernanceService } from "../GovernanceService.ts";

function createMockAi(): GoogleGenAI {
  return {
    models: {
      generateContent: jest.fn(async ({ contents }: { contents: string }) => {
        const prompt = contents.toLowerCase();
        if (prompt.includes("delete")) {
          return { text: '{"escalate": true, "reason": "High risk: deletion"}' };
        }
        return { text: '{"escalate": false, "reason": "Low risk"}' };
      }),
    },
  } as unknown as GoogleGenAI;
}

describe("GovernanceService", () => {
  describe("requiresHumanEscalation", () => {
    it("does not escalate low-risk tasks before calling the model", async () => {
      const ai = createMockAi();
      const result = await GovernanceService.requiresHumanEscalation(
        {
          id: "low-risk",
          description: "Update UI button color",
          risk_score: 40,
        },
        ai,
      );

      expect(result).toBe(false);
      expect(ai.models.generateContent).not.toHaveBeenCalled();
    });

    it("escalates catastrophic high-risk tasks", async () => {
      const ai = createMockAi();
      const result = await GovernanceService.requiresHumanEscalation(
        {
          id: "high-risk",
          description: "Delete all user data",
          risk_score: 90,
        },
        ai,
      );

      expect(result).toBe(true);
      expect(ai.models.generateContent).toHaveBeenCalledTimes(1);
    });

    it("does not escalate high-risk tasks when the model returns false", async () => {
      const ai = createMockAi();
      const result = await GovernanceService.requiresHumanEscalation(
        {
          id: "growth-path",
          description: "Expand adaptive governance dashboards",
          risk_score: 90,
        },
        ai,
      );

      expect(result).toBe(false);
      expect(ai.models.generateContent).toHaveBeenCalledTimes(1);
    });
  });

  describe("isPathAllowed", () => {
    it("allows expected workspace paths", () => {
      const allowedPaths = [
        "src/App.tsx",
        "server/server.ts",
        "app/main.tsx",
        "core/agents/runtime.ts",
        "docs/rituals.md",
        "tasks.json",
      ];

      for (const targetPath of allowedPaths) {
        expect(GovernanceService.isPathAllowed(targetPath)).toBe(true);
      }
    });

    it("blocks sensitive and build paths", () => {
      const forbiddenPaths = [
        ".env",
        ".git/config",
        "secrets/key.txt",
        "node_modules/express/index.js",
        "dist/index.html",
        "build/main.js",
        "audit.log",
      ];

      for (const targetPath of forbiddenPaths) {
        expect(GovernanceService.isPathAllowed(targetPath)).toBe(false);
      }
    });

    it("blocks absolute and out-of-scope paths", () => {
      const outsidePaths = ["/etc/passwd", "README.md", "../server.ts"];

      for (const targetPath of outsidePaths) {
        expect(GovernanceService.isPathAllowed(targetPath)).toBe(false);
      }
    });
  });
});
