import { useState, useEffect, useCallback, useRef } from 'react';
import type { AutonomyStatus } from '../types';

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

/**
 * Hook for real-time autonomy status updates using WebSocket/SSE with polling fallback
 */
export function useAutonomyRealtime(options: UseAutonomyRealtimeOptions = {}): UseAutonomyRealtimeReturn {
  const {
    enabled = true,
    pollingInterval = 5000,
    maxRetries = 3,
    reconnectDelay = 2000,
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

  // Refs for managing connections and timers
  const wsRef = useRef<WebSocket | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Get API base URL
  const getBaseUrl = useCallback(() => {
    const runtimeConfig = (window as any).__KORTANA__;
    if (runtimeConfig && runtimeConfig.VITE_API_URL) {
      return runtimeConfig.VITE_API_URL;
    }
    if (import.meta.env.VITE_API_URL) {
      return import.meta.env.VITE_API_URL;
    }
    if (typeof window !== 'undefined' && window.location.port === '5173') {
      return 'http://localhost:8000';
    }
    return '';
  }, []);

  // Fetch status via REST API (for polling fallback)
  const fetchStatus = useCallback(async () => {
    try {
      const baseUrl = getBaseUrl();
      const response = await fetch(`${baseUrl}/api/autonomy/status`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setStatus(data);
      setError(null);
      setConnectionState(prev => ({
        ...prev,
        lastError: null,
      }));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setConnectionState(prev => ({
        ...prev,
        lastError: errorMessage,
      }));
      throw err;
    }
  }, [getBaseUrl]);

  // Start polling fallback
  const startPolling = useCallback(() => {
    setConnectionState(prev => ({
      ...prev,
      fallbackToPolling: true,
      isConnected: false,
      isConnecting: false,
    }));

    const poll = async () => {
      try {
        await fetchStatus();
        setIsLoading(false);
      } catch (err) {
        console.warn('Polling failed:', err);
      }
    };

    poll(); // Initial fetch
    pollingTimerRef.current = setInterval(poll, pollingInterval);
  }, [fetchStatus, pollingInterval]);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingTimerRef.current) {
      clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  // Try WebSocket connection
  const connectWebSocket = useCallback(() => {
    if (!enabled) return;

    setConnectionState(prev => ({
      ...prev,
      isConnecting: true,
      retryCount: prev.retryCount + 1,
    }));

    try {
      const baseUrl = getBaseUrl();
      const wsUrl = baseUrl.replace(/^http/, 'ws') + '/api/autonomy/ws';

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected for autonomy status');
        setConnectionState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          lastError: null,
          retryCount: 0,
          fallbackToPolling: false,
        }));
        setError(null);
        setIsLoading(false);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setStatus(data);
          setError(null);
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onclose = (event) => {
        console.log('WebSocket closed:', event.code, event.reason);
        wsRef.current = null;

        setConnectionState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
        }));

        // Try SSE fallback if WebSocket fails and we haven't exceeded retries
        if (connectionState.retryCount < maxRetries) {
          setTimeout(() => connectSSE(), reconnectDelay);
        } else {
          console.log('Max retries reached, falling back to polling');
          startPolling();
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setConnectionState(prev => ({
          ...prev,
          lastError: 'WebSocket connection failed',
        }));
      };

    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      setConnectionState(prev => ({
        ...prev,
        isConnecting: false,
        lastError: 'WebSocket creation failed',
      }));

      // Try SSE fallback
      if (connectionState.retryCount < maxRetries) {
        setTimeout(() => connectSSE(), reconnectDelay);
      } else {
        startPolling();
      }
    }
  }, [enabled, getBaseUrl, connectionState.retryCount, maxRetries, reconnectDelay, startPolling]);

  // Try Server-Sent Events connection
  const connectSSE = useCallback(() => {
    if (!enabled) return;

    setConnectionState(prev => ({
      ...prev,
      isConnecting: true,
      retryCount: prev.retryCount + 1,
    }));

    try {
      const baseUrl = getBaseUrl();
      const sseUrl = `${baseUrl}/api/autonomy/sse`;

      const eventSource = new EventSource(sseUrl);
      eventSourceRef.current = eventSource;

      eventSource.onopen = () => {
        console.log('SSE connected for autonomy status');
        setConnectionState(prev => ({
          ...prev,
          isConnected: true,
          isConnecting: false,
          lastError: null,
          retryCount: 0,
          fallbackToPolling: false,
        }));
        setError(null);
        setIsLoading(false);
      };

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setStatus(data);
          setError(null);
        } catch (err) {
          console.error('Failed to parse SSE message:', err);
        }
      };

      eventSource.onerror = (event) => {
        console.error('SSE error:', event);
        eventSourceRef.current = null;

        setConnectionState(prev => ({
          ...prev,
          isConnected: false,
          isConnecting: false,
          lastError: 'SSE connection failed',
        }));

        // Fall back to polling if SSE fails
        if (connectionState.retryCount >= maxRetries) {
          console.log('Max retries reached, falling back to polling');
          startPolling();
        } else {
          // Try WebSocket again after delay
          setTimeout(() => connectWebSocket(), reconnectDelay);
        }
      };

    } catch (err) {
      console.error('Failed to create SSE:', err);
      setConnectionState(prev => ({
        ...prev,
        isConnecting: false,
        lastError: 'SSE creation failed',
      }));

      // Fall back to polling
      startPolling();
    }
  }, [enabled, getBaseUrl, connectionState.retryCount, maxRetries, reconnectDelay, startPolling, connectWebSocket]);

  // Manual reconnect
  const reconnect = useCallback(() => {
    disconnect();
    setConnectionState(prev => ({
      ...prev,
      retryCount: 0,
      fallbackToPolling: false,
    }));
    connectWebSocket();
  }, [connectWebSocket]);

  // Disconnect all connections
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    stopPolling();

    setConnectionState(prev => ({
      ...prev,
      isConnected: false,
      isConnecting: false,
    }));
  }, [stopPolling]);

  // Initialize connection on mount
  useEffect(() => {
    if (enabled) {
      // Initial fetch to get current status
      fetchStatus().finally(() => setIsLoading(false));

      // Try WebSocket first, then SSE, then polling
      connectWebSocket();
    }

    return () => {
      disconnect();
    };
  }, [enabled, connectWebSocket, fetchStatus, disconnect]);

  // Cleanup on unmount
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