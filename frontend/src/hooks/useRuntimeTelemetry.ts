import { useSyncExternalStore } from 'react';
import { api, type ApiError } from '../lib/api';
import type { DaemonStatus, HealthStatus, ModelLaneSummary } from '../types';

type RuntimeResourceKey = 'health' | 'daemon' | 'lanes';

interface RuntimeResourceState<T> {
  value: T | null;
  error: string | null;
  retryAfterMs: number | null;
  fetchedAt: number;
  inflight: Promise<T | null> | null;
}

export interface RuntimeTelemetrySnapshot {
  health: HealthStatus | null;
  daemon: DaemonStatus | null;
  lanes: ModelLaneSummary | null;
  errors: Partial<Record<RuntimeResourceKey, string>>;
  loading: boolean;
  refreshing: boolean;
  lastUpdatedAt: string | null;
}

interface RefreshRuntimeTelemetryOptions {
  force?: boolean;
  resources?: RuntimeResourceKey[];
}

const VISIBLE_POLL_MS = 15000;
const HIDDEN_POLL_MS = 30000;

const listeners = new Set<() => void>();

const resourceState: {
  health: RuntimeResourceState<HealthStatus>;
  daemon: RuntimeResourceState<DaemonStatus>;
  lanes: RuntimeResourceState<ModelLaneSummary>;
} = {
  health: {
    value: null,
    error: null,
    retryAfterMs: null,
    fetchedAt: 0,
    inflight: null,
  },
  daemon: {
    value: null,
    error: null,
    retryAfterMs: null,
    fetchedAt: 0,
    inflight: null,
  },
  lanes: {
    value: null,
    error: null,
    retryAfterMs: null,
    fetchedAt: 0,
    inflight: null,
  },
};

let refreshing = false;
let lastUpdatedAt: string | null = null;
let pollTimer: number | null = null;
let pollingActive = false;
let subscriberCount = 0;

function notifyListeners() {
  listeners.forEach((listener) => listener());
}

function readApiError(error: unknown): Error & Partial<ApiError> {
  if (error instanceof Error) {
    return error as Error & Partial<ApiError>;
  }

  return new Error('Unknown error') as Error & Partial<ApiError>;
}

function describeRuntimeError(error: unknown, fallback: string): string {
  const apiError = readApiError(error);
  if (apiError.isRateLimited) {
    return apiError.retryAfterSeconds
      ? `Rate limit reached. Refreshing again in ${apiError.retryAfterSeconds}s.`
      : 'Rate limit reached. Refreshing again shortly.';
  }
  if (apiError.isOffline) {
    return 'Backend is unreachable right now. Retrying automatically.';
  }
  return apiError.message || fallback;
}

function recommendedDelayMs(resources: RuntimeResourceKey[]): number {
  const hidden = typeof document !== 'undefined' && document.visibilityState === 'hidden';
  const baseDelay = hidden ? HIDDEN_POLL_MS : VISIBLE_POLL_MS;
  const retryAfterMs = resources.reduce<number | null>((longestDelay, key) => {
    const nextDelay = resourceState[key].retryAfterMs;
    if (nextDelay === null) {
      return longestDelay;
    }
    return longestDelay === null ? nextDelay : Math.max(longestDelay, nextDelay);
  }, null);
  return retryAfterMs ?? baseDelay;
}

function getSnapshot(): RuntimeTelemetrySnapshot {
  return {
    health: resourceState.health.value,
    daemon: resourceState.daemon.value,
    lanes: resourceState.lanes.value,
    errors: {
      health: resourceState.health.error ?? undefined,
      daemon: resourceState.daemon.error ?? undefined,
      lanes: resourceState.lanes.error ?? undefined,
    },
    loading: !lastUpdatedAt && refreshing,
    refreshing,
    lastUpdatedAt,
  };
}

async function loadHealth(force = false, maxAgeMs = 0): Promise<HealthStatus | null> {
  const state = resourceState.health;
  if (!force && state.value && Date.now() - state.fetchedAt <= maxAgeMs) {
    return state.value;
  }
  if (state.inflight) {
    return state.inflight;
  }

  state.inflight = api.health()
    .then((value) => {
      state.value = value;
      state.error = null;
      state.retryAfterMs = null;
      state.fetchedAt = Date.now();
      lastUpdatedAt = new Date().toISOString();
      return value;
    })
    .catch((error: unknown) => {
      const apiError = readApiError(error);
      state.error = describeRuntimeError(error, 'System status refresh failed.');
      state.retryAfterMs = apiError.retryAfterSeconds ? apiError.retryAfterSeconds * 1000 : null;
      throw error;
    })
    .finally(() => {
      state.inflight = null;
      notifyListeners();
    });

  notifyListeners();
  return state.inflight;
}

async function loadDaemon(force = false, maxAgeMs = 0): Promise<DaemonStatus | null> {
  const state = resourceState.daemon;
  if (!force && state.value && Date.now() - state.fetchedAt <= maxAgeMs) {
    return state.value;
  }
  if (state.inflight) {
    return state.inflight;
  }

  state.inflight = api.getDaemonStatus()
    .then((value) => {
      state.value = value;
      state.error = null;
      state.retryAfterMs = null;
      state.fetchedAt = Date.now();
      lastUpdatedAt = new Date().toISOString();
      return value;
    })
    .catch((error: unknown) => {
      const apiError = readApiError(error);
      state.error = describeRuntimeError(error, 'Daemon runtime refresh failed.');
      state.retryAfterMs = apiError.retryAfterSeconds ? apiError.retryAfterSeconds * 1000 : null;
      throw error;
    })
    .finally(() => {
      state.inflight = null;
      notifyListeners();
    });

  notifyListeners();
  return state.inflight;
}

async function loadLanes(force = false, maxAgeMs = 0): Promise<ModelLaneSummary | null> {
  const state = resourceState.lanes;
  if (!force && state.value && Date.now() - state.fetchedAt <= maxAgeMs) {
    return state.value;
  }
  if (state.inflight) {
    return state.inflight;
  }

  state.inflight = api.getModelLaneSummary()
    .then((value) => {
      state.value = value;
      state.error = null;
      state.retryAfterMs = null;
      state.fetchedAt = Date.now();
      lastUpdatedAt = new Date().toISOString();
      return value;
    })
    .catch((error: unknown) => {
      const apiError = readApiError(error);
      state.error = describeRuntimeError(error, 'Model routing summary refresh failed.');
      state.retryAfterMs = apiError.retryAfterSeconds ? apiError.retryAfterSeconds * 1000 : null;
      throw error;
    })
    .finally(() => {
      state.inflight = null;
      notifyListeners();
    });

  notifyListeners();
  return state.inflight;
}

async function loadResource(
  key: RuntimeResourceKey,
  force = false,
  maxAgeMs = 0
): Promise<HealthStatus | DaemonStatus | ModelLaneSummary | null> {
  switch (key) {
    case 'health':
      return loadHealth(force, maxAgeMs);
    case 'daemon':
      return loadDaemon(force, maxAgeMs);
    case 'lanes':
      return loadLanes(force, maxAgeMs);
    default:
      return null;
  }
}

function clearPollTimer() {
  if (pollTimer !== null) {
    window.clearTimeout(pollTimer);
    pollTimer = null;
  }
}

function schedulePoll(resources: RuntimeResourceKey[]) {
  if (!pollingActive || subscriberCount === 0) {
    return;
  }

  clearPollTimer();
  pollTimer = window.setTimeout(() => {
    void refreshRuntimeTelemetry({ resources })
      .finally(() => {
        schedulePoll(resources);
      });
  }, recommendedDelayMs(resources));
}

function startPolling(resources: RuntimeResourceKey[] = ['health', 'daemon', 'lanes']) {
  if (pollingActive) {
    return;
  }
  pollingActive = true;
  void refreshRuntimeTelemetry({ resources })
    .finally(() => {
      schedulePoll(resources);
    });
}

function stopPolling() {
  pollingActive = false;
  clearPollTimer();
}

if (typeof document !== 'undefined') {
  document.addEventListener('visibilitychange', () => {
    if (!pollingActive) {
      return;
    }
    schedulePoll(['health', 'daemon', 'lanes']);
  });
}

export async function refreshRuntimeTelemetry(
  options: RefreshRuntimeTelemetryOptions = {}
): Promise<RuntimeTelemetrySnapshot> {
  const resources = options.resources ?? ['health', 'daemon', 'lanes'];
  const force = options.force ?? false;

  refreshing = true;
  notifyListeners();

  await Promise.allSettled(
    resources.map((key) => loadResource(key, force))
  );

  refreshing = false;
  notifyListeners();
  return getSnapshot();
}

export async function getCachedModelLaneSummary(maxAgeMs = 1500): Promise<ModelLaneSummary> {
  const lanes = await loadLanes(false, maxAgeMs);
  if (!lanes) {
    throw new Error('Model routing summary unavailable.');
  }
  return lanes;
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  subscriberCount += 1;
  if (subscriberCount === 1) {
    startPolling();
  }

  return () => {
    listeners.delete(listener);
    subscriberCount = Math.max(0, subscriberCount - 1);
    if (subscriberCount === 0) {
      stopPolling();
    }
  };
}

export function useRuntimeTelemetry(): RuntimeTelemetrySnapshot & {
  refresh: (options?: RefreshRuntimeTelemetryOptions) => Promise<RuntimeTelemetrySnapshot>;
} {
  const snapshot = useSyncExternalStore(subscribe, getSnapshot, getSnapshot);
  return {
    ...snapshot,
    refresh: refreshRuntimeTelemetry,
  };
}
