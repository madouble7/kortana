/**
 * TypeScript type definitions for Kor'tana
 */

export type ChatPhase = 'analysis' | 'commentary' | 'final_answer';

export interface QueuedTaskSummary {
  id: string;
  name: string;
  branch: string;
}

export interface ChatHistoryEntry {
  role: 'user' | 'assistant';
  content: string;
  phase?: ChatPhase;
}

export interface ChatTurnMetadata {
  phase?: ChatPhase;
  provider?: string;
  model?: string;
  lane?: string;
  response_id?: string;
  stateful?: boolean;
  used_previous_response_id?: boolean;
  input_tokens?: number;
  output_tokens?: number;
  tasks_queued?: QueuedTaskSummary[];
}

export interface ChatUsageMetrics {
  tokens: number;
  inputTokens?: number;
  outputTokens?: number;
  costUsd: number;
  sessionCostUsd?: number;
  live?: boolean;
  estimated?: boolean;
  source?: 'local' | 'telemetry' | 'openai';
}

export interface SandboxResult {
  ok: boolean;
  status: string;
  error?: string;
  artifacts?: {
    id?: string;
    description?: string;
    plan?: {
      steps?: string[];
      files_to_change?: string[];
      tests_to_run?: string[];
      expected_behavior?: string;
      rollback_points?: string[];
      risk_assessment?: string;
      safety_measures?: string[];
    };
    changeset?: {
      files_changed?: string[];
      diff?: string;
      commit_msg?: string;
    };
    test_report?: {
      command?: string;
      exit_code?: number;
      stdout?: string;
      stderr?: string;
    };
    review_summary?: {
      approved?: boolean;
      blocking_issues?: string[];
      non_blocking_notes?: string[];
      risk_reassessment?: number;
    };
    deployment_manifest?: {
      taskId?: string;
      stagingSubDir?: string;
      files?: string[];
      timestamp?: string;
      dryRun?: boolean;
      status?: string;
    };
  };
}

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'waiting_for_ho' | 'planning_complete' | string;
  priority: 'low' | 'medium' | 'high';
  classification?: 'auto' | 'ho' | 'approval';
  created_at: string;
  updated_at: string;
  result?: string;
  error?: string;
  hop_capable?: boolean;
  hop_executed_by?: 'human' | 'hop';
  ho_scaffold?: string;
  sandbox_result?: SandboxResult;
}

export interface Message extends ChatTurnMetadata {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: string;
  streaming?: boolean;
  usage?: ChatUsageMetrics;
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

export interface ModelUsageSummary {
  total_generations: number;
  total_tokens_used: number;
  last_recorded_at?: string | null;
  by_provider: Record<string, number>;
  by_provider_tokens: Record<string, number>;
}

export interface CostProviderSummary {
  model: string;
  lane: string;
  is_free_tier: boolean;
  input_cost_per_1k?: number;
  output_cost_per_1k?: number;
  requests: number;
  total_tokens: number;
  cooling_down?: boolean;
  cooldown_seconds?: number;
  last_error?: string | null;
  last_task_type?: string | null;
  last_used_at?: string | null;
}

export interface AdaptiveRetryEvent {
  operation_id: string;
  provider?: string | null;
  task_type?: string | null;
  error_category: string;
  error_type: string;
  attempt: number;
  will_retry: boolean;
  delay_seconds?: number | null;
  timestamp: string;
}

export interface AdaptiveRetrySummary {
  total_events: number;
  scheduled_retries: number;
  skipped_retries: number;
  by_category: Record<string, number>;
  last_recorded_at?: string | null;
  recent: AdaptiveRetryEvent[];
}

export interface ModelLaneSummary {
  active_lane: string;
  runtime_usage: {
    total_generations: number;
    total_tokens_used: number;
    memory: ModelUsageSummary;
    persisted: ModelUsageSummary;
  };
  cost_router: {
    cost: {
      total_daily_spend: string;
      total_monthly_spend: string;
      report_generated_at?: string;
      totals: {
        daily_spend_usd: number;
        monthly_spend_usd: number;
        requests: number;
        input_tokens: number;
        output_tokens: number;
        total_tokens: number;
      };
      providers: Record<string, CostProviderSummary>;
      free_tier_usage: Record<string, number>;
    };
  };
  adaptive_retry: AdaptiveRetrySummary;
}

export interface DaemonCycle {
  cycle_id: string;
  start_time: string;
  end_time: string | null;
  tasks_processed: number;
  approvals_processed: number;
  errors_encountered: number;
  metrics: {
    deferred?: number;
    failed?: number;
    succeeded?: number;
    processed?: number;
    system_state?: string;
    task_events?: Array<{
      type: string;
      timestamp: string;
      data: {
        task_id?: string;
        title?: string;
        reason?: string;
        error?: string;
        status?: string;
        [key: string]: unknown;
      };
    }>;
    [key: string]: unknown;
  } | null;
}

export interface DaemonStatus {
  deployment_mode: 'embedded' | 'external';
  control_available: boolean;
  message: string;
  running?: boolean;
  enabled?: boolean;
  cycle_interval_seconds?: number;
  base_cycle_interval_seconds?: number;
  max_tasks_per_cycle?: number;
  base_max_tasks_per_cycle?: number;
  github_mode?: string;
  safe_mode?: boolean;
  live_execution_enabled?: boolean;
  control_mode?: string;
  workspace_bridge?: unknown;
  last_cycle?: Record<string, unknown>;
  provider_health?: Record<string, string>;
  local_process?: { running: boolean; enabled: boolean };
  external_daemon?: {
    alive: boolean;
    state: 'alive' | 'stale' | 'unknown';
    message: string;
    last_cycle_id?: string;
    last_cycle_completed_at?: string;
    seconds_since_last_cycle?: number;
    stale_after_seconds: number;
    tasks_processed?: number;
    errors_encountered?: number;
    provider_health?: Record<string, string>;
    system_state?: string;
    safe_mode?: boolean;
    live_execution_enabled?: boolean;
    control_mode?: string;
    workspace_bridge?: unknown;
    operator_guidance?: string | null;
    autonomy_index?: number | null;
  };
}

export interface ApiError {
  message: string;
  status: number;
  details?: unknown;
  retryAfterSeconds?: number;
  isRateLimited?: boolean;
  isOffline?: boolean;
  isAborted?: boolean;
}
