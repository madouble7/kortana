/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/

// Redefine LiveServerMessage locally to avoid potential conflicts or outdated type definitions
// from @google/genai, aligning with current usage in services/apiService.ts and
// components/LiveConversation.tsx
export interface LiveServerMessage {
  serverContent?: {
    modelTurn?: {
      parts: Array<{
        inlineData?: {
          data: string; // base64 encoded audio
          mimeType: string;
        };
      }>;
    };
    inputTranscription?: { text: string };
    outputTranscription?: { text: string };
    turnComplete?: boolean;
    interrupted?: boolean;
  };
  toolCall?: {
    functionCalls: Array<{
      name: string;
      args: { [key: string]: any };
      id: string;
    }>;
  };
}

export type Role = 'system' | 'user' | 'assistant';

export interface ChatMessage {
  id: string;
  role: Role;
  text: string;
  createdAt: string; // ISO
  used_rag?: boolean;
}

export type GeminiModel = 'gemini-2.5-flash' | 'gemini-3.1-flash-lite-preview';
export type ImageAspectRatio = '1:1' | '3:4' | '4:3' | '9:16' | '16:9';
export type VideoAspectRatio = '16:9' | '9:16';
export type VideoResolution = '720p' | '1080p';

export interface ChatTextResponse {
  reply: string;
  used_rag: boolean;
}

export interface ChatAudioResponse {
  transcript: string;

  summary: string;
  reply: string;
}

// Types for Search Grounding
export interface GroundingSource {
  uri: string;
  title: string;
}

export interface SearchGroundingResponse {
  reply: string;
  sources: GroundingSource[];
}

// Types for Maps Grounding
export interface MapsGroundingResponse {
  reply: string;
  sources: GroundingSource[];
}

// Types for Text-to-Speech
export interface TextToSpeechResponse {
  audio_base64: string;
  mime_type: string;
}

// Types for Image Analysis
export interface ImageAnalysisResponse {
  analysis: string;
}

// Types for Video Analysis
export interface VideoAnalysisResponse {
  analysis: string;
}

// Types for Day Capture
export interface Snapshot {
  session_id: string;
  updated_at: string;
  last_chunk_ts: string;
  summary: string;
  words: number;
  actions: string[];
  diarization: 'on' | 'off';
  pii_redaction: boolean;
}

export interface StartSessionResp {
  session_id: string;
  presign: any;
  bucket: string;
  prefix: string;
}

// Types for Knowledge Base (RAG v2)
export interface RagUploadResult {
  document_id: string;
  filename: string;
  chunks: number;
  namespace: string;
}

export interface RagMatch {
  id: string;
  text: string;
  score: number;
  metadata: {
    document_id: string;
    filename: string;
    chunk_id: number;
    uploaded_at: number;
  };
}

export interface RagQueryResponse {
  answer?: string;
  matches: RagMatch[];
}


// Types for Builder Agent
export interface BuilderPlan {
  goal: string;
  steps: string[];
}

// Type for Document Scanner
export interface OcrResponse {
  text: string;
}

// Type for Image Generation
export interface ImageGenerateResponse {
  image_base64: string;
  model: string;
  prompt_hash: string;
  cached?: boolean;
}

// Type for Image Editing
export interface ImageEditResponse {
  image_base64: string;
  text: string | null;
}

// Type for Rclone Sync Status
export interface RcloneStatus {
  last_run_ts: string | null;
  last_success_ts: string | null;
  last_error_ts: string | null;
  last_error: string | null;
  duration_sec: number | null;
  result: 'not_run_yet' | 'skipped' | 'success' | 'error' | string;
  mode?: 'pull' | 'push' | 'sync';
}

// Type for Video Generation
export interface VideoOperation {
  name: string; // e.g., "operations/12345"
  done: boolean;
  response?: {
    generatedVideos: {
      video: {
        uri: string;
      };
    }[];
  };
  error?: {
    code: number;
    message: string;
  };
}

// Type for Code Snippet Generation
export interface CodeSnippetResponse {
  code: string;
  language: string;
}

// Type for Web Search
export interface WebSource {
  uri: string;
  title: string;
}

export interface WebSearchResponse {
  reply: string;
  sources: WebSource[];
}

// Types for Autonomy Audit
export interface AuditCodeItem {
  code: string;
  language: string;
}
export type AuditContentItem = string | AuditCodeItem;
export interface AuditSection {
  title: string;
  content: AuditContentItem[];
}

// Type for Weather Forecast
export interface WeatherResponse {
  location: string;
  current: {
    temperature_2m: number;
    weather_code: number;
  };
  hourly: {
    time: string[];
    temperature_2m: number[];
  };
}

// Type for Tech News
export interface HackerNewsStory {
  id: number;
  title: string;
  url?: string;
  score: number;
  by: string;
  time: number;
}

// Type for Public Holidays
export interface PublicHoliday {
  date: string;
  localName: string;
  name: string;
  countryCode: string;
}

// Type for Book Finder
export interface BookSearchResult {
  title: string;
  author_name?: string[];
  first_publish_year?: number;
  cover_i?: number;
}

// Type for Stripe Integration
export interface StripeCheckoutSessionResponse {
  url: string;
}

// Type for Autonomy Telemetry
export interface AutonomyHeartbeat {
  status: string;
  uptime: number;
  thought_cycles: number;
  resonance: number;
}

// Types for Constellation Dashboard
export type AgentStatus = 'online' | 'processing' | 'offline';
export interface Agent {
  id: string;
  name: string;
  glyph: string;
  title: string;
  purpose: string;
  status: AgentStatus;
  position: {
    gridArea: string;
    coords: { x: number; y: number };
  };
  // Optional details for modal view
  history?: string[];
  completedRituals?: number[];
  emotionalPulse?: string;
}

export interface Ritual {
  id: number;
  title: string;
  status: 'completed' | 'in-progress';
  agentIds: string[];
  reuseMetrics?: {
    linesGrafted: number;
    reuseRatio: number;
  };
}

// Types for Autonomous Task System
export type TaskPriority = 'urgent' | 'normal' | 'low';
export type TaskStatus = 'new' | 'triaged' | 'proposing' | 'planned' | 'in_progress' | 'coded' | 'tested' | 'reviewed' | 'approved' | 'merged' | 'verified' | 'blocked' | 'needs_human' | 'failed' | 'retriable_failed' | 'abandoned' | 'available' | 'claimed' | 'completed';

export interface ChangeSet {
  files_changed: string[];
  diff: string;
  commit_msg?: string;
}

export interface TestReport {
  command: string;
  exit_code: number;
  stdout: string;
  stderr: string;
  coverage?: number;
  failed_tests?: string[];
}

export interface ReviewSummary {
  approved: boolean;
  blocking_issues: string[];
  non_blocking_notes: string[];
  risk_reassessment: number;
}

export interface MergeResult {
  merge_sha: string;
  pr_url?: string;
  merged_at: string;
}

export interface Task {
  id: string;
  description: string;
  priority: TaskPriority;
  status: TaskStatus;
  assigned_to?: string;
  created_at: string; // ISO string
  estimated_hours?: number;
  completed_at?: string; // ISO string
  risk_score?: number;
  plan?: TaskPlan;
  changeset?: ChangeSet;
  test_report?: TestReport;
  review_summary?: ReviewSummary;
  merge_result?: MergeResult;
  deployment_manifest?: any; // To avoid circular imports, but typically DeploymentManifest
  retries?: number;
}

export interface ServiceResult<T = any> {
  ok: boolean;
  status: "passed" | "failed" | "blocked" | "needs_human";
  artifacts?: T;
  error?: string;
}

export interface TaskPlan {
  steps: string[];
  files_to_change: string[];
  tests_to_run: string[];
  expected_behavior: string;
  rollback_points: string[];
  risk_assessment?: string;
  safety_measures?: string[];
}

// Types for Heuristic Management
export interface HeuristicWeights {
  base_layer: number;
  decision_layer: number;
  alignment_monitor: number;
  [key: string]: number;
}

export interface BehavioralParameters {
  max_uncertainty_threshold: number;
  alignment_mode: 'strict' | 'flexible';
  log_audit: boolean;
  simulation_iters: number;
}

export interface HeuristicOverride {
  id: string;
  taskId: string;
  weights?: Partial<HeuristicWeights>;
  parameters?: Partial<BehavioralParameters>;
  reason: string;
  timestamp: string;
  status: 'pending' | 'verified' | 'rejected' | 'integrated';
}

// View and Tool types for App navigation
/** canonical view + tool typing (single source of truth) */
export const VIEW_LIST = [
  'dashboard', 'chat', 'privacy', 'localServer', 'dayCapture', 'knowledge', 'builder', 'scanner',
  'rclone', 'image', 'video', 'imageEditor', 'deployment', 'codeSnippet', 'webSearch', 'devEnvSetup',
  'autonomousCoder', 'autonomyAudit', 'liveConversation', 'dataVisualizer', 'weather', 'techNews',
  'holidays', 'bookFinder', 'stripe', 'localCloudIntegration', 'googleAIStudio', 'langGraph',
  'constellation', 'taskQueue', 'covenantOpsLog', // Existing
  'imageAnalyzer', 'videoAnalyzer', 'textToSpeech', 'searchGrounding', 'mapsGrounding', // New
  'github', 'systemMonitor', 'memoryManager', 'book', 'prayerAgent'
] as const;

export type View = (typeof VIEW_LIST)[number];
export type ToolId = Exclude<View, 'dashboard'> | 'transcribe';
