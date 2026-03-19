import { useState } from 'react';
import { Brain, Play, Activity, TrendingUp, Loader2, Wifi, WifiOff, RefreshCw } from 'lucide-react';
import { api } from '../lib/api';
import { formatRelativeTime } from '../lib/utils';
import { useAutonomyRealtime } from '../hooks/useAutonomyRealtime';

export default function Autonomy() {
  const [running, setRunning] = useState(false);

  const {
    status,
    connectionState,
    isLoading,
    error,
    reconnect,
  } = useAutonomyRealtime({
    enabled: true,
    pollingInterval: 5000,
    maxRetries: 3,
    reconnectDelay: 2000,
  });

  const triggerCycle = async () => {
    try {
      setRunning(true);
      await api.triggerAutonomyCycle();
      // Status will be updated automatically via real-time connection
    } catch (error) {
      console.error('Failed to trigger autonomy cycle:', error);
    } finally {
      setRunning(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold text-white">HOP Autonomy</h2>
          </div>
          <div className="flex items-center gap-4">
            {/* Connection Status */}
            <div className="flex items-center gap-2">
              {connectionState.isConnected ? (
                <Wifi className="w-4 h-4 text-green-400" />
              ) : connectionState.fallbackToPolling ? (
                <RefreshCw className="w-4 h-4 text-yellow-400 animate-spin" />
              ) : (
                <WifiOff className="w-4 h-4 text-red-400" />
              )}
              <span className="text-xs text-gray-400">
                {connectionState.isConnected
                  ? 'Real-time'
                  : connectionState.fallbackToPolling
                  ? 'Polling'
                  : 'Disconnected'
                }
              </span>
              {!connectionState.isConnected && !connectionState.fallbackToPolling && (
                <button
                  onClick={reconnect}
                  className="text-xs text-blue-400 hover:text-blue-300 underline"
                  disabled={connectionState.isConnecting}
                >
                  {connectionState.isConnecting ? 'Connecting...' : 'Reconnect'}
                </button>
              )}
            </div>

            {/* Autonomy Status */}
            <div className="flex items-center gap-2">
              <div
                className={`w-2 h-2 rounded-full ${
                  status?.status === 'active' ? 'bg-green-500 animate-pulse' : 'bg-gray-500'
                }`}
              />
              <span className="text-sm text-gray-400">
                {status?.status === 'active' ? 'Active' : 'Inactive'}
              </span>
            </div>
          </div>
        </div>

        {/* Connection Error Display */}
        {error && (
          <div className="mt-2 px-3 py-2 bg-red-900/20 border border-red-700/50 rounded-lg">
            <p className="text-sm text-red-400">
              Connection issue: {error}
              {connectionState.fallbackToPolling && (
                <span className="text-yellow-400 ml-2">Using polling fallback.</span>
              )}
            </p>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {/* Control Panel */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4">Control Panel</h3>
          <div className="flex gap-3">
            <button
              onClick={triggerCycle}
              disabled={running}
              className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-lg px-6 py-3 transition-colors"
            >
              {running ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Running Cycle...
                </>
              ) : (
                <>
                  <Play className="w-5 h-5" />
                  Trigger Autonomy Cycle
                </>
              )}
            </button>
          </div>
          <p className="text-gray-400 text-sm mt-3">
            Manually trigger an autonomy cycle to process pending tasks.
          </p>
          {status?.last_run && (
            <p className="text-gray-500 text-xs mt-2">
              Last run: {formatRelativeTime(status.last_run)}
            </p>
          )}
        </div>

        {/* Statistics */}
        {status?.statistics && (
          <>
            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Task Statistics
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Total Tasks</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {status.statistics.total_tasks}
                  </p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Pending</p>
                  <p className="text-2xl font-bold text-yellow-400 mt-1">
                    {status.statistics.by_status.pending}
                  </p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Running</p>
                  <p className="text-2xl font-bold text-blue-400 mt-1">
                    {status.statistics.by_status.running}
                  </p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Completed</p>
                  <p className="text-2xl font-bold text-green-400 mt-1">
                    {status.statistics.by_status.completed}
                  </p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Failed</p>
                  <p className="text-2xl font-bold text-red-400 mt-1">
                    {status.statistics.by_status.failed}
                  </p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Waiting HO</p>
                  <p className="text-2xl font-bold text-purple-400 mt-1">
                    {status.statistics.by_status.waiting_for_ho}
                  </p>
                </div>
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6">
              <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
                <TrendingUp className="w-5 h-5" />
                Classification Breakdown
              </h3>
              <div className="grid grid-cols-3 gap-4">
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Auto</p>
                  <p className="text-2xl font-bold text-green-400 mt-1">
                    {status.statistics.by_classification.auto}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Fully autonomous</p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">HO</p>
                  <p className="text-2xl font-bold text-blue-400 mt-1">
                    {status.statistics.by_classification.ho}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Human oversight</p>
                </div>
                <div className="bg-gray-900 rounded-lg p-4">
                  <p className="text-gray-400 text-sm">Approval</p>
                  <p className="text-2xl font-bold text-yellow-400 mt-1">
                    {status.statistics.by_classification.approval}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Needs approval</p>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Info */}
        <div className="bg-gray-800/50 rounded-lg p-6 border border-purple-900/30">
          <h3 className="text-purple-400 font-semibold mb-3">About HOP (Human Oversight Protocol)</h3>
          <p className="text-gray-300 text-sm leading-relaxed">
            The HOP autonomy system classifies tasks into three categories:
          </p>
          <ul className="mt-3 space-y-2 text-sm text-gray-400">
            <li className="flex items-start gap-2">
              <span className="text-green-400 mt-0.5">●</span>
              <span><strong className="text-white">Auto:</strong> Fully autonomous tasks that can execute without human intervention</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-blue-400 mt-0.5">●</span>
              <span><strong className="text-white">HO:</strong> Tasks requiring human oversight during execution</span>
            </li>
            <li className="flex items-start gap-2">
              <span className="text-yellow-400 mt-0.5">●</span>
              <span><strong className="text-white">Approval:</strong> Tasks requiring explicit human approval before execution</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
