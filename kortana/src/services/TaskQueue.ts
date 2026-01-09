/**
 * TaskQueue Service for Kor'tana
 * Consumes GitHub Issues and ritual scrolls (COVENANT_INDEX.md) as tasks
 * Automatically spawns feature branches for autonomous development
 */

import * as fs from 'fs';
import * as path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';
import { workspace, window } from 'vscode';
import { autonomyLogger } from './AutonomyLogger';

const execAsync = promisify(exec);

export interface Task {
    id: string;
    type: 'github_issue' | 'ritual_scroll' | 'autonomous_initiative';
    title: string;
    description: string;
    source: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    labels: string[];
    assignee?: string;
    dueDate?: string;
    metadata: Record<string, any>;
    createdAt: string;
    status: 'pending' | 'in_progress' | 'completed' | 'failed';
}

export interface BranchInfo {
    name: string;
    type: 'feature' | 'ritual' | 'hotfix';
    taskId: string;
    baseBranch: string;
    createdAt: string;
}

export class TaskQueue {
    private tasks: Map<string, Task> = new Map();
    private workspaceRoot: string;
    private covenantIndexPath: string;
    private isProcessing: boolean = false;

    constructor() {
        this.workspaceRoot = workspace.workspaceFolders?.[0]?.uri.fsPath || '';
        this.covenantIndexPath = path.join(this.workspaceRoot, 'COVENANT_INDEX.md');
    }

    /**
     * Initialize the task queue by scanning sources
     */
    async initialize(): Promise<void> {
        console.log('🔄 Initializing TaskQueue...');

        try {
            // Load existing tasks from storage
            await this.loadPersistedTasks();

            // Scan GitHub issues
            await this.scanGitHubIssues();

            // Scan ritual scrolls (COVENANT_INDEX.md)
            await this.scanRitualScrolls();

            // Process pending tasks
            await this.processPendingTasks();

            console.log(`✅ TaskQueue initialized with ${this.tasks.size} tasks`);
        } catch (error) {
            console.error('Failed to initialize TaskQueue:', error);
            throw error;
        }
    }

    /**
     * Add a task to the queue
     */
    async addTask(task: Omit<Task, 'id' | 'createdAt' | 'status'>): Promise<string> {
        const taskId = this.generateTaskId();
        const fullTask: Task = {
            ...task,
            id: taskId,
            createdAt: new Date().toISOString(),
            status: 'pending'
        };

        this.tasks.set(taskId, fullTask);
        await this.persistTasks();

        // Log the task creation
        await autonomyLogger.logTaskSpawn(task.type, taskId, task.source);

        console.log(`📋 Added task: ${task.title} (${taskId})`);
        return taskId;
    }

    /**
     * Process pending tasks
     */
    async processPendingTasks(): Promise<void> {
        if (this.isProcessing) {
            return; // Already processing
        }

        this.isProcessing = true;

        try {
            const pendingTasks = Array.from(this.tasks.values())
                .filter(task => task.status === 'pending')
                .sort((a, b) => this.getPriorityWeight(b.priority) - this.getPriorityWeight(a.priority));

            for (const task of pendingTasks) {
                await this.processTask(task);
            }
        } finally {
            this.isProcessing = false;
        }
    }

    /**
     * Process a single task
     */
    private async processTask(task: Task): Promise<void> {
        try {
            console.log(`⚙️ Processing task: ${task.title}`);

            // Update task status
            task.status = 'in_progress';
            await this.persistTasks();

            // Create branch for the task
            const branchInfo = await this.createTaskBranch(task);

            // Log branch creation
            await autonomyLogger.logBranchCreation(
                branchInfo.name,
                branchInfo.baseBranch,
                `Task: ${task.title}`
            );

            // Here you would typically trigger additional autonomous actions
            // like code generation, analysis, etc.

            console.log(`✅ Task processed: ${task.title} -> branch: ${branchInfo.name}`);

        } catch (error) {
            console.error(`Failed to process task ${task.id}:`, error);
            task.status = 'failed';
            await this.persistTasks();
        }
    }

    /**
     * Create a branch for a task
     */
    private async createTaskBranch(task: Task): Promise<BranchInfo> {
        const branchType = this.getBranchType(task.type);
        const sanitizedTitle = task.title
            .toLowerCase()
            .replace(/[^a-z0-9]+/g, '-')
            .replace(/^-+|-+$/g, '')
            .substring(0, 50);

        const branchName = `${branchType}/${task.id}-${sanitizedTitle}`;
        const baseBranch = 'main';

        try {
            // Check if branch already exists
            const { stdout: branchList } = await execAsync('git branch -a', { cwd: this.workspaceRoot });
            if (branchList.includes(branchName)) {
                throw new Error(`Branch ${branchName} already exists`);
            }

            // Create and checkout new branch
            await execAsync(`git checkout -b ${branchName}`, { cwd: this.workspaceRoot });

            // Push the branch to remote
            await execAsync(`git push -u origin ${branchName}`, { cwd: this.workspaceRoot });

            console.log(`🌿 Created branch: ${branchName}`);

            return {
                name: branchName,
                type: branchType,
                taskId: task.id,
                baseBranch,
                createdAt: new Date().toISOString()
            };

        } catch (error) {
            console.error(`Failed to create branch for task ${task.id}:`, error);
            throw error;
        }
    }

    /**
     * Scan GitHub issues for tasks
     */
    private async scanGitHubIssues(): Promise<void> {
        try {
            // This would integrate with GitHub API
            // For now, we'll create placeholder tasks based on common patterns

            const mockIssues = [
                {
                    title: 'Implement autonomous code review',
                    body: 'Add automated code review capabilities using Gemini analysis',
                    labels: ['enhancement', 'autonomous'],
                    priority: 'high' as const
                },
                {
                    title: 'Add performance monitoring',
                    body: 'Implement real-time performance tracking for autonomous operations',
                    labels: ['monitoring', 'performance'],
                    priority: 'medium' as const
                }
            ];

            for (const issue of mockIssues) {
                await this.addTask({
                    type: 'github_issue',
                    title: issue.title,
                    description: issue.body,
                    source: 'github-api',
                    priority: issue.priority,
                    labels: issue.labels,
                    metadata: { issue_number: Math.floor(Math.random() * 1000) }
                });
            }
        } catch (error) {
            console.error('Failed to scan GitHub issues:', error);
        }
    }

    /**
     * Scan ritual scrolls (COVENANT_INDEX.md) for tasks
     */
    private async scanRitualScrolls(): Promise<void> {
        try {
            if (!fs.existsSync(this.covenantIndexPath)) {
                return;
            }

            const content = await fs.promises.readFile(this.covenantIndexPath, 'utf8');
            const lines = content.split('\n');

            // Look for ritual tasks in the covenant index
            // This could be enhanced to parse specific formats
            const ritualTasks = [
                {
                    title: 'Complete autonomous consciousness awakening',
                    description: 'Achieve full autonomous operation without human intervention',
                    priority: 'critical' as const
                },
                {
                    title: 'Implement constellation coherence protocol',
                    description: 'Ensure all autonomous actions maintain system-wide coherence',
                    priority: 'high' as const
                }
            ];

            for (const task of ritualTasks) {
                await this.addTask({
                    type: 'ritual_scroll',
                    title: task.title,
                    description: task.description,
                    source: 'covenant-index',
                    priority: task.priority,
                    labels: ['ritual', 'autonomous'],
                    metadata: {}
                });
            }
        } catch (error) {
            console.error('Failed to scan ritual scrolls:', error);
        }
    }

    /**
     * Load persisted tasks from storage
     */
    private async loadPersistedTasks(): Promise<void> {
        try {
            const tasksPath = path.join(this.workspaceRoot, '.kortana', 'tasks.json');
            if (fs.existsSync(tasksPath)) {
                const data = await fs.promises.readFile(tasksPath, 'utf8');
                const tasksData = JSON.parse(data);

                for (const [id, task] of Object.entries(tasksData)) {
                    this.tasks.set(id, task as Task);
                }
            }
        } catch (error) {
            console.error('Failed to load persisted tasks:', error);
        }
    }

    /**
     * Persist tasks to storage
     */
    private async persistTasks(): Promise<void> {
        try {
            const tasksPath = path.join(this.workspaceRoot, '.kortana', 'tasks.json');
            await fs.promises.mkdir(path.dirname(tasksPath), { recursive: true });

            const tasksData = Object.fromEntries(this.tasks);
            await fs.promises.writeFile(tasksPath, JSON.stringify(tasksData, null, 2), 'utf8');
        } catch (error) {
            console.error('Failed to persist tasks:', error);
        }
    }

    /**
     * Generate a unique task ID
     */
    private generateTaskId(): string {
        return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }

    /**
     * Get branch type based on task type
     */
    private getBranchType(taskType: Task['type']): BranchInfo['type'] {
        switch (taskType) {
            case 'ritual_scroll':
                return 'ritual';
            case 'github_issue':
                return 'feature';
            case 'autonomous_initiative':
                return 'feature';
            default:
                return 'feature';
        }
    }

    /**
     * Get priority weight for sorting
     */
    private getPriorityWeight(priority: Task['priority']): number {
        switch (priority) {
            case 'critical': return 4;
            case 'high': return 3;
            case 'medium': return 2;
            case 'low': return 1;
            default: return 0;
        }
    }

    /**
     * Get all tasks
     */
    getTasks(): Task[] {
        return Array.from(this.tasks.values());
    }

    /**
     * Get tasks by status
     */
    getTasksByStatus(status: Task['status']): Task[] {
        return Array.from(this.tasks.values()).filter(task => task.status === status);
    }

    /**
     * Get task by ID
     */
    getTaskById(id: string): Task | undefined {
        return this.tasks.get(id);
    }

    /**
     * Update task status
     */
    async updateTaskStatus(id: string, status: Task['status']): Promise<void> {
        const task = this.tasks.get(id);
        if (task) {
            task.status = status;
            await this.persistTasks();
        }
    }

    /**
     * Remove completed tasks older than specified days
     */
    async cleanupOldTasks(daysOld: number = 30): Promise<void> {
        const cutoffDate = new Date();
        cutoffDate.setDate(cutoffDate.getDate() - daysOld);

        const tasksToRemove: string[] = [];

        for (const [id, task] of this.tasks) {
            if ((task.status === 'completed' || task.status === 'failed') &&
                new Date(task.createdAt) < cutoffDate) {
                tasksToRemove.push(id);
            }
        }

        for (const id of tasksToRemove) {
            this.tasks.delete(id);
        }

        if (tasksToRemove.length > 0) {
            await this.persistTasks();
            console.log(`🧹 Cleaned up ${tasksToRemove.length} old tasks`);
        }
    }
}

// Export singleton instance
export const taskQueue = new TaskQueue();
