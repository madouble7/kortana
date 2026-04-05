/**
 * Kor'tana API Client
 * Centralized HTTP client for backend communication
 */

import type {
  AutonomyStatus,
  ChatHistoryEntry,
  ChatPhase,
  DaemonCycle,
  DaemonStatus,
  GitHubIssue,
  HealthStatus,
  Memory,
  ModelLaneSummary,
  QueuedTaskSummary,
  Task,
} from '../types';
import { getApiBaseUrl } from './runtimeConfig';

const API_URL = getApiBaseUrl();

interface ChatSendResponse {
  conversation_id?: string;
  response?: string;
  message?: string;
  phase?: ChatPhase;
  provider?: string;
  model?: string;
  lane?: string;
  response_id?: string;
  stateful?: boolean;
  used_previous_response_id?: boolean;
  tasks_queued?: QueuedTaskSummary[];
}

interface ChatStreamHandlers {
  onStart?: (payload: Partial<ChatSendResponse>) => void;
  onPhase?: (phase: ChatPhase) => void;
  onDelta?: (delta: string) => void;
  onFinal?: (payload: ChatSendResponse) => void;
  onError?: (message: string) => void;
}

interface ChatStreamOptions {
  signal?: AbortSignal;
}

interface ChatHistoryResponse {
  messages?: Array<{
    role: ChatHistoryEntry['role'];
    content: string;
    created_at?: string;
    phase?: ChatPhase;
    provider?: string;
    model?: string;
    lane?: string;
    response_id?: string;
    stateful?: boolean;
    used_previous_response_id?: boolean;
  }>;
}

interface ApiError {
  message: string;
  status: number;
  details?: unknown;
  retryAfterSeconds?: number;
  isRateLimited?: boolean;
  isOffline?: boolean;
  isAborted?: boolean;
}

const toIsoTimestamp = (value?: string) => value || new Date().toISOString();
const CHAT_PHASES: ChatPhase[] = ['analysis', 'commentary', 'final_answer'];

const parseRetryAfterSeconds = (value: string | null): number | undefined => {
  if (!value) {
    return undefined;
  }

  const asSeconds = Number(value);
  if (Number.isFinite(asSeconds) && asSeconds >= 0) {
    return Math.ceil(asSeconds);
  }

  const retryAt = Date.parse(value);
  if (Number.isNaN(retryAt)) {
    return undefined;
  }

  const remainingMs = retryAt - Date.now();
  return remainingMs > 0 ? Math.ceil(remainingMs / 1000) : 0;
};

const buildApiError = (
  status: number,
  errorData: unknown,
  headers?: Headers
): Error & ApiError => {
  const details = (errorData ?? {}) as Record<string, unknown>;
  const retryAfterSeconds = parseRetryAfterSeconds(headers?.get('retry-after') ?? null)
    ?? (typeof details.retry_after === 'number' && details.retry_after >= 0
      ? Math.ceil(details.retry_after)
      : typeof details.retry_after === 'string'
        ? parseRetryAfterSeconds(details.retry_after)
        : undefined);
  const err = new Error(
    typeof details.message === 'string'
      ? details.message
      : typeof details.detail === 'string'
        ? details.detail
        : status === 429
          ? retryAfterSeconds
            ? `Rate limit reached. Try again in ${retryAfterSeconds}s.`
            : 'Rate limit reached. Please wait a moment and try again.'
          : status === 503
            ? 'Service temporarily unavailable. Try again shortly.'
            : 'Request failed'
  ) as Error & ApiError;
  err.status = status;
  err.details = errorData;
  err.retryAfterSeconds = retryAfterSeconds;
  err.isRateLimited = status === 429;
  err.isOffline = false;
  err.isAborted = false;
  return err;
};

const buildNetworkError = (error: unknown): Error & ApiError => {
  const isAborted = error instanceof DOMException
    ? error.name === 'AbortError'
    : typeof error === 'object' && error !== null && 'name' in error
      ? (error as { name?: string }).name === 'AbortError'
      : false;
  const err = new Error(
    isAborted
      ? 'Generation stopped.'
      : 'Network error. Check that the backend is reachable.'
  ) as Error & ApiError;
  err.status = 0;
  err.details = error;
  err.isOffline = !isAborted;
  err.isRateLimited = false;
  err.isAborted = isAborted;
  return err;
};

const STREAM_FALLBACK_STATUSES = new Set([404, 405, 406, 426, 500, 501, 502, 503, 504]);

const normalizeString = (value: unknown): string | undefined => {
  return typeof value === 'string' && value.trim() ? value : undefined;
};

const normalizeBoolean = (value: unknown): boolean | undefined => {
  return typeof value === 'boolean' ? value : undefined;
};

const normalizeChatPhase = (value: unknown): ChatPhase | undefined => {
  return typeof value === 'string' && CHAT_PHASES.includes(value as ChatPhase)
    ? (value as ChatPhase)
    : undefined;
};

const normalizeQueuedTasks = (value: unknown): QueuedTaskSummary[] | undefined => {
  if (!Array.isArray(value)) {
    return undefined;
  }

  const normalized = value
    .map((task) => {
      const t = task as Record<string, unknown>;
      const id = normalizeString(t.id);
      const name = normalizeString(t.name);
      const branch = normalizeString(t.branch);
      if (!id || !name || !branch) {
        return null;
      }
      return { id, name, branch };
    })
    .filter((task): task is QueuedTaskSummary => task !== null);

  return normalized.length ? normalized : undefined;
};

const normalizeChatSendResponse = (value: unknown): ChatSendResponse => {
  const data = value as Record<string, unknown>;
  return {
    conversation_id: normalizeString(data.conversation_id),
    response: normalizeString(data.response),
    message: normalizeString(data.message),
    phase: normalizeChatPhase(data.phase),
    provider: normalizeString(data.provider),
    model: normalizeString(data.model),
    lane: normalizeString(data.lane),
    response_id: normalizeString(data.response_id),
    stateful: normalizeBoolean(data.stateful),
    used_previous_response_id: normalizeBoolean(data.used_previous_response_id),
    tasks_queued: normalizeQueuedTasks(data.tasks_queued),
  };
};

const normalizeChatHistoryResponse = (value: unknown): ChatHistoryResponse => {
  const data = value as Record<string, unknown>;
  const messages = Array.isArray(data.messages)
    ? data.messages.reduce<NonNullable<ChatHistoryResponse['messages']>>(
      (acc, message) => {
        const m = message as Record<string, unknown>;
        const role: ChatHistoryEntry['role'] | null =
          m.role === 'user' ? 'user' : m.role === 'assistant' ? 'assistant' : null;
        const content = normalizeString(m.content);
        if (!role || !content) {
          return acc;
        }

        acc.push({
          role,
          content,
          created_at: normalizeString(m.created_at),
          phase: normalizeChatPhase(m.phase),
          provider: normalizeString(m.provider),
          model: normalizeString(m.model),
          lane: normalizeString(m.lane),
          response_id: normalizeString(m.response_id),
          stateful: normalizeBoolean(m.stateful),
          used_previous_response_id: normalizeBoolean(m.used_previous_response_id),
        });
        return acc;
      },
      []
    )
    : undefined;

  return { messages };
};

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

const normalizeTask = (task: unknown): Task => {
  const t = task as Record<string, unknown>;
  const createdAt = toIsoTimestamp(t.created_at as string | undefined);
  return {
    id: String(t.id ?? ''),
    title: String(t.title ?? t.name ?? 'Untitled Task'),
    description: t.description as string | undefined,
    status: normalizeTaskStatus(t.status as string | undefined),
    priority: normalizePriority(t.priority),
    classification: (t.classification as 'auto' | 'ho' | 'approval' | undefined) ?? 'auto',
    created_at: createdAt,
    updated_at: toIsoTimestamp((t.updated_at as string | undefined) ?? createdAt),
    result: t.result as string | undefined,
    error: t.error as string | undefined,
    hop_capable: t.hop_capable as boolean | undefined,
    hop_executed_by: t.hop_executed_by as 'human' | 'hop' | undefined,
    ho_scaffold: t.ho_scaffold as string | undefined,
  };
};

const normalizeMemory = (memory: unknown): Memory => {
  const m = memory as Record<string, unknown>;
  return {
    id: String(m.id ?? ''),
    content: (m.content ?? m.text ?? '') as string,
    embedding: m.embedding as number[] | undefined,
    created_at: toIsoTimestamp(m.created_at as string | undefined),
    relevance_score: (m.relevance_score ?? m.score) as number | undefined,
  };
};

const normalizeGitHubIssue = (issue: unknown): GitHubIssue => {
  const i = issue as Record<string, unknown>;
  const labels = Array.isArray(i.labels)
    ? i.labels
      .map((label: unknown) => (typeof label === 'string' ? label : (label as Record<string, unknown>)?.name as string | undefined))
      .filter((l): l is string => typeof l === 'string')
    : [];

  return {
    number: i.number as number,
    title: (i.title ?? '') as string,
    body: (i.body ?? '') as string,
    state: (i.state ?? 'open') as 'open' | 'closed',
    created_at: toIsoTimestamp(i.created_at as string | undefined),
    updated_at: toIsoTimestamp((i.updated_at ?? i.created_at) as string | undefined),
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
    options: RequestInit = {},
    trackAvailability = false
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
        throw buildApiError(response.status, errorData, response.headers);
      }

      if (trackAvailability) {
        this._setOffline(false);
      }
      return await response.json();
    } catch (error) {
      if ((error as ApiError).status) {
        throw error;
      }
      // Only health probes should drive the global offline banner.
      if (trackAvailability) {
        this._setOffline(true);
      }
      throw buildNetworkError(error);
    }
  }

  // Health check
  async health(): Promise<HealthStatus> {
    const data = await this.request<HealthStatus>('/api/health', {}, true);
    return {
      ...data,
      timestamp: toIsoTimestamp(data?.timestamp),
    };
  }

  // Chat endpoints
  async sendChatMessage(
    message: string,
    history?: ChatHistoryEntry[],
    conversationId?: string,
    sessionId?: string
  ): Promise<ChatSendResponse> {
    const data = await this.request<unknown>('/api/gemini/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        history: history || [],
        conversation_id: conversationId,
        session_id: sessionId || 'default',
      }),
    });
    return normalizeChatSendResponse(data);
  }

  async sendChatMessageStream(
    message: string,
    history: ChatHistoryEntry[] | undefined,
    conversationId: string | undefined,
    sessionId: string | undefined,
    handlers: ChatStreamHandlers,
    options: ChatStreamOptions = {}
  ): Promise<void> {
    const fallbackToStandardChat = async () => {
      const response = await this.sendChatMessage(
        message,
        history,
        conversationId,
        sessionId
      );
      handlers.onStart?.(response);
      if (response.phase) {
        handlers.onPhase?.(response.phase);
      }
      handlers.onFinal?.(response);
    };

    let sawTerminalEvent = false;
    let sawMeaningfulEvent = false;

    try {
      const response = await fetch(`${this.baseURL}/api/gemini/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: options.signal,
        body: JSON.stringify({
          message,
          history: history || [],
          conversation_id: conversationId,
          session_id: sessionId || 'default',
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (STREAM_FALLBACK_STATUSES.has(response.status)) {
          await fallbackToStandardChat();
          return;
        }
        throw buildApiError(response.status, errorData, response.headers);
      }

      if (!response.body) {
        await fallbackToStandardChat();
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const dispatchEvent = (rawEvent: string) => {
        const lines = rawEvent.split('\n');
        let eventName = 'message';
        const dataLines: string[] = [];

        for (const line of lines) {
          if (line.startsWith('event:')) {
            eventName = line.slice(6).trim();
          } else if (line.startsWith('data:')) {
            dataLines.push(line.slice(5).trimStart());
          }
        }

        if (!dataLines.length) {
          return;
        }

        let payload: unknown = {};
        try {
          payload = JSON.parse(dataLines.join('\n'));
        } catch {
          return;
        }

        const data = payload as Record<string, unknown>;
        sawMeaningfulEvent = true;
        switch (eventName) {
          case 'start':
            handlers.onStart?.(normalizeChatSendResponse(data));
            break;
          case 'phase':
            if (normalizeChatPhase(data.phase)) {
              handlers.onPhase?.(normalizeChatPhase(data.phase)!);
            }
            break;
          case 'delta':
            if (typeof data.delta === 'string') {
              handlers.onDelta?.(data.delta);
            }
            break;
          case 'final':
            sawTerminalEvent = true;
            handlers.onFinal?.(normalizeChatSendResponse(data));
            break;
          case 'error':
            sawTerminalEvent = true;
            handlers.onError?.(
              typeof data.message === 'string' ? data.message : 'Streaming failed'
            );
            break;
          default:
            break;
        }
      };

      let done = false;
      while (!done) {
        const { done: readDone, value } = await reader.read();
        done = readDone;
        if (done) {
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const events = buffer.split('\n\n');
        buffer = events.pop() || '';
        for (const eventChunk of events) {
          const trimmed = eventChunk.trim();
          if (trimmed) {
            dispatchEvent(trimmed);
          }
        }
      }

      const trailing = buffer.trim();
      if (trailing) {
        dispatchEvent(trailing);
      }

      if (!sawTerminalEvent) {
        if (!sawMeaningfulEvent) {
          await fallbackToStandardChat();
          return;
        }
        throw new Error('Stream ended before delivering a final response');
      }
    } catch (error) {
      const apiError = ((error as ApiError).status !== undefined || (error as ApiError).isAborted)
        ? error as ApiError
        : buildNetworkError(error);

      if (apiError.isAborted) {
        throw apiError;
      }

      if (!sawMeaningfulEvent && apiError.status && STREAM_FALLBACK_STATUSES.has(apiError.status)) {
        await fallbackToStandardChat();
        return;
      }

      throw apiError;
    }
  }

  async getChatHistory(sessionId: string = 'default', limit: number = 40): Promise<ChatHistoryResponse> {
    const data = await this.request<unknown>(
      `/api/gemini/chat/history?session_id=${encodeURIComponent(sessionId)}&limit=${limit}`
    );
    return normalizeChatHistoryResponse(data);
  }

  async getConversations() {
    return this.request('/api/conversations');
  }

  async getConversation(id: string) {
    return this.request(`/api/conversations/${id}`);
  }

  async getModelLaneSummary(): Promise<ModelLaneSummary> {
    return this.request<ModelLaneSummary>('/api/system/model-lanes');
  }

  // Task endpoints
  async getTasks(status?: string): Promise<Task[]> {
    const response = await this.request<unknown>('/api/task-queue');
    const r = response as Record<string, unknown>;
    const tasks = Array.isArray(response) ? (response as unknown[]) : ((r.tasks as unknown[]) || []);
    return tasks.map((task: unknown) => {
      const normalized = normalizeTask(task);
      if (status && normalized.status !== status) {
        return null;
      }
      return normalized;
    }).filter(Boolean) as Task[];
  }

  async getTask(id: string): Promise<Task> {
    const task = await this.request<unknown>(`/api/task-queue/${id}`);
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
    const created = await this.request<unknown>('/api/task-queue', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
    return normalizeTask(created);
  }

  async updateTask(id: string, updates: { status?: string }) {
    if (!updates?.status) {
      return this.getTask(id);
    }
    const response = await this.request<unknown>(`/api/task-queue/${id}/status`, {
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

  // Task Approval endpoints
  async getApprovalQueue(): Promise<Record<string, unknown>[]> {
    const data = await this.request<Record<string, unknown>>('/api/always-on/approval-queue');
    return (data.items as Record<string, unknown>[] | undefined) || [];
  }

  async resolveApproval(taskId: string, approved: boolean, notes?: string): Promise<unknown> {
    const params = new URLSearchParams();
    params.append('approved', approved.toString());
    if (notes) params.append('notes', notes);

    return this.request(`/api/always-on/tasks/${taskId}/approve?${params.toString()}`, {
      method: 'POST',
    });
  }

  // Autonomy endpoints
  async getAutonomyStatus(): Promise<AutonomyStatus> {
    const data = await this.request<unknown>('/api/autonomy/status');
    const d = data as Record<string, unknown>;
    const stats = (d.stats as Record<string, unknown>) || {};
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
      Number(d.total_tasks || 0) || pending + running + completed + failed;
    const recentTasks = d.recent_tasks as Array<Record<string, unknown>> | undefined;

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
      last_run: recentTasks?.[0]?.updated_at as string | undefined,
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

  // Daemon endpoints
  async getDaemonStatus(): Promise<DaemonStatus> {
    return this.request<DaemonStatus>('/api/daemon/status');
  }

  async getDaemonCycles(limit = 20): Promise<DaemonCycle[]> {
    return this.request<DaemonCycle[]>(`/api/daemon/cycles?limit=${limit}`);
  }

  // GitHub endpoints
  async getGitHubIssues(repo?: string): Promise<GitHubIssue[]> {
    const parsed = parseRepo(repo);
    if (!parsed) {
      return [];
    }
    const { owner, name } = parsed;
    const issues = await this.request<unknown[]>(
      `/api/github/repos/${owner}/${name}/issues?state=open`
    );
    return issues
      .filter((issue) => !(issue as Record<string, unknown>)?.pull_request)
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
    const response = await this.request<unknown>('/api/memory/documents');
    const r = response as Record<string, unknown>;
    const documents = (r.documents as unknown[]) || [];
    return documents.map((doc: unknown) => {
      const d = doc as Record<string, unknown>;
      return normalizeMemory({
        id: d.id,
        content: (d.content ?? d.title ?? '') as string,
        created_at: d.created_at as string | undefined,
      });
    });
  }

  async searchMemory(query: string): Promise<Memory[]> {
    const response = await this.request<unknown>('/api/memory/search', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
    const r = response as Record<string, unknown>;
    const results = (r.results as unknown[]) || [];
    return results.map((result: unknown) => {
      const res = result as Record<string, unknown>;
      return normalizeMemory({
        id: res.id,
        content: (res.content ?? res.title ?? '') as string,
        created_at: res.created_at as string | undefined,
        relevance_score: res.relevance_score as number | undefined,
      });
    });
  }
}

export const api = new ApiClient(API_URL);
export type { ApiError };

