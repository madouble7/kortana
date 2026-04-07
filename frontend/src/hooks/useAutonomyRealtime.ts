import { useCallback, useEffect, useRef, useState } from 'react';
import type { AutonomyStatus } from '../types';
import { getApiBaseUrl } from '../lib/runtimeConfig';

interface ConnectionState {
  isConnected: boolean;
  isConnecting: boolean;
  lastError: string | null;
  retryCount: number;
  fallbackToPolling: boolean;
}

interface UseAutonomyRealtimeOptions {
  enabled?: boolean;
  pollingInterval?: number;
  maxRetries?: number;
  reconnectDelay?: number;
}

interface UseAutonomyRealtimeReturn {
  status: AutonomyStatus | null;
  connectionState: ConnectionState;
  isLoading: boolean;
  error: string | null;
  reconnect: () => void;
  disconnect: () => void;
}

interface AutonomyRealtimeError extends Error {
  status?: number;
  retryAfterMs?: number;
}

interface RawAutonomyStatusResponse {
  total_tasks?: number;
  stats?: Record<string, number | string | undefined>;
  recent_tasks?: Array<{
    updated_at?: string;
  }>;
}

const toAutonomyStatus = (data: RawAutonomyStatusResponse): AutonomyStatus => {
  const stats = data?.stats ?? {};
  const pending = Number(stats.pending ?? 0);
  const running =
    Number(stats.running ?? 0) +
    Number(stats.analyzing ?? 0) +
    Number(stats.planning ?? 0) +
    Number(stats.ready_to_execute ?? 0) +
    Number(stats.executing ?? 0);
  const completed = Number(stats.completed ?? 0);
  const failed = Number(stats.failed ?? 0);
  const total = Number(data?.total_tasks ?? 0) || pending + running + completed + failed;

  return {
    status: total > 0 ? 'active' : 'inactive',
    timestamp: new Date().toISOString(),
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
};

const getRetryAfterMs = (response: Response, responseBody: unknown): number | undefined => {
  const retryAfterHeader = response.headers.get('Retry-After');
  const retryAfterSeconds = retryAfterHeader ? Number.parseInt(retryAfterHeader, 10) : Number.NaN;

  if (Number.isFinite(retryAfterSeconds) && retryAfterSeconds > 0) {
    return retryAfterSeconds * 1000;
  }

  if (
    typeof responseBody === 'object' &&
    responseBody !== null &&
    'retry_after' in responseBody &&
    typeof (responseBody as { retry_after?: unknown }).retry_after === 'number'
  ) {
    return (responseBody as { retry_after: number }).retry_after * 1000;
  }

  return undefined;
};

const readAutonomyErrorMessage = (error: unknown): string => {
  if (error instanceof Error) {
    return error.message;
  }

  return 'Unknown error';
};

/**
 * Hook for autonomy status updates using polling.
 *
 * The current backend does not expose `/api/autonomy/ws` or `/api/autonomy/sse`,
 * so this hook intentionally polls the canonical status endpoint instead of
 * thrashing dead realtime transports.
 */
export function useAutonomyRealtime(options: UseAutonomyRealtimeOptions = {}): UseAutonomyRealtimeReturn {
  const {
    enabled = true,
    pollingInterval = 5000,
  } = options;

  const [status, setStatus] = useState<AutonomyStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [connectionState, setConnectionState] = useState<ConnectionState>({
    isConnected: false,
    isConnecting: false,
    lastError: null,
    retryCount: 0,
    fallbackToPolling: false,
  });

  const pollingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pollingActiveRef = useRef(false);

  const fetchStatus = useCallback(async () => {
    try {
      const baseUrl = getApiBaseUrl();
      const response = await fetch(`${baseUrl}/api/autonomy/status`);

      if (!response.ok) {
        const responseBody = await response.json().catch(() => ({}));
        const requestError = new Error(
          response.status === 429
            ? 'HTTP 429: Too many requests'
            : `HTTP ${response.status}: ${response.statusText}`
        ) as AutonomyRealtimeError;

        requestError.status = response.status;
        requestError.retryAfterMs = getRetryAfterMs(response, responseBody);
        throw requestError;
      }

      const data = (await response.json()) as RawAutonomyStatusResponse;
      setStatus(toAutonomyStatus(data));
      setError(null);
      setConnectionState(prev => ({
        ...prev,
        lastError: null,
      }));
    } catch (err) {
      const errorMessage = readAutonomyErrorMessage(err);
      setError(errorMessage);
      setConnectionState(prev => ({
        ...prev,
        lastError: errorMessage,
      }));
      throw err;
    }
  }, []);

  const stopPolling = useCallback(() => {
    pollingActiveRef.current = false;

    if (pollingTimerRef.current) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  const startPolling = useCallback((initialDelay = 0) => {
    stopPolling();
    pollingActiveRef.current = true;

    setConnectionState(prev => ({
      ...prev,
      fallbackToPolling: true,
      isConnected: false,
      isConnecting: false,
      retryCount: 0,
    }));

    const poll = async () => {
      let nextPollDelay = pollingInterval;

      try {
        await fetchStatus();
        setIsLoading(false);
      } catch (err) {
        console.warn('Polling failed:', err);
        nextPollDelay =
          (err as AutonomyRealtimeError | undefined)?.retryAfterMs ??
          pollingInterval * 2;
      }

      if (!enabled || !pollingActiveRef.current) {
        return;
      }

      pollingTimerRef.current = setTimeout(poll, nextPollDelay);
    };

    pollingTimerRef.current = setTimeout(poll, initialDelay);
  }, [enabled, fetchStatus, pollingInterval, stopPolling]);

  const disconnect = useCallback(() => {
    stopPolling();
    setConnectionState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, [stopPolling]);

  const reconnect = useCallback(() => {
    disconnect();
    setError(null);
    setIsLoading(true);
    startPolling();
  }, [disconnect, startPolling]);

  useEffect(() => {
    if (!enabled) {
      return undefined;
    }

    setIsLoading(true);
    startPolling();

    return () => {
      disconnect();
    };
  }, [disconnect, enabled, startPolling]);

  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    status,
    connectionState,
    isLoading,
    error,
    reconnect,
    disconnect,
  };
}
