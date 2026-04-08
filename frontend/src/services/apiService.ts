import { getApiBaseUrl } from '../lib/runtimeConfig';

const API_BASE_URL = getApiBaseUrl();

export interface HealthResponse {
  status: string;
  message: string;
  environment?: string;
  version?: string;
}

export interface SystemMetrics {
  cpu_percent: number;
  memory_percent: number;
  disk_percent: number;
  requests_total: number;
  errors_total: number;
  uptime_seconds: number;
}

export interface AgentInfo {
  id: number;
  name: string;
  description: string;
  status: 'active' | 'idle' | 'training' | 'error';
  model: string;
  created_at: string;
  last_active: string;
}

export interface TaskInfo {
  id: number;
  name: string;
  description: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  priority: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  result?: unknown;
}

export interface PrayerStatusResponse {
  status: string;
  message: string;
  timestamp: string;
  persons: string[];
  next_cycle: string;
}

export interface GitHubIssue {
  id: number;
  number: number;
  title: string;
  body: string;
  state: string;
  html_url: string;
  created_at: string;
}

export interface MemoryEntry {
  id: string;
  title: string;
  content: string;
  timestamp: string;
  tags: string[];
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed for ${endpoint}:`, error);
      throw error;
    }
  }

  // Health & Status
  async getHealth(): Promise<HealthResponse> {
    return this.request<HealthResponse>('/api/health');
  }

  // Prayer Agent
  async getPrayerStatus(): Promise<PrayerStatusResponse> {
    return this.request<PrayerStatusResponse>('/api/prayer/status');
  }

  async requestPrayer(person: string = 'both', request: string = ''): Promise<unknown> {
    const params = new URLSearchParams({ person, request });
    return this.request(`/api/prayer/request?${params}`);
  }

  // GitHub Integration
  async getGitHubIssues(owner: string, repo: string, state: string = 'open'): Promise<GitHubIssue[]> {
    return this.request<GitHubIssue[]>(`/api/github/repos/${owner}/${repo}/issues?state=${state}`);
  }

  async getGitHubPullRequests(owner: string, repo: string, state: string = 'open'): Promise<unknown[]> {
    return this.request(`/api/github/repos/${owner}/${repo}/pulls?state=${state}`);
  }

  async analyzeGitHubContent(content: string, type: string = 'issue'): Promise<unknown> {
    return this.request('/api/github/analyze', {
      method: 'POST',
      body: JSON.stringify({ content, type }),
    });
  }

  // Memory System
  async getMemories(): Promise<MemoryEntry[]> {
    const response = await this.request<{ documents: MemoryEntry[] }>('/api/memory/documents');
    return response.documents;
  }

  async searchMemories(query: string, tags?: string[]): Promise<unknown> {
    const params = new URLSearchParams({ query });
    if (tags && tags.length > 0) {
      params.append('tags', tags.join(','));
    }
    return this.request(`/api/memory/search?${params}`);
  }

  async addMemory(title: string, content: string): Promise<unknown> {
    return this.request('/api/memory/add_document', {
      method: 'POST',
      body: JSON.stringify({ title, content }),
    });
  }

  // System & Management
  async getSystemInfo(): Promise<unknown> { return this.request('/api/system/info'); }
  async getLogs(lines: number = 100): Promise<unknown> { return this.request(`/api/system/logs?lines=${lines}`); }
  async getSettings(): Promise<unknown> { return this.request('/api/system/settings'); }

  // Rclone Cloud Storage
  async getRcloneRemotes(): Promise<unknown> { return this.request('/api/rclone/list'); }
  async getRcloneFiles(remote: string, path: string = ""): Promise<unknown> { return this.request(`/api/rclone/files/${remote}?path=${path}`); }

  // Human Only Protocol (HOP)
  async getProtocolStatus(): Promise<unknown> { return this.request('/api/protocol/status'); }
  async runAutonomousCycle(): Promise<unknown> { return this.request('/api/protocol/auto/cycle', { method: 'POST' }); }
  async getNextHoTask(): Promise<unknown> { return this.request('/api/protocol/ho/next'); }
  async completeHoTask(taskId: string): Promise<unknown> { return this.request(`/api/protocol/ho/complete/${taskId}`, { method: 'POST' }); }

  // Agent Operations
  async listAgents(): Promise<AgentInfo[]> {
    const response = await this.request<{ agents: AgentInfo[] }>('/api/agents/list');
    return response.agents;
  }

  async createAgent(name: string, description: string, capabilities: string[]): Promise<unknown> {
    return this.request('/api/agents/create', {
      method: 'POST',
      body: JSON.stringify({ name, description, capabilities }),
    });
  }

  async executeAgent(agentId: number, task: string): Promise<unknown> {
    return this.request(`/api/agents/execute/${agentId}`, {
      method: 'POST',
      body: JSON.stringify({ task }),
    });
  }

  // Task Operations
  async getTasks(): Promise<TaskInfo[]> {
    const response = await this.request<{ tasks: TaskInfo[] }>('/api/task-queue');
    return response.tasks || [];
  }

  async createTask(name: string, description: string, priority: number = 5): Promise<unknown> {
    return this.request('/api/task-queue', {
      method: 'POST',
      body: JSON.stringify({ name, description, priority }),
    });
  }

  async cancelTask(taskId: number): Promise<unknown> {
    return this.request(`/api/task-queue/${taskId}`, {
      method: 'DELETE',
    });
  }

  // Metrics
  async getMetrics(): Promise<SystemMetrics> {
    return this.request<SystemMetrics>('/api/system/health/metrics');
  }

  async getDetailedHealth(): Promise<unknown> {
    return this.request('/api/system/health/detailed');
  }
}

export const apiService = new ApiService();
