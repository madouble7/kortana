/**
 * TypeScript type definitions for Kor'tana
 */

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'waiting_for_ho';
  priority: 'low' | 'medium' | 'high';
  classification?: 'auto' | 'ho' | 'approval';
  created_at: string;
  updated_at: string;
  result?: string;
  error?: string;
  hop_capable?: boolean;
  hop_executed_by?: 'human' | 'hop';
  ho_scaffold?: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
}

export interface Conversation {
  id: string;
  messages: Message[];
  created_at: string;
  updated_at: string;
}

export interface Memory {
  id: string;
  content: string;
  embedding?: number[];
  created_at: string;
  relevance_score?: number;
}

export interface AutonomyStatus {
  status: 'active' | 'inactive';
  timestamp: string;
  statistics: {
    total_tasks: number;
    by_status: {
      pending: number;
      running: number;
      completed: number;
      failed: number;
      waiting_for_ho: number;
    };
    by_classification: {
      auto: number;
      ho: number;
      approval: number;
    };
  };
  last_run?: string;
  tasks_executed: number;
}

export interface GitHubIssue {
  number: number;
  title: string;
  body: string;
  state: 'open' | 'closed';
  created_at: string;
  updated_at: string;
  labels: string[];
}

export interface HealthStatus {
  status: 'alive' | 'degraded' | 'down';
  message: string;
  timestamp: string;
  version?: string;
  environment?: string;
  database?: string;
  redis?: string;
  gemini?: string;
  uptime_seconds?: number;
}

export interface ApiError {
  message: string;
  status: number;
  details?: any;
}
