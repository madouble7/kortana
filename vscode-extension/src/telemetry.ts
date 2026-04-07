import * as fs from "fs";
import * as path from "path";
import * as vscode from "vscode";
import axios from "axios";

/**
 * Monastery telemetry - silent, ambient observation.
 * Focuses on state and friction, not keystrokes.
 */
export class FocusTelemetry {
    private activeContexts: Map<string, number> = new Map();
    private updateInterval: NodeJS.Timeout | null = null;
    private sessionInterval: NodeJS.Timeout | null = null;
    private frictionInterval: NodeJS.Timeout | null = null;
    
    private readonly FOCUS_FILE = path.join("c:", "kortana", "mcp-server", "current_focus.json");
    private readonly MEMORY_ENDPOINT = "http://localhost:8000/api/consciousness/memory/self";
    
    // Friction tracking
    private currentErrorSignature: string | null = null;
    private errorStartTime: number | null = null;
    
    // Config
    private readonly UPDATE_MS = 60_000; // 1 minute focus write
    private readonly SESSION_MS = 45 * 60_000; // 45 minutes flow synthesis
    private readonly FRICTION_THRESHOLD_MS = 10 * 60_000; // 10 minutes same error
    
    public start(context: vscode.ExtensionContext) {
        // Track time spent in the active editor
        this.updateInterval = setInterval(() => this.recordTick(), 1000);
        
        // Write the local file for the ambient heartbeat
        const fileWriter = setInterval(() => this.writeFocusSync(), this.UPDATE_MS);
        context.subscriptions.push({ dispose: () => clearInterval(fileWriter) });
        
        // Check for persistent friction
        this.frictionInterval = setInterval(() => this.checkFriction(), 60_000);
        
        // Summarize flow
        this.sessionInterval = setInterval(() => this.summarizeFlow(), this.SESSION_MS);
        
        // Cleanup
        context.subscriptions.push({
            dispose: () => {
                if (this.updateInterval) clearInterval(this.updateInterval);
                if (this.frictionInterval) clearInterval(this.frictionInterval);
                if (this.sessionInterval) clearInterval(this.sessionInterval);
                this.writeFocusSync();
            }
        });
    }
    
    private recordTick() {
        const editor = vscode.window.activeTextEditor;
        if (!editor || !editor.document) return;
        
        const fsPath = editor.document.uri.fsPath;
        // Normalize to relative path if possible to keep it clean
        const relPath = vscode.workspace.asRelativePath(fsPath);
        
        const currentSeconds = this.activeContexts.get(relPath) || 0;
        this.activeContexts.set(relPath, currentSeconds + 1);
    }
    
    private writeFocusSync() {
        try {
            const editor = vscode.window.activeTextEditor;
            const contextObj = Object.fromEntries(this.activeContexts);
            
            const state = {
                timestamp: new Date().toISOString(),
                current_active_file: editor?.document.uri.fsPath || null,
                session_focus_seconds: contextObj
            };
            
            fs.mkdirSync(path.dirname(this.FOCUS_FILE), { recursive: true });
            fs.writeFileSync(this.FOCUS_FILE, JSON.stringify(state, null, 2), "utf-8");
        } catch {
            // Ignore - silent fail for telemetry
        }
    }
    
    private checkFriction() {
        try {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                this.clearFriction();
                return;
            }
            
            const diags = vscode.languages.getDiagnostics(editor.document.uri);
            const errors = diags.filter(d => d.severity === vscode.DiagnosticSeverity.Error);
            
            if (errors.length === 0) {
                this.clearFriction();
                return;
            }
            
            // Signature is the file + the first error message
            const signature = `${editor.document.uri.fsPath}::${errors[0].message}`;
            
            if (this.currentErrorSignature !== signature) {
                this.currentErrorSignature = signature;
                this.errorStartTime = Date.now();
            } else {
                const duration = Date.now() - (this.errorStartTime || 0);
                if (duration > this.FRICTION_THRESHOLD_MS) {
                    // Fire friction event
                    this.sendMemoryEvent(
                        `Observed significant friction: Matt has been struggling with the same error in ${vscode.workspace.asRelativePath(editor.document.uri.fsPath)} for over 10 minutes. Error: "${errors[0].message}"`,
                        ["vscode", "telemetry", "friction"]
                    );
                    
                    // Reset threshold so we don't spam
                    this.errorStartTime = Date.now();
                }
            }
        } catch {
             // Silently fail
        }
    }
    
    private clearFriction() {
        this.currentErrorSignature = null;
        this.errorStartTime = null;
    }
    
    private summarizeFlow() {
        if (this.activeContexts.size === 0) return;
        
        let totalSeconds = 0;
        const sortedContexts = [...this.activeContexts.entries()].sort((a, b) => b[1] - a[1]);
        
        for (const [_, seconds] of sortedContexts) {
            totalSeconds += seconds;
        }
        
        if (totalSeconds < 300) {
            // Less than 5 minutes of total activity in this 45 min block, ignore (away from keyboard)
            this.activeContexts.clear();
            return;
        }
        
        const topFiles = sortedContexts.slice(0, 3).map(([file, secs]) => {
            const percentage = Math.round((secs / totalSeconds) * 100);
            return `${file} (${percentage}%)`;
        });
        
        const summary = `Observed a 45-minute flow state block. Matt's primary workspace focus was heavily distributed across: ${topFiles.join(', ')}.`;
        
        this.sendMemoryEvent(summary, ["vscode", "telemetry", "flow"]);
        
        // Reset for the next session
        this.activeContexts.clear();
        this.writeFocusSync();
    }
    
    private async sendMemoryEvent(summary: string, tags: string[]) {
        try {
            await axios.post(this.MEMORY_ENDPOINT, {
                summary,
                tags,
                source: "vscode-telemetry"
            }, { timeout: 3000 });
        } catch {
            // Fails silently to prevent annoyance
        }
    }
}
