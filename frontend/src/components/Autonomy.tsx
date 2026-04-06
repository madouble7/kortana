import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle,
  Loader2,
  Mic,
  Pause,
  Play,
  RefreshCw,
  Shield,
  TrendingUp,
  Wifi,
  WifiOff,
  XCircle,
} from 'lucide-react';
import { useState } from 'react';
import { useRuntimeTelemetry } from '../hooks/useRuntimeTelemetry';
import { useAutonomyRealtime } from '../hooks/useAutonomyRealtime';
import { api } from '../lib/api';
import { cn, formatRelativeTime } from '../lib/utils';
import { ApprovalQueue } from './ApprovalQueue';

function providerTone(status: string | undefined) {
  if (!status || status === 'unknown') {
    return 'bg-gray-800 text-gray-300';
  }
  if (status === 'ok') {
    return 'bg-green-900/60 text-green-300';
  }
  if (status.startsWith('backoff_until:')) {
    return 'bg-yellow-900/60 text-yellow-300';
  }
  return 'bg-red-900/60 text-red-300';
}

function metricTone(value: boolean | undefined, fallback: string, active: string, inactive: string) {
  if (value === undefined) {
    return fallback;
  }
  return value ? active : inactive;
}

function voiceTone(status: string | undefined) {
  switch (status) {
    case 'ready':
      return 'text-green-300 bg-green-950/40 border-green-800/50';
    case 'degraded':
      return 'text-yellow-200 bg-yellow-950/40 border-yellow-800/50';
    case 'configured':
      return 'text-blue-200 bg-blue-950/40 border-blue-800/50';
    default:
      return 'text-gray-300 bg-gray-900/60 border-gray-700';
  }
}

export default function Autonomy() {
  const [runningCycle, setRunningCycle] = useState(false);
  const [daemonActionPending, setDaemonActionPending] = useState<'start' | 'stop' | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

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

  const {
    daemon,
    lanes,
    errors,
    loading: runtimeLoading,
    refreshing: runtimeRefreshing,
    lastUpdatedAt,
    refresh,
  } = useRuntimeTelemetry();

  const runtimeError = errors.daemon || errors.lanes || null;

  const refreshRuntime = async () => {
    await refresh({ force: true, resources: ['daemon', 'lanes'] });
  };

  const triggerCycle = async () => {
    try {
      setRunningCycle(true);
      setActionError(null);
      await api.triggerAutonomyCycle();
    } catch (triggerError) {
      console.error('Failed to trigger autonomy cycle:', triggerError);
      setActionError(
        triggerError instanceof Error ? triggerError.message : 'Failed to trigger autonomy cycle.'
      );
    } finally {
      setRunningCycle(false);
      void refreshRuntime();
    }
  };

  const toggleDaemon = async (action: 'start' | 'stop') => {
    try {
      setDaemonActionPending(action);
      setActionError(null);
      await (action === 'start' ? api.startDaemon() : api.stopDaemon());
      await refresh({ force: true, resources: ['daemon'] });
    } catch (actionError) {
      console.error(`Failed to ${action} daemon:`, actionError);
      setActionError(
        actionError instanceof Error
          ? actionError.message
          : `Failed to ${action === 'start' ? 'start' : 'stop'} daemon.`
      );
    } finally {
      setDaemonActionPending(null);
      void refreshRuntime();
    }
  };

  if (isLoading && runtimeLoading && !status && !daemon) {
    return (
      <div className="flex items-center justify-center h-full bg-gray-900">
        <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
      </div>
    );
  }

  const daemonState = daemon?.deployment_mode === 'embedded'
    ? daemon?.running
      ? 'running'
      : 'idle'
    : daemon?.external_daemon?.state ?? 'unknown';
  const daemonAlive = daemon?.deployment_mode === 'embedded'
    ? daemon?.running
    : daemon?.external_daemon?.alive;
  const providerHealth = daemon?.provider_health ?? daemon?.external_daemon?.provider_health ?? {};
  const providerHealthEntries = Object.entries(providerHealth);
  const providersInBackoff = providerHealthEntries.filter(([, state]) => state.startsWith('backoff_until:')).length;
  const providerErrors = providerHealthEntries.filter(([, state]) => state.startsWith('error:')).length;
  const retrySummary = lanes?.adaptive_retry;
  const ext = daemon?.external_daemon;
  const voice = daemon?.voice_daemon;

  return (
    <div className="flex flex-col h-full bg-gray-900">
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-400" />
            <div>
              <h2 className="text-lg font-semibold text-white">HOP Autonomy</h2>
              <p className="text-xs text-gray-500">
                Silent background evolution, continuity, and operator guidance in one surface
              </p>
            </div>
          </div>
          <div className="flex items-center gap-4 flex-wrap">
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
                  ? 'Real-time task feed'
                  : connectionState.fallbackToPolling
                    ? 'Polling fallback'
                    : 'Disconnected'}
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

            <div className="flex items-center gap-2">
              <div
                className={cn(
                  'w-2 h-2 rounded-full',
                  daemonAlive ? 'bg-green-500 animate-pulse' : 'bg-red-500'
                )}
              />
              <span className="text-sm text-gray-300 capitalize">
                {runtimeLoading || runtimeRefreshing ? 'Refreshing runtime...' : `Daemon ${daemonState}`}
              </span>
            </div>

            <button
              onClick={() => void refreshRuntime()}
              disabled={runtimeLoading || runtimeRefreshing}
              className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-40"
            >
              <RefreshCw className={cn('w-3.5 h-3.5', (runtimeLoading || runtimeRefreshing) && 'animate-spin')} />
              Refresh
            </button>
          </div>
        </div>

        {(error || runtimeError || actionError) && (
          <div className="mt-3 px-3 py-2 bg-red-900/20 border border-red-700/50 rounded-lg">
            <p className="text-sm text-red-400">
              {error ? `Task status issue: ${error}` : null}
              {error && (runtimeError || actionError) ? ' | ' : null}
              {runtimeError ? `Runtime issue: ${runtimeError}` : null}
              {runtimeError && actionError ? ' | ' : null}
              {actionError ? `Action issue: ${actionError}` : null}
              {connectionState.fallbackToPolling && (
                <span className="text-yellow-400 ml-2">Using polling fallback.</span>
              )}
            </p>
          </div>
        )}
        {lastUpdatedAt ? (
          <p className="mt-3 text-xs text-gray-500">
            Runtime telemetry {formatRelativeTime(lastUpdatedAt)}
          </p>
        ) : null}
      </div>

      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        <div className="rounded-xl border border-indigo-900/40 bg-gradient-to-br from-indigo-950/40 via-gray-900 to-gray-900 px-5 py-4">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div>
              <p className="text-[11px] uppercase tracking-[0.24em] text-indigo-300/70">
                Primary Form
              </p>
              <h3 className="mt-1 text-white font-semibold">Silent Presence</h3>
              <p className="mt-2 max-w-3xl text-sm leading-relaxed text-gray-300">
                Kor&apos;tana is now optimized for continuous background awareness, self-directed improvement,
                and deliberate high-signal outputs. Voice remains archived as an experiment, not the center of the system.
              </p>
            </div>
            <div className="rounded-full border border-indigo-800/50 bg-indigo-950/40 px-3 py-1 text-xs text-indigo-200">
              presence over conversation
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Daemon Mode</p>
            <p className="text-xl font-bold text-white mt-1 capitalize">
              {daemon?.deployment_mode ?? 'unknown'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {daemon?.control_available ? 'local controls enabled' : 'worker-managed'}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Control Mode</p>
            <p className="text-xl font-bold text-white mt-1 capitalize">
              {daemon?.control_mode ?? ext?.control_mode ?? '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              github mode: {daemon?.github_mode ?? '—'}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Active Lane</p>
            <p className="text-xl font-bold text-white mt-1">
              {lanes?.active_lane ?? '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {retrySummary ? `${retrySummary.total_events} retry events` : 'shared routing telemetry'}
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Provider Backoff</p>
            <p className="text-xl font-bold text-yellow-300 mt-1">
              {providersInBackoff}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {providerErrors} provider errors tracked
            </p>
          </div>
          <div className="bg-gray-800 rounded-lg p-4">
            <p className="text-gray-400 text-sm">Last Cycle</p>
            <p className="text-xl font-bold text-white mt-1">
              {ext?.seconds_since_last_cycle !== undefined
                ? ext.seconds_since_last_cycle < 60
                  ? `${ext.seconds_since_last_cycle}s ago`
                  : `${Math.floor(ext.seconds_since_last_cycle / 60)}m ago`
                : status?.last_run
                  ? formatRelativeTime(status.last_run)
                  : '—'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              {ext?.last_cycle_id ? `cycle ${ext.last_cycle_id.replace('cycle_', '')}` : 'queue activity'}
            </p>
          </div>
        </div>

        {voice ? (
          <div className="bg-gray-800 rounded-lg p-6">
            <div className="flex items-center justify-between gap-4 flex-wrap">
              <div>
                <h3 className="text-white font-semibold mb-1 flex items-center gap-2">
                  <Mic className="w-5 h-5 text-cyan-300" />
                  Archived Voice Experiment
                </h3>
                <p className="text-gray-400 text-sm">
                  Voice is retained only as a dormant capability. The active product focus is continuity, memory, and autonomous evolution.
                </p>
              </div>
              <span className={cn('rounded-full border px-3 py-1 text-xs font-medium uppercase tracking-[0.2em]', voiceTone(voice.status))}>
                archived
              </span>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Continuity State</p>
                <p className="text-lg font-bold text-white mt-1">
                  {voice.temporal_state_present ? 'present' : 'missing'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {voice.last_diary_date ? `diary ${voice.last_diary_date}` : 'no diary snapshot'}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Archived Stack</p>
                <p className="text-lg font-bold text-white mt-1 capitalize">
                  {voice.model ?? 'unknown'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {[voice.device, voice.compute_type].filter(Boolean).join(' · ') || 'runtime unknown'}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Last Voice Touch</p>
                <p className="text-lg font-bold text-white mt-1">
                  {voice.last_voice_interaction_at ? formatRelativeTime(voice.last_voice_interaction_at) : '—'}
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {voice.last_absence_ack_at ? `ack ${formatRelativeTime(voice.last_absence_ack_at)}` : 'no absence ack'}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Artifacts</p>
                <p className="text-lg font-bold text-white mt-1">
                  {[voice.script_present, voice.binary_present, voice.model_present].filter(Boolean).length}/3
                </p>
                <p className="text-xs text-gray-500 mt-1">
                  {voice.last_log_at ? `last log ${formatRelativeTime(voice.last_log_at)}` : 'no runtime log'}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-2 mt-4">
              {voice.temporal_state_present ? (
                <span className="rounded-full border border-gray-700 bg-gray-900/70 px-3 py-1 text-[11px] text-gray-300">
                  temporal state present
                </span>
              ) : null}
              {voice.log_present ? (
                <span className="rounded-full border border-gray-700 bg-gray-900/70 px-3 py-1 text-[11px] text-gray-300">
                  voice log present
                </span>
              ) : null}
              {voice.last_diary_date ? (
                <span className="rounded-full border border-gray-700 bg-gray-900/70 px-3 py-1 text-[11px] text-gray-300">
                  diary {voice.last_diary_date}
                </span>
              ) : null}
              <span className="rounded-full border border-indigo-800/40 bg-indigo-950/30 px-3 py-1 text-[11px] text-indigo-200">
                not part of primary experience
              </span>
            </div>
          </div>
        ) : null}

        <div className="bg-gray-800 rounded-lg p-6">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <h3 className="text-white font-semibold mb-1">Daemon Control Panel</h3>
              <p className="text-gray-400 text-sm">
                {daemon?.message ?? 'Manage the autonomy daemon and trigger manual cycles.'}
              </p>
            </div>
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={triggerCycle}
                disabled={runningCycle}
                className="flex items-center gap-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-700 text-white rounded-lg px-5 py-3 transition-colors"
              >
                {runningCycle ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Running Cycle...
                  </>
                ) : (
                  <>
                    <Play className="w-5 h-5" />
                    Trigger Cycle
                  </>
                )}
              </button>
              {daemon?.control_available && (
                <>
                  <button
                    onClick={() => void toggleDaemon('start')}
                    disabled={daemonActionPending !== null || daemon?.running}
                    className="flex items-center gap-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-700 text-white rounded-lg px-5 py-3 transition-colors"
                  >
                    {daemonActionPending === 'start' ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Play className="w-5 h-5" />
                    )}
                    Start Daemon
                  </button>
                  <button
                    onClick={() => void toggleDaemon('stop')}
                    disabled={daemonActionPending !== null || !daemon?.running}
                    className="flex items-center gap-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-700 text-white rounded-lg px-5 py-3 transition-colors"
                  >
                    {daemonActionPending === 'stop' ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Pause className="w-5 h-5" />
                    )}
                    Stop Daemon
                  </button>
                </>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-5">
            <div className="bg-gray-900 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Safe Mode</p>
              <p className={cn('text-lg font-bold mt-1', metricTone(
                daemon?.safe_mode ?? ext?.safe_mode,
                'text-gray-300',
                'text-yellow-300',
                'text-green-400',
              ))}>
                {(daemon?.safe_mode ?? ext?.safe_mode) ? 'On' : 'Off'}
              </p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Live Execution</p>
              <p className={cn('text-lg font-bold mt-1', metricTone(
                daemon?.live_execution_enabled ?? ext?.live_execution_enabled,
                'text-gray-300',
                'text-green-400',
                'text-red-400',
              ))}>
                {(daemon?.live_execution_enabled ?? ext?.live_execution_enabled) ? 'Enabled' : 'Disabled'}
              </p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4">
              <p className="text-gray-400 text-sm">System State</p>
              <p className="text-lg font-bold text-white mt-1 capitalize">
                {ext?.system_state ?? '—'}
              </p>
            </div>
            <div className="bg-gray-900 rounded-lg p-4">
              <p className="text-gray-400 text-sm">Autonomy Index</p>
              <p className="text-lg font-bold text-white mt-1">
                {typeof ext?.autonomy_index === 'number' ? ext.autonomy_index.toFixed(2) : '—'}
              </p>
            </div>
          </div>

          {!daemon?.control_available && (
            <div className="mt-4 rounded-lg border border-blue-900/40 bg-blue-950/20 px-4 py-3 text-sm text-blue-200">
              This deployment uses a dedicated worker. Manual start/stop controls stay disabled here, but runtime health and cycle freshness are still tracked.
            </div>
          )}
        </div>

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

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Shield className="w-5 h-5" />
              Provider Health
            </h3>
            {providerHealthEntries.length === 0 ? (
              <p className="text-sm text-gray-500">No provider telemetry recorded yet.</p>
            ) : (
              <div className="space-y-3">
                {providerHealthEntries.map(([provider, state]) => (
                  <div key={provider} className="flex items-center justify-between gap-3 bg-gray-900 rounded-lg px-4 py-3">
                    <div>
                      <p className="text-sm font-medium text-white capitalize">{provider}</p>
                      <p className="text-xs text-gray-500 truncate">{state}</p>
                    </div>
                    <span className={cn('text-xs px-2 py-1 rounded', providerTone(state))}>
                      {state === 'ok'
                        ? 'ok'
                        : state.startsWith('backoff_until:')
                          ? 'backoff'
                          : state.startsWith('error:')
                            ? 'error'
                            : state}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="bg-gray-800 rounded-lg p-6">
            <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
              <Activity className="w-5 h-5" />
              Retry and Cost Telemetry
            </h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Retry Events</p>
                <p className="text-2xl font-bold text-white mt-1">
                  {retrySummary?.total_events ?? 0}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Scheduled Retries</p>
                <p className="text-2xl font-bold text-yellow-300 mt-1">
                  {retrySummary?.scheduled_retries ?? 0}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Skipped Retries</p>
                <p className="text-2xl font-bold text-red-400 mt-1">
                  {retrySummary?.skipped_retries ?? 0}
                </p>
              </div>
              <div className="bg-gray-900 rounded-lg p-4">
                <p className="text-gray-400 text-sm">Daily Spend</p>
                <p className="text-2xl font-bold text-green-400 mt-1">
                  {lanes?.cost_router?.cost?.totals?.daily_spend_usd !== undefined
                    ? `$${lanes.cost_router.cost.totals.daily_spend_usd.toFixed(4)}`
                    : '—'}
                </p>
              </div>
            </div>

            {retrySummary?.recent?.length ? (
              <div className="mt-4 space-y-2">
                {retrySummary.recent.slice(0, 4).map((event) => (
                  <div key={event.operation_id + event.timestamp + event.attempt} className="bg-gray-900 rounded-lg px-4 py-3">
                    <div className="flex items-center justify-between gap-3">
                      <p className="text-sm text-white">
                        {event.provider ?? 'provider'} · {event.error_category}
                      </p>
                      <span className="text-xs text-gray-500">
                        {new Date(event.timestamp).toLocaleTimeString()}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-1">
                      attempt {event.attempt + 1} · {event.will_retry ? `retrying in ${event.delay_seconds ?? 0}s` : 'no retry'}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 mt-4">No recent retry events recorded.</p>
            )}
          </div>
        </div>

        <div className="my-8">
          <ApprovalQueue />
        </div>

        <div className="bg-gray-800/50 rounded-lg p-6 border border-purple-900/30">
          <h3 className="text-purple-400 font-semibold mb-3">About HOP (Human Oversight Protocol)</h3>
          <p className="text-gray-300 text-sm leading-relaxed">
            The HOP autonomy system classifies tasks into three categories:
          </p>
          <ul className="mt-3 space-y-2 text-sm text-gray-400">
            <li className="flex items-start gap-2">
              <CheckCircle className="w-4 h-4 text-green-400 mt-0.5 shrink-0" />
              <span><strong className="text-white">Auto:</strong> Fully autonomous tasks that can execute without human intervention</span>
            </li>
            <li className="flex items-start gap-2">
              <AlertTriangle className="w-4 h-4 text-blue-400 mt-0.5 shrink-0" />
              <span><strong className="text-white">HO:</strong> Tasks requiring human oversight during execution</span>
            </li>
            <li className="flex items-start gap-2">
              <XCircle className="w-4 h-4 text-yellow-400 mt-0.5 shrink-0" />
              <span><strong className="text-white">Approval:</strong> Tasks requiring explicit human approval before execution</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}
