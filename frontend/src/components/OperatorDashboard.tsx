import {
    Activity,
    AlertTriangle,
    CheckCircle,
    Clock,
    Cpu,
    Loader2,
    RefreshCw,
    Volume2,
    XCircle,
    Zap,
} from 'lucide-react';
import { useEffect, useState } from 'react';
import { useRuntimeTelemetry } from '../hooks/useRuntimeTelemetry';
import { api } from '../lib/api';
import { cn, formatRelativeTime } from '../lib/utils';
import type { DaemonCycle } from '../types';

type CycleTaskEvent = NonNullable<NonNullable<DaemonCycle['metrics']>['task_events']>[number];

// ─── sub-components ──────────────────────────────────────────────────────────

function StatusDot({ alive }: { alive: boolean | undefined }) {
    if (alive === undefined)
        return <span className="inline-block w-2.5 h-2.5 rounded-full bg-gray-600" />;
    return (
        <span
            className={cn(
                'inline-block w-2.5 h-2.5 rounded-full',
                alive ? 'bg-green-500 animate-pulse' : 'bg-red-500',
            )}
        />
    );
}

function MetricCard({
    icon: Icon,
    label,
    value,
    sub,
    accent,
}: {
    icon: React.ElementType;
    label: string;
    value: React.ReactNode;
    sub?: string;
    accent?: 'green' | 'yellow' | 'red' | 'blue' | 'purple';
}) {
    const accentClass: Record<string, string> = {
        green: 'border-green-700/60 bg-green-950/30',
        yellow: 'border-yellow-700/60 bg-yellow-950/30',
        red: 'border-red-700/60 bg-red-950/30',
        blue: 'border-indigo-700/60 bg-indigo-950/30',
        purple: 'border-purple-700/60 bg-purple-950/30',
    };
    return (
        <div
            className={cn(
                'rounded-xl border p-4 flex flex-col gap-1',
                accent ? accentClass[accent] : 'border-gray-800 bg-gray-900/60',
            )}
        >
            <div className="flex items-center gap-2 text-gray-400 text-xs font-medium uppercase tracking-wide">
                <Icon className="w-3.5 h-3.5" />
                {label}
            </div>
            <div className="text-2xl font-bold text-white">{value}</div>
            {sub && <div className="text-xs text-gray-500">{sub}</div>}
        </div>
    );
}

function CycleRow({ cycle, index }: { cycle: DaemonCycle; index: number }) {
    const hasErrors = cycle.errors_encountered > 0;
    const deferredCount = typeof cycle.metrics?.deferred === 'number' ? cycle.metrics.deferred : 0;
    const systemState = typeof cycle.metrics?.system_state === 'string' ? cycle.metrics.system_state : null;
    const duration =
        cycle.start_time && cycle.end_time
            ? ((new Date(cycle.end_time).getTime() - new Date(cycle.start_time).getTime()) / 1000).toFixed(1)
            : null;

    return (
        <tr
            className={cn(
                'border-t border-gray-800 text-sm',
                index === 0 ? 'bg-gray-800/20' : '',
            )}
        >
            <td className="py-2 px-3 text-gray-400 font-mono text-xs truncate max-w-[120px]">
                {cycle.cycle_id?.replace('cycle_', '') ?? '—'}
            </td>
            <td className="py-2 px-3 text-gray-300">
                {cycle.end_time
                    ? new Date(cycle.end_time).toLocaleTimeString()
                    : <span className="text-yellow-500">running</span>}
            </td>
            <td className="py-2 px-3 text-gray-300">{duration ? `${duration}s` : '—'}</td>
            <td className="py-2 px-3 text-gray-300">{cycle.tasks_processed}</td>
            <td className="py-2 px-3">
                {hasErrors ? (
                    <span className="text-red-400 font-medium">{cycle.errors_encountered}</span>
                ) : (
                    <span className="text-green-500">0</span>
                )}
            </td>
            <td className="py-2 px-3">
                {deferredCount > 0 ? (
                    <span className="text-yellow-300 font-medium">{deferredCount}</span>
                ) : (
                    <span className="text-gray-500">0</span>
                )}
            </td>
            <td className="py-2 px-3">
                {cycle.end_time ? (
                    hasErrors ? (
                        <span className="inline-flex items-center gap-1 text-yellow-400 text-xs">
                            <AlertTriangle className="w-3 h-3" /> degraded
                        </span>
                    ) : deferredCount > 0 || systemState === 'degraded' ? (
                        <span className="inline-flex items-center gap-1 text-yellow-300 text-xs">
                            <Clock className="w-3 h-3" /> guarded
                        </span>
                    ) : (
                        <span className="inline-flex items-center gap-1 text-green-400 text-xs">
                            <CheckCircle className="w-3 h-3" /> ok
                        </span>
                    )
                ) : (
                    <span className="inline-flex items-center gap-1 text-blue-400 text-xs">
                        <Loader2 className="w-3 h-3 animate-spin" /> active
                    </span>
                )}
            </td>
        </tr>
    );
}

function ProviderRow({
    name,
    p,
}: {
    name: string;
    p: {
        model: string;
        lane: string;
        is_free_tier: boolean;
        requests: number;
        cooling_down?: boolean;
        last_error?: string | null;
        last_used_at?: string | null;
    };
}) {
    return (
        <tr className="border-t border-gray-800 text-sm">
            <td className="py-2 px-3 text-gray-200 font-medium">{name}</td>
            <td className="py-2 px-3 text-gray-400 font-mono text-xs">{p.model}</td>
            <td className="py-2 px-3">
                <span
                    className={cn(
                        'text-xs px-1.5 py-0.5 rounded',
                        p.lane === 'free' ? 'bg-green-900/60 text-green-300' : 'bg-blue-900/60 text-blue-300',
                    )}
                >
                    {p.lane}
                </span>
            </td>
            <td className="py-2 px-3 text-gray-300">{p.requests}</td>
            <td className="py-2 px-3">
                {p.cooling_down ? (
                    <span className="text-yellow-400 text-xs">cooling down</span>
                ) : p.last_error ? (
                    <span className="text-red-400 text-xs truncate max-w-[120px] block" title={p.last_error}>
                        error
                    </span>
                ) : (
                    <span className="text-green-400 text-xs">ok</span>
                )}
            </td>
        </tr>
    );
}

function providerHealthTone(status: string | undefined) {
    if (!status || status === 'unknown') {
        return {
            label: status ?? 'unknown',
            className: 'bg-gray-800 text-gray-300',
        };
    }
    if (status === 'ok') {
        return {
            label: 'ok',
            className: 'bg-green-900/60 text-green-300',
        };
    }
    if (status.startsWith('backoff_until:')) {
        return {
            label: 'backoff',
            className: 'bg-yellow-900/60 text-yellow-300',
        };
    }
    return {
        label: 'error',
        className: 'bg-red-900/60 text-red-300',
    };
}

function ProviderHealthRow({ name, status }: { name: string; status: string }) {
    const tone = providerHealthTone(status);

    return (
        <tr className="border-t border-gray-800 text-sm">
            <td className="py-2 px-3 text-gray-200 font-medium">{name}</td>
            <td className="py-2 px-3">
                <span className={cn('text-xs px-1.5 py-0.5 rounded', tone.className)}>
                    {tone.label}
                </span>
            </td>
            <td className="py-2 px-3 text-gray-400 text-xs">
                {status === 'ok' ? 'ready' : status}
            </td>
        </tr>
    );
}

function voiceStatusTone(status: string | undefined) {
    switch (status) {
        case 'ready':
            return {
                label: 'ready',
                className: 'bg-green-900/60 text-green-300',
            };
        case 'degraded':
            return {
                label: 'degraded',
                className: 'bg-yellow-900/60 text-yellow-300',
            };
        case 'configured':
            return {
                label: 'configured',
                className: 'bg-blue-900/60 text-blue-300',
            };
        default:
            return {
                label: status ?? 'unknown',
                className: 'bg-gray-800 text-gray-300',
            };
    }
}

function formatEventReason(reason: unknown) {
    if (typeof reason !== 'string' || reason.trim() === '') {
        return 'unspecified';
    }
    return reason.replace(/_/g, ' ');
}

function SafeBlockRow({
    cycle,
    event,
}: {
    cycle: DaemonCycle;
    event: CycleTaskEvent;
}) {
    const title =
        typeof event.data?.title === 'string' && event.data.title.trim() !== ''
            ? event.data.title
            : typeof event.data?.task_id === 'string' && event.data.task_id.trim() !== ''
              ? event.data.task_id
              : 'Untitled task';
    const reason = formatEventReason(event.data?.reason ?? event.data?.status ?? event.data?.error);
    const cycleLabel = cycle.cycle_id?.replace('cycle_', '') ?? '—';
    const tone =
        event.type === 'task_blocked'
            ? 'bg-red-950/40 text-red-300 border-red-800/60'
            : 'bg-yellow-950/40 text-yellow-200 border-yellow-800/60';

    return (
        <tr className="border-t border-gray-800 text-sm">
            <td className="py-2 px-3 text-gray-300">
                {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : '—'}
            </td>
            <td className="py-2 px-3 text-gray-200 font-medium max-w-[280px] truncate" title={title}>
                {title}
            </td>
            <td className="py-2 px-3 text-gray-400 max-w-[280px] truncate" title={reason}>
                {reason}
            </td>
            <td className="py-2 px-3 text-gray-400 font-mono text-xs">{cycleLabel}</td>
            <td className="py-2 px-3">
                <span className={cn('text-[11px] px-2 py-0.5 rounded border', tone)}>
                    {event.type === 'task_blocked' ? 'blocked' : 'deferred'}
                </span>
            </td>
        </tr>
    );
}

// ─── main component ───────────────────────────────────────────────────────────

export default function OperatorDashboard() {
    const [cycles, setCycles] = useState<DaemonCycle[]>([]);
    const [loadingCycles, setLoadingCycles] = useState(true);
    const [cycleError, setCycleError] = useState<string | null>(null);
    const {
        daemon,
        lanes,
        errors,
        loading: runtimeLoading,
        refreshing: runtimeRefreshing,
        lastUpdatedAt,
        refresh,
    } = useRuntimeTelemetry();

    useEffect(() => {
        let cancelled = false;
        let timeoutId: number | null = null;

        const pollCycles = async () => {
            try {
                const nextCycles = await api.getDaemonCycles(15);
                if (cancelled) {
                    return;
                }
                setCycles(nextCycles);
                setCycleError(null);
            } catch (error) {
                if (!cancelled) {
                    setCycleError(
                        error instanceof Error ? error.message : 'Unable to load daemon cycles.'
                    );
                }
            } finally {
                if (!cancelled) {
                    setLoadingCycles(false);
                    timeoutId = window.setTimeout(() => {
                        void pollCycles();
                    }, 15000);
                }
            }
        };

        void pollCycles();
        return () => {
            cancelled = true;
            if (timeoutId !== null) {
                window.clearTimeout(timeoutId);
            }
        };
    }, []);

    const ext = daemon?.external_daemon;
    const alive = ext?.alive ?? (daemon?.deployment_mode === 'embedded' && daemon?.local_process?.running);
    const loading = runtimeLoading || loadingCycles;
    const notice = errors.daemon || errors.lanes || cycleError;

    // Aggregate cycle stats for header cards
    const totalCycles = cycles.length;
    const totalErrors = cycles.reduce((s, c) => s + c.errors_encountered, 0);
    const totalProcessed = cycles.reduce((s, c) => s + c.tasks_processed, 0);
    const totalDeferred = cycles.reduce(
        (s, c) => s + (typeof c.metrics?.deferred === 'number' ? c.metrics.deferred : 0),
        0,
    );
    const safeBlockEvents = cycles
        .flatMap((cycle) =>
            (cycle.metrics?.task_events ?? []).map((event) => ({
                cycle,
                event,
            })),
        )
        .filter(({ event }) => event.type === 'task_deferred' || event.type === 'task_blocked')
        .slice(0, 8);
    const latestCycleSecs = ext?.seconds_since_last_cycle;
    const providerHealth = daemon?.provider_health ?? ext?.provider_health ?? {};
    const providerHealthEntries = Object.entries(providerHealth);
    const providersInBackoff = providerHealthEntries.filter(([, status]) =>
        status.startsWith('backoff_until:'),
    ).length;
    const providerIssues = providerHealthEntries.filter(([, status]) =>
        status !== 'ok' && status !== 'unknown',
    ).length;

    // Model lane info
    const activeLane = lanes?.active_lane ?? '—';
    const totalGens = lanes?.runtime_usage?.total_generations ?? 0;
    const providers = lanes?.cost_router?.cost?.providers ?? {};
    const retrySummary = lanes?.adaptive_retry;
    const voice = daemon?.voice_daemon;
    const voiceTone = voiceStatusTone(voice?.status);

    return (
        <div className="flex flex-col h-full bg-gray-950 overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-gray-950/95 backdrop-blur px-6 py-4 border-b border-gray-800 flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-indigo-400" />
                    <h2 className="text-lg font-semibold text-white">Operator Dashboard</h2>
                    <div className="flex items-center gap-1.5 ml-2">
                        <StatusDot alive={alive} />
                        <span className={cn('text-xs font-medium', alive ? 'text-green-400' : 'text-red-400')}>
                            {loading ? 'loading…' : alive ? 'daemon alive' : 'daemon offline'}
                        </span>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    <span className="text-xs text-gray-500">
                        {lastUpdatedAt ? `runtime ${formatRelativeTime(lastUpdatedAt)}` : 'refreshing…'}
                    </span>
                    <button
                        onClick={() => {
                            setLoadingCycles(true);
                            void Promise.all([
                                refresh({ force: true, resources: ['daemon', 'lanes'] }),
                                api.getDaemonCycles(15).then((nextCycles) => {
                                    setCycles(nextCycles);
                                    setCycleError(null);
                                }).catch((error) => {
                                    setCycleError(
                                        error instanceof Error ? error.message : 'Unable to refresh daemon cycles.'
                                    );
                                }).finally(() => {
                                    setLoadingCycles(false);
                                }),
                            ]);
                        }}
                        disabled={loading}
                        className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-white transition-colors disabled:opacity-40"
                    >
                        <RefreshCw className={cn('w-3.5 h-3.5', (loading || runtimeRefreshing) && 'animate-spin')} />
                        Refresh
                    </button>
                </div>
            </div>

            <div className="flex-1 px-6 py-5 space-y-6">
                {notice ? (
                    <div className="rounded-xl border border-amber-800/70 bg-amber-950/40 px-4 py-3 text-sm text-amber-100">
                        {notice}
                    </div>
                ) : null}
                {/* ── Daemon Health Cards ── */}
                <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                        Daemon Health
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                        <MetricCard
                            icon={alive ? CheckCircle : XCircle}
                            label="Status"
                            value={alive ? 'Alive' : 'Offline'}
                            sub={daemon?.deployment_mode === 'external' ? 'external worker' : 'embedded'}
                            accent={alive ? 'green' : 'red'}
                        />
                        <MetricCard
                            icon={Clock}
                            label="Last Cycle"
                            value={
                                latestCycleSecs !== undefined
                                    ? latestCycleSecs < 60
                                        ? `${latestCycleSecs}s ago`
                                        : `${Math.floor(latestCycleSecs / 60)}m ago`
                                    : '—'
                            }
                            sub={ext?.last_cycle_id ? `id ${ext.last_cycle_id.replace('cycle_', '')}` : undefined}
                            accent={
                                latestCycleSecs === undefined ? undefined
                                    : latestCycleSecs < 120 ? 'green'
                                        : latestCycleSecs < 300 ? 'yellow'
                                            : 'red'
                            }
                        />
                        <MetricCard
                            icon={Activity}
                            label="Tasks / 15 cycles"
                            value={totalProcessed}
                            sub={`${totalCycles} cycles shown`}
                            accent="blue"
                        />
                        <MetricCard
                            icon={AlertTriangle}
                            label="Errors / 15 cycles"
                            value={totalErrors}
                            sub={totalErrors === 0 ? 'clean run' : 'check cycle log'}
                            accent={totalErrors === 0 ? 'green' : 'yellow'}
                        />
                        <MetricCard
                            icon={Clock}
                            label="Safe Blocks / 15 cycles"
                            value={totalDeferred}
                            sub={totalDeferred === 0 ? 'no guardrail holds' : 'guardrail deferrals'}
                            accent={totalDeferred === 0 ? 'blue' : 'yellow'}
                        />
                    </div>
                </section>

                <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                        Autonomy Providers
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        <MetricCard
                            icon={Activity}
                            label="Providers Seen"
                            value={providerHealthEntries.length || '—'}
                            sub="daemon health snapshot"
                            accent="blue"
                        />
                        <MetricCard
                            icon={AlertTriangle}
                            label="Cooling Down"
                            value={providersInBackoff}
                            sub={providersInBackoff === 0 ? 'no active backoff' : 'provider backoff active'}
                            accent={providersInBackoff === 0 ? 'green' : 'yellow'}
                        />
                        <MetricCard
                            icon={RefreshCw}
                            label="Retry Events"
                            value={retrySummary?.total_events ?? 0}
                            sub={
                                retrySummary
                                    ? `${retrySummary.scheduled_retries} scheduled / ${retrySummary.skipped_retries} skipped`
                                    : 'shared retry engine'
                            }
                            accent="purple"
                        />
                        <MetricCard
                            icon={XCircle}
                            label="Provider Issues"
                            value={providerIssues}
                            sub={providerIssues === 0 ? 'healthy' : 'needs attention'}
                            accent={providerIssues === 0 ? 'green' : 'red'}
                        />
                    </div>

                    {providerHealthEntries.length > 0 && (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 overflow-x-auto">
                            <table className="w-full min-w-[520px]">
                                <thead>
                                    <tr className="text-xs text-gray-500 uppercase tracking-wide">
                                        <th className="text-left py-2 px-3">Provider</th>
                                        <th className="text-left py-2 px-3">State</th>
                                        <th className="text-left py-2 px-3">Detail</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {providerHealthEntries.map(([name, status]) => (
                                        <ProviderHealthRow key={name} name={name} status={status} />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>

                {voice ? (
                    <section>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                            Voice Runtime
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                            <MetricCard
                                icon={Volume2}
                                label="Voice Status"
                                value={voiceTone.label}
                                sub={voice.message}
                                accent={
                                    voice.status === 'ready'
                                        ? 'green'
                                        : voice.status === 'degraded'
                                            ? 'yellow'
                                            : 'blue'
                                }
                            />
                            <MetricCard
                                icon={Clock}
                                label="Last Heard"
                                value={voice.last_voice_interaction_at ? formatRelativeTime(voice.last_voice_interaction_at) : '—'}
                                sub={voice.last_log_at ? `log ${formatRelativeTime(voice.last_log_at)}` : 'no voice log'}
                                accent="blue"
                            />
                            <MetricCard
                                icon={Cpu}
                                label="STT Runtime"
                                value={voice.model ?? 'unknown'}
                                sub={[voice.device, voice.compute_type].filter(Boolean).join(' · ') || 'runtime unknown'}
                                accent="purple"
                            />
                            <MetricCard
                                icon={Activity}
                                label="Artifacts"
                                value={`${[voice.script_present, voice.binary_present, voice.model_present].filter(Boolean).length}/3`}
                                sub={voice.binary_present ? 'tts ready' : 'tts incomplete'}
                                accent={voice.binary_present && voice.model_present ? 'green' : 'yellow'}
                            />
                        </div>
                    </section>
                ) : null}

                {/* ── Model Lane ── */}
                <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                        AI Model / Lane
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                        <MetricCard
                            icon={Zap}
                            label="Active Lane"
                            value={activeLane}
                            sub="cost router selection"
                            accent="purple"
                        />
                        <MetricCard
                            icon={Cpu}
                            label="Runtime Generations"
                            value={totalGens.toLocaleString()}
                            sub="since last restart"
                            accent="blue"
                        />
                        <MetricCard
                            icon={Activity}
                            label="Daily Spend"
                            value={lanes?.cost_router?.cost?.totals?.daily_spend_usd !== undefined
                                ? `$${lanes.cost_router.cost.totals.daily_spend_usd.toFixed(4)}`
                                : '—'}
                            sub="estimated"
                            accent="green"
                        />
                        <MetricCard
                            icon={Clock}
                            label="Last Retry"
                            value={
                                retrySummary?.last_recorded_at
                                    ? new Date(retrySummary.last_recorded_at).toLocaleTimeString()
                                    : '—'
                            }
                            sub="shared retry telemetry"
                            accent="yellow"
                        />
                    </div>

                    {Object.keys(providers).length > 0 && (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 overflow-x-auto">
                            <table className="w-full min-w-[640px]">
                                <thead>
                                    <tr className="text-xs text-gray-500 uppercase tracking-wide">
                                        <th className="text-left py-2 px-3">Provider</th>
                                        <th className="text-left py-2 px-3">Model</th>
                                        <th className="text-left py-2 px-3">Lane</th>
                                        <th className="text-left py-2 px-3">Requests</th>
                                        <th className="text-left py-2 px-3">State</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {Object.entries(providers).map(([name, p]) => (
                                        <ProviderRow key={name} name={name} p={p} />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>

                {/* ── Cycle History ── */}
                <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                        Cycle History (last {cycles.length})
                    </h3>
                    {cycles.length === 0 ? (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 px-4 py-8 text-center text-gray-500 text-sm">
                            {loading ? (
                                <Loader2 className="w-5 h-5 animate-spin mx-auto" />
                            ) : (
                                'No cycles recorded yet'
                            )}
                        </div>
                    ) : (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 overflow-x-auto">
                            <table className="w-full min-w-[760px]">
                                <thead>
                                    <tr className="text-xs text-gray-500 uppercase tracking-wide">
                                        <th className="text-left py-2 px-3">Cycle ID</th>
                                        <th className="text-left py-2 px-3">Completed</th>
                                        <th className="text-left py-2 px-3">Duration</th>
                                        <th className="text-left py-2 px-3">Tasks</th>
                                        <th className="text-left py-2 px-3">Errors</th>
                                        <th className="text-left py-2 px-3">Deferred</th>
                                        <th className="text-left py-2 px-3">State</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {cycles.map((cycle, i) => (
                                        <CycleRow key={cycle.cycle_id} cycle={cycle} index={i} />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>

                <section>
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-3">
                        Recent Safe Blocks
                    </h3>
                    {safeBlockEvents.length === 0 ? (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 px-4 py-6 text-sm text-gray-500">
                            No recent guardrail deferrals or blocks recorded in the last {cycles.length} cycles.
                        </div>
                    ) : (
                        <div className="rounded-xl border border-gray-800 bg-gray-900/40 overflow-x-auto">
                            <table className="w-full min-w-[720px]">
                                <thead>
                                    <tr className="text-xs text-gray-500 uppercase tracking-wide">
                                        <th className="text-left py-2 px-3">When</th>
                                        <th className="text-left py-2 px-3">Task</th>
                                        <th className="text-left py-2 px-3">Reason</th>
                                        <th className="text-left py-2 px-3">Cycle</th>
                                        <th className="text-left py-2 px-3">Type</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {safeBlockEvents.map(({ cycle, event }, index) => (
                                        <SafeBlockRow
                                            key={`${cycle.cycle_id}-${event.timestamp}-${index}`}
                                            cycle={cycle}
                                            event={event}
                                        />
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </section>

                {/* ── Raw Daemon Message ── */}
                {ext?.message && (
                    <section>
                        <h3 className="text-xs font-semibold uppercase tracking-wider text-gray-500 mb-2">
                            Daemon Message
                        </h3>
                        <div className="rounded-lg border border-gray-800 bg-gray-900/40 px-4 py-3 text-sm text-gray-400">
                            {ext.message}
                            {ext.last_cycle_completed_at && (
                                <span className="ml-3 text-gray-600">
                                    last cycle: {new Date(ext.last_cycle_completed_at).toLocaleString()}
                                </span>
                            )}
                        </div>
                    </section>
                )}
            </div>
        </div>
    );
}
