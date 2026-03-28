/**
 * Kor'tana API Client
 * Centralized HTTP client for backend communication
 */

import type { AutonomyStatus, GitHubIssue, HealthStatus, Memory, Task } from '../types';

// Helper to determine the API base URL
const getBaseUrl = () => {
  // 1. Check for runtime configuration injected by the backend
  const runtimeConfig = (window as any).__KORTANA__;
  if (runtimeConfig && runtimeConfig.VITE_API_URL !== undefined) {
    return runtimeConfig.VITE_API_URL;
  }

  // 2. Check for build-time environment variable
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }

  // 3. Smart fallback: If we're on the Vite dev port (5173), target the backend on 8000
  // using the current browser hostname so LAN/mobile dev access works too.
  // Otherwise, use relative paths (unified mode)
  if (typeof window !== 'undefined' && window.location.port === '5173') {
    return `http://${window.location.hostname}:8000`;
  }

  return ''; // Relative paths
};

const API_URL = getBaseUrl();

interface ApiError {
  message: string;
  status: number;
  details?: any;
}

const toIsoTimestamp = (value?: string) => value || new Date().toISOString();

const normalizeTaskStatus = (status?: string): Task['status'] => {
  switch (status) {
    case 'in_progress':
    case 'executing':
    case 'running':
      return 'running';
    case 'completed':
      return 'completed';
    case 'failed':
      return 'failed';
    case 'waiting_for_ho':
      return 'waiting_for_ho';
    case 'pending':
    default:
      return 'pending';
  }
};

const normalizePriority = (priority: unknown): Task['priority'] => {
  if (priority === 'low' || priority === 'medium' || priority === 'high') {
    return priority;
  }
  if (typeof priority === 'number') {
    if (priority <= 3) return 'low';
    if (priority >= 7) return 'high';
  }
  return 'medium';
};

const priorityToNumber = (priority?: Task['priority']): number => {
  switch (priority) {
    case 'low':
      return 3;
    case 'high':
      return 8;
    case 'medium':
    default:
      return 5;
  }
};

const normalizeTask = (task: any): Task => {
  const createdAt = toIsoTimestamp(task?.created_at);
  return {
    id: String(task?.id ?? ''),
    title: task?.title ?? task?.name ?? 'Untitled Task',
    description: task?.description ?? undefined,
    status: normalizeTaskStatus(task?.status),
    priority: normalizePriority(task?.priority),
    classification: task?.classification ?? 'auto',
    created_at: createdAt,
    updated_at: toIsoTimestamp(task?.updated_at ?? createdAt),
    result: task?.result ?? undefined,
    error: task?.error ?? undefined,
    hop_capable: task?.hop_capable ?? undefined,
    hop_executed_by: task?.hop_executed_by ?? undefined,
    ho_scaffold: task?.ho_scaffold ?? undefined,
  };
};

const normalizeMemory = (memory: any): Memory => ({
  id: String(memory?.id ?? ''),
  content: memory?.content ?? memory?.text ?? '',
  embedding: memory?.embedding ?? undefined,
  created_at: toIsoTimestamp(memory?.created_at),
  relevance_score: memory?.relevance_score ?? memory?.score ?? undefined,
});

const normalizeGitHubIssue = (issue: any): GitHubIssue => {
  const labels = Array.isArray(issue?.labels)
    ? issue.labels
      .map((label: any) => (typeof label === 'string' ? label : label?.name))
      .filter(Boolean)
    : [];

  return {
    number: issue?.number,
    title: issue?.title ?? '',
    body: issue?.body ?? '',
    state: issue?.state ?? 'open',
    created_at: toIsoTimestamp(issue?.created_at),
    updated_at: toIsoTimestamp(issue?.updated_at ?? issue?.created_at),
    labels,
  };
};

const parseRepo = (repo?: string): { owner: string; name: string } | null => {
  if (!repo) return null;
  const trimmed = repo.trim();
  if (!trimmed) return null;
  const [owner, name] = trimmed.split('/');
  if (!owner || !name) {
    throw new Error('Invalid repo format. Use owner/repo.');
  }
  return { owner, name };
};

class ApiClient {
  private baseURL: string;
  /** True when the backend is unreachable (no VITE_API_URL set and relative calls 404). */
  offline = false;
  private _offlineListeners: Array<(v: boolean) => void> = [];

  constructor(baseURL: string) {
    this.baseURL = baseURL;
  }

  onOfflineChange(cb: (offline: boolean) => void) {
    this._offlineListeners.push(cb);
    return () => {
      this._offlineListeners = this._offlineListeners.filter((l) => l !== cb);
    };
  }

  private _setOffline(v: boolean) {
    if (this.offline !== v) {
      this.offline = v;
      this._offlineListeners.forEach((cb) => cb(v));
    }
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw {
          message: errorData.message || errorData.detail || 'Request failed',
          status: response.status,
          details: errorData,
        } as ApiError;
      }

      this._setOffline(false);
      return await response.json();
    } catch (error) {
      if ((error as ApiError).status) {
        throw error;
      }
      // Network error → mark as offline
      this._setOffline(true);
      throw {
        message: 'Network error',
        status: 0,
        details: error,
      } as ApiError;
    }
  }

  // Health check
  async health(): Promise<HealthStatus> {
    const data = await this.request<HealthStatus>('/api/health');
    return {
      ...data,
      timestamp: toIsoTimestamp(data?.timestamp),
    };
  }

  // Chat endpoints
  async sendChatMessage(message: string, conversationId?: string): Promise<any> {
    return this.request<any>('/api/gemini/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id: conversationId }),
    });
  }

  async getConversations() {
    return this.request('/api/conversations');
  }

  async getConversation(id: string) {
    return this.request(`/api/conversations/${id}`);
  }

  // Task endpoints
  async getTasks(status?: string): Promise<Task[]> {
    const response = await this.request<any>('/api/task-queue');
    const tasks = Array.isArray(response) ? response : response?.tasks || [];
    return tasks.map((task: any) => {
      const normalized = normalizeTask(task);
      if (status && normalized.status !== status) {
        return null;
      }
      return normalized;
    }).filter(Boolean) as Task[];
  }

  async getTask(id: string): Promise<Task> {
    const task = await this.request<any>(`/api/task-queue/${id}`);
    return normalizeTask(task);
  }

  async createTask(task: {
    title: string;
    description?: string;
    priority?: Task['priority'];
  }) {
    const payload = {
      name: task.title,
      description: task.description,
      priority: priorityToNumber(task.priority),
    };
    const created = await this.request<any>('/api/task-queue', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return normalizeTask(created);
  }

  async updateTask(id: string, updates: { status?: string }) {
    if (!updates?.status) {
      return this.getTask(id);
    }
    const response = await this.request<any>(`/api/task-queue/${id}/status`, {
      method: 'POST',
      body: JSON.stringify({ status: updates.status }),
    });
    return response;
  }

  async deleteTask(id: string) {
    return this.request(`/api/task-queue/${id}`, {
      method: 'DELETE',
    });
  }

  async executeTask(id: string) {
    return this.request(`/api/task-queue/execute/${id}`, {
      method: 'POST',
    });
  }

  // Autonomy endpoints
  async getAutonomyStatus(): Promise<AutonomyStatus> {
    const data = await this.request<any>('/api/autonomy/status');
    const stats = data?.stats || {};
    const pending = Number(stats.pending || 0);
    const running =
      Number(stats.running || 0) +
      Number(stats.analyzing || 0) +
      Number(stats.planning || 0) +
      Number(stats.ready_to_execute || 0) +
      Number(stats.executing || 0);
    const completed = Number(stats.completed || 0);
    const failed = Number(stats.failed || 0);
    const total =
      Number(data?.total_tasks || 0) || pending + running + completed + failed;

    return {
      status: total > 0 ? 'active' : 'inactive',
      timestamp: toIsoTimestamp(),
      statistics: {
        total_tasks: total,
        by_status: {
          pending,
          running,
          completed,
          failed,
          waiting_for_ho: 0,
        },
        by_classification: {
          auto: total,
          ho: 0,
          approval: 0,
        },
      },
      last_run: data?.recent_tasks?.[0]?.updated_at,
      tasks_executed: completed,
    };
  }

  async triggerAutonomyCycle() {
    return this.request('/api/autonomy/task-queue', {
      method: 'POST',
    });
  }

  async getAutonomyLogs() {
    return this.request('/api/autonomy/actions');
  }

  // GitHub endpoints
  async getGitHubIssues(repo?: string): Promise<GitHubIssue[]> {
    const parsed = parseRepo(repo);
    if (!parsed) {
      return [];
    }
    const { owner, name } = parsed;
    const issues = await this.request<any[]>(
      `/api/github/repos/${owner}/${name}/issues?state=open`
    );
    return issues
      .filter((issue) => !issue?.pull_request)
      .map((issue) => normalizeGitHubIssue(issue));
  }

  async createTaskFromIssue(issue: GitHubIssue, repo: string) {
    const payload = {
      name: `#${issue.number} ${issue.title}`,
      description: issue.body || `GitHub issue ${repo}#${issue.number}`,
      priority: 5,
    };
    return this.request('/api/task-queue', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  // Memory endpoints
  async getMemories(): Promise<Memory[]> {
    const response = await this.request<any>('/api/memory/documents');
    const documents = response?.documents || [];
    return documents.map((doc: any) =>
      normalizeMemory({
        id: doc.id,
        content: doc.content ?? doc.title ?? '',
        created_at: doc.created_at,
      })
    );
  }

  async searchMemory(query: string): Promise<Memory[]> {
    const response = await this.request<any>('/api/memory/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    const results = response?.results || [];
    return results.map((result: any) =>
      normalizeMemory({
        id: result.id,
        content: result.content ?? result.title ?? '',
        created_at: result.created_at,
        relevance_score: result.relevance_score,
      })
    );
  }
}

export const api = new ApiClient(API_URL);
export type { ApiError };

