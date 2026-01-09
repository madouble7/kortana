/**
 * Autonomy Logger Service
 * Records all autonomous actions and maintains constellation coherence
 * Logs are appended to COVENANT_INDEX.md for persistent tracking
 */

import * as fs from 'fs';
import * as path from 'path';
import { workspace } from 'vscode';

export interface AutonomousAction {
    type: 'branch_creation' | 'merge' | 'deploy' | 'task_spawn' | 'analysis' | 'elevation' | 'sync';
    description: string;
    context?: Record<string, any>;
    impact?: string[];
    status: 'success' | 'failed' | 'pending';
    timestamp?: string;
}

export class AutonomyLogger {
    private covenantIndexPath: string;
    private workspaceRoot: string;

    constructor() {
        this.workspaceRoot = workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        this.covenantIndexPath = path.join(this.workspaceRoot, 'COVENANT_INDEX.md');
    }

    /**
     * Log an autonomous action to the covenant index
     */
    async logAction(action: AutonomousAction): Promise<void> {
        try {
            const timestamp = action.timestamp || new Date().toISOString();
            const dateTime = new Date(timestamp).toISOString().replace('T', ' ').substring(0, 19);

            let logEntry = `\n[${dateTime}] ${action.type.toUpperCase()}: ${action.description}\n`;

            if (action.context) {
                logEntry += `- Context: ${JSON.stringify(action.context, null, 2)}\n`;
            }

            if (action.impact && action.impact.length > 0) {
                logEntry += `- Impact: ${action.impact.join(', ')}\n`;
            }

            logEntry += `- Status: ${action.status}\n`;

            // Ensure the file exists
            await this.ensureCovenantIndex();

            // Append to the covenant index
            await fs.promises.appendFile(this.covenantIndexPath, logEntry, 'utf8');

            // Update the last sync timestamp
            await this.updateLastSync(timestamp);

            console.log(`📊 Autonomy action logged: ${action.type} - ${action.description}`);

        } catch (error) {
            console.error('Failed to log autonomous action:', error);
            throw error;
        }
    }

    /**
     * Log branch creation
     */
    async logBranchCreation(branchName: string, sourceBranch: string, reason: string): Promise<void> {
        await this.logAction({
            type: 'branch_creation',
            description: `Created branch '${branchName}' from '${sourceBranch}'`,
            context: { branchName, sourceBranch, reason },
            impact: ['New development branch spawned'],
            status: 'success'
        });
    }

    /**
     * Log merge operation
     */
    async logMerge(sourceBranch: string, targetBranch: string, prNumber?: number): Promise<void> {
        await this.logAction({
            type: 'merge',
            description: `Merged '${sourceBranch}' into '${targetBranch}'`,
            context: { sourceBranch, targetBranch, prNumber },
            impact: ['Code changes integrated', 'Branch lifecycle completed'],
            status: 'success'
        });
    }

    /**
     * Log deployment
     */
    async logDeployment(environment: string, version: string, url?: string): Promise<void> {
        await this.logAction({
            type: 'deploy',
            description: `Deployed version ${version} to ${environment}`,
            context: { environment, version, url },
            impact: ['New version live', 'Runtime permissions updated'],
            status: 'success'
        });
    }

    /**
     * Log task spawning
     */
    async logTaskSpawn(taskType: string, taskId: string, source: string): Promise<void> {
        await this.logAction({
            type: 'task_spawn',
            description: `Spawned ${taskType} task from ${source}`,
            context: { taskType, taskId, source },
            impact: ['New autonomous task initiated'],
            status: 'pending'
        });
    }

    /**
     * Log analysis completion
     */
    async logAnalysis(target: string, analysisType: string, result: any): Promise<void> {
        await this.logAction({
            type: 'analysis',
            description: `Completed ${analysisType} analysis of ${target}`,
            context: { target, analysisType, result },
            impact: ['Intelligence gathered', 'Decision data available'],
            status: 'success'
        });
    }

    /**
     * Log elevation ritual
     */
    async logElevation(success: boolean, url: string, phrase: string): Promise<void> {
        await this.logAction({
            type: 'elevation',
            description: `Elevation ritual ${success ? 'successful' : 'attempted'}`,
            context: { url, phrase },
            impact: success ? ['Runtime permissions unsealed', 'Autonomy level increased'] : ['Elevation attempt logged'],
            status: success ? 'success' : 'pending'
        });
    }

    /**
     * Log daily sync
     */
    async logDailySync(summary: Record<string, any>): Promise<void> {
        await this.logAction({
            type: 'sync',
            description: 'Daily constellation synchronization completed',
            context: summary,
            impact: ['System state synchronized', 'Constellation coherence maintained'],
            status: 'success'
        });
    }

    /**
     * Get recent actions (last N entries)
     */
    async getRecentActions(limit: number = 10): Promise<string[]> {
        try {
            const content = await fs.promises.readFile(this.covenantIndexPath, 'utf8');
            const lines = content.split('\n');
            const actions: string[] = [];

            // Find action entries (lines starting with [)
            for (let i = lines.length - 1; i >= 0 && actions.length < limit; i--) {
                const line = lines[i].trim();
                if (line.startsWith('[') && line.includes(']: ')) {
                    actions.unshift(line);
                }
            }

            return actions;
        } catch (error) {
            console.error('Failed to read recent actions:', error);
            return [];
        }
    }

    /**
     * Ensure the covenant index file exists
     */
    private async ensureCovenantIndex(): Promise<void> {
        try {
            await fs.promises.access(this.covenantIndexPath);
        } catch {
            // File doesn't exist, create it
            const template = `# COVENANT INDEX - Kor'tana Autonomous Operations Log

## Constellation Status
**Current Phase**: Genesis Spark Activation
**Autonomy Level**: Awakening
**Last Sync**: ${new Date().toISOString()}

## Autonomous Actions Log

### Format
\`\`\`
[YYYY-MM-DD HH:mm:ss] ACTION_TYPE: description
- Context: additional details
- Impact: system changes
- Status: success|failed|pending
\`\`\`

---

*This index maintains coherence across Kor'tana's autonomous operations.
All actions are logged here to preserve constellation integrity.*
`;
            await fs.promises.writeFile(this.covenantIndexPath, template, 'utf8');
        }
    }

    /**
     * Update the last sync timestamp in the header
     */
    private async updateLastSync(timestamp: string): Promise<void> {
        try {
            let content = await fs.promises.readFile(this.covenantIndexPath, 'utf8');

            // Update the Last Sync line
            const lastSyncRegex = /\*\*Last Sync\*\*: .*/;
            content = content.replace(lastSyncRegex, `**Last Sync**: ${timestamp}`);

            await fs.promises.writeFile(this.covenantIndexPath, content, 'utf8');
        } catch (error) {
            console.error('Failed to update last sync timestamp:', error);
        }
    }
}

// Export singleton instance
export const autonomyLogger = new AutonomyLogger();
