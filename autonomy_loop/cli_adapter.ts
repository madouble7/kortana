#!/usr/bin/env node
import fs from 'node:fs';
import { OrchestratorService } from './server/services/OrchestratorService.ts';
import type { Task } from './src/types.ts';

/**
 * Autonomy Loop CLI Adapter
 *
 * Provides a safe external boundary to execute the sandbox loop.
 * Accepts a JSON-serialized Task via stdin.
 * Emits a JSON-serialized ServiceResult via stdout.
 *
 * Defaults to dry-run mode unless --danger-live-run is explicitly passed.
 */

// Redirect console.log and console.warn to stderr so they don't break JSON output on stdout
console.log = console.error;
console.warn = console.error;

async function main() {
    const args = process.argv.slice(2);
    const isLiveRun = args.includes('--danger-live-run');
    const dryRun = !isLiveRun;

    // Read payload from stdin
    const input = fs.readFileSync(0, 'utf-8');

    if (!input.trim()) {
        console.error(JSON.stringify({
            ok: false,
            status: 'failed',
            error: 'No input provided to stdin'
        }));
        process.exit(1);
    }

    let task: Task;
    try {
        task = JSON.parse(input) as Task;
    } catch (e: any) {
        console.error(JSON.stringify({
            ok: false,
            status: 'failed',
            error: `Failed to parse input JSON: ${e.message}`
        }));
        process.exit(1);
    }

    if (!task.id || !task.description) {
        console.error(JSON.stringify({
            ok: false,
            status: 'failed',
            error: 'Invalid Task format: Requires at least id and description'
        }));
        process.exit(1);
    }

    let aiClient: any;
    if (process.env.GEMINI_API_KEY) {
        const { GoogleGenAI } = await import('@google/genai');
        aiClient = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
    } else {
        // Fallback or dry-run mock
        aiClient = {
            models: {
                generateContent: async () => ({
                    text: JSON.stringify({
                        steps: ["Mocked step 1"],
                        files_to_change: ["src/mock.ts"],
                        tests_to_run: ["src/mock.test.ts"],
                        expected_behavior: "It works.",
                        rollback_points: ["Before"],
                        files: [
                            { path: "src/mock.ts", content: `export const mocked = ${Date.now()};` }
                        ],
                        commit_msg: "feat: mock",
                        approved: true,
                        blocking_issues: [],
                        non_blocking_notes: [],
                        risk_reassessment: 1
                    })
                })
            }
        };
    }

    try {
        // Execute the loop
        const result = await OrchestratorService.executeLoop(task, aiClient, { dryRun });

        // Output result to stdout cleanly
        process.stdout.write(JSON.stringify(result, null, 2) + "\n");
        process.exit(result.ok ? 0 : 1);
    } catch (error: any) {
        console.error(JSON.stringify({
            ok: false,
            status: 'failed',
            error: `Uncaught Orchestration Error: ${error.message}`
        }, null, 2));
        process.exit(1);
    }
}

main().catch(e => {
    console.error(JSON.stringify({ ok: false, error: e.message }));
    process.exit(1);
});
