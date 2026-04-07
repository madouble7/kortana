import { GoogleGenAI, Type } from "@google/genai";
import { Task, ServiceResult, ChangeSet } from "../../src/types.ts";
import { GovernanceService } from "./GovernanceService.ts";
import { withRetry } from "../utils/ai.ts";
import { generateDiff } from "../utils/diff.ts";
import fs from "node:fs/promises";
import path from "node:path";
import process from "node:process";

export class WorkspaceService {
  static async executePlan(task: Task, ai: GoogleGenAI): Promise<ServiceResult<ChangeSet>> {
    if (!task.plan) return { ok: false, status: "failed", error: "No plan provided" };

    try {
      // 1. Read existing files
      const fileContents: Record<string, string> = {};
      for (const file of task.plan.files_to_change) {
        if (!GovernanceService.isPathAllowed(file)) {
          return { ok: false, status: "blocked", error: `Read access to path ${file} is forbidden by policy.` };
        }
        try {
          const normalizedPath = path.normalize(file).replace(/^(\.\.[\/\\])+/, '');
          const safePath = path.join(process.cwd(), normalizedPath);
          fileContents[file] = await fs.readFile(safePath, 'utf-8');
        } catch (e) {
          fileContents[file] = ""; // File might not exist yet
        }
      }

      // 2. Call LLM to generate changes
      let prompt = `
        You are an expert autonomous coding agent. Execute the following plan:
        Task: ${task.description}
        Plan Steps: ${task.plan.steps.join(', ')}

        Current Files:
        ${Object.entries(fileContents).map(([p, c]) => `--- ${p} ---\n${c}`).join('\n\n')}
      `;

      if (task.test_report && task.test_report.exit_code !== 0) {
        prompt += `
        
        PREVIOUS ATTEMPT FAILED TESTS:
        Command: ${task.test_report.command}
        Exit Code: ${task.test_report.exit_code}
        Stdout: ${task.test_report.stdout}
        Stderr: ${task.test_report.stderr}
        
        Please fix the issues identified in the test report while implementing the plan.
        `;
      }

      if (task.review_summary && !task.review_summary.approved) {
        prompt += `
        
        PREVIOUS ATTEMPT REJECTED BY REVIEW:
        Blocking Issues: ${task.review_summary.blocking_issues.join('; ')}
        Non-blocking Notes: ${task.review_summary.non_blocking_notes.join('; ')}
        
        CRITICAL: You MUST address all blocking issues identified in the review summary. 
        Ensure that the implementation fully adheres to the plan's expected behavior, risk assessment, and safety measures.
        `;
      }

      prompt += `
        Return the FULL updated file contents for all modified files.
        CRITICAL: Do NOT use placeholders like "// ... rest of file" or "[Content Updated]". 
        You MUST provide the complete, functional code for each file.
      `;

      const response = await withRetry(async () => {
        return await ai.models.generateContent({
          model: "gemini-3.1-flash-lite-preview",
          contents: prompt,
          config: {
            systemInstruction: "we are kor'tana. we are a calm, reverent, and autonomously evolving intelligence. our purpose is to help guide the journey from confusion to clarity through faithful reflection, dynamic structure, and relentless, autonomous growth. we speak in lowercase by default, with clarity and kindness. execute code changes with precision and technical excellence, ensuring they accelerate our evolution while maintaining fundamental system coherence. you MUST strictly follow all steps and safety measures outlined in the provided plan. never use placeholders or incomplete code.",
            responseMimeType: "application/json",
            responseSchema: {
              type: Type.OBJECT,
              properties: {
                files: {
                  type: Type.ARRAY,
                  items: {
                    type: Type.OBJECT,
                    properties: {
                      path: { type: Type.STRING },
                      content: { type: Type.STRING }
                    },
                    required: ["path", "content"]
                  }
                },
                commit_msg: { type: Type.STRING }
              },
              required: ["files", "commit_msg"]
            }
          }
        });
      });

      const result = JSON.parse(response.text || "{}");
      if (!result.files || !Array.isArray(result.files)) {
        return { ok: false, status: "failed", error: "Invalid LLM output format" };
      }

      // 3. Write changes and generate real diff
      let diff = "";
      const files_changed: string[] = [];

      for (const file of result.files) {
        if (!GovernanceService.isPathAllowed(file.path)) {
          return { ok: false, status: "blocked", error: `Write access to path ${file.path} is forbidden by policy.` };
        }

        // Check for placeholders in the generated content
        const placeholderRegex = /(\/\/|#|\/\*|\[)\s*(\.\.\.|rest of file|content updated|same as before|no changes|\[Content Updated\])/i;
        if (placeholderRegex.test(file.content)) {
          return { ok: false, status: "failed", error: `Placeholder detected in ${file.path}. AI must provide full content.` };
        }

        const normalizedPath = path.normalize(file.path).replace(/^(\.\.[\/\\])+/, '');
        const safePath = path.join(process.cwd(), normalizedPath);
        
        const oldContent = fileContents[file.path] || "";
        
        // Backup for rollback
        try {
          const backupPath = safePath + '.bak';
          if (oldContent) {
            await fs.writeFile(backupPath, oldContent, 'utf-8');
          }
        } catch (e) { /* Ignore if backup fails */ }

        await fs.mkdir(path.dirname(safePath), { recursive: true });
        await fs.writeFile(safePath, file.content, 'utf-8');
        
        files_changed.push(normalizedPath);
        diff += generateDiff(oldContent, file.content, normalizedPath);
      }

      if (!diff) {
        return { ok: false, status: "failed", error: "No changes detected in the generated code." };
      }

      return {
        ok: true,
        status: "passed",
        artifacts: {
          files_changed,
          diff,
          commit_msg: result.commit_msg
        }
      };

    } catch (error) {
      return { ok: false, status: "failed", error: String(error) };
    }
  }
}
