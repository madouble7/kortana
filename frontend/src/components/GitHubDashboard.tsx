import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { formatRelativeTime } from '../lib/utils';
import type { AlwaysOnMetricsResponse, IssueQueueResponse } from '../types';

const STATUS_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  pending: { bg: 'bg-gray-700', text: 'text-gray-300', label: 'Pending' },
  analyzing: { bg: 'bg-yellow-900/50', text: 'text-yellow-300', label: 'Analyzing' },
  analyzed: { bg: 'bg-blue-900/50', text: 'text-blue-300', label: 'Analyzed' },
  planning: { bg: 'bg-indigo-900/50', text: 'text-indigo-300', label: 'Planning' },
  planning_complete: { bg: 'bg-purple-900/50', text: 'text-purple-300', label: 'Planned' },
  executing: { bg: 'bg-orange-900/50', text: 'text-orange-300', label: 'Executing' },
  executed: { bg: 'bg-green-900/50', text: 'text-green-300', label: 'Executed' },
  completed: { bg: 'bg-green-900/60', text: 'text-green-400', label: 'Done' },
  failed: { bg: 'bg-red-900/50', text: 'text-red-400', label: 'Failed' },
};

function StatusChip({ status }: { status: string }) {
  const s = STATUS_STYLE[status] ?? { bg: 'bg-gray-700', text: 'text-gray-400', label: status };
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${s.bg} ${s.text}`}>
      {s.label}
    </span>
  );
}

const PIPELINE_ORDER = ['pending', 'analyzing', 'analyzed', 'planning', 'planning_complete', 'executing', 'executed', 'completed', 'failed'];

export default function GitHubDashboard() {
  const [data, setData] = useState<IssueQueueResponse | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [providerHealth, setProviderHealth] = useState<Record<string, string>>({});
  const [hideLocal, setHideLocal] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [lastUpdatedAt, setLastUpdatedAt] = useState<string | null>(null);

  const fetchDashboard = async () => {
    try {
      const [queue, metrics] = await Promise.all([
        api.getAlwaysOnIssueQueue({ limit: 100, hideLocal }),
        api.getAlwaysOnMetrics(),
      ]);
      setData(queue);
      setProviderHealth((metrics as AlwaysOnMetricsResponse).provider_health ?? {});
      setNotice(null);
      setLastUpdatedAt(new Date().toISOString());
    } catch (error) {
      setNotice(error instanceof Error ? error.message : 'Failed to refresh GitHub pipeline.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchDashboard();
    const id = setInterval(() => {
      void fetchDashboard();
    }, 8000);
    return () => clearInterval(id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hideLocal]);

  const tasks = data?.tasks ?? [];
  const visible = filter === 'all' ? tasks : tasks.filter(t => t.status === filter);
  const realIssues = tasks.filter(t => !t.is_local);
  const inFlight = tasks.filter(t => ['analyzing', 'analyzed', 'planning', 'planning_complete', 'executing'].includes(t.status));

  return (
    <div className="flex flex-col h-full bg-gray-900 overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/90 sticky top-0 backdrop-blur-sm z-10">
        <div className="flex items-center gap-3">
          <span className="text-2xl">🔗</span>
          <div>
            <h2 className="text-lg font-semibold text-green-400">Silent Evolution Pipeline</h2>
            <p className="text-xs text-gray-500">self-directed background work flowing through GitHub</p>
          </div>
        </div>
        <div className="flex items-center gap-4 text-xs text-gray-500">
          {lastUpdatedAt ? <span>updated {formatRelativeTime(lastUpdatedAt)}</span> : null}
          <span className="text-green-400 font-bold">{realIssues.length}</span> real issues
          <span className="text-orange-400 font-bold">{inFlight.length}</span> in-flight
          <button
            onClick={() => setHideLocal(h => !h)}
            className={`flex items-center gap-1.5 px-2 py-1 rounded-md border transition-colors ${hideLocal
              ? 'border-gray-700 text-gray-500 hover:text-gray-300'
              : 'border-purple-700/50 bg-purple-900/20 text-purple-400'
              }`}
            title={hideLocal ? 'Local tasks hidden — click to show' : 'Showing local tasks — click to hide'}
          >
            {hideLocal ? 'local: hidden' : 'local: visible'}
          </button>
          <button
            onClick={() => void fetchDashboard()}
            className="rounded-md border border-gray-700 px-2 py-1 text-gray-400 transition-colors hover:text-gray-200"
          >
            refresh
          </button>
          <div className="flex items-center gap-1">
            <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div> Live
          </div>
        </div>
      </div>

      <div className="p-6 space-y-6 max-w-6xl mx-auto w-full">
        {notice ? (
          <div className="rounded-xl border border-amber-800/70 bg-amber-950/40 px-4 py-3 text-sm text-amber-100">
            {notice}
          </div>
        ) : null}
        {/* Pipeline bar */}
        <section>
          <div className="flex items-center gap-2 mb-3 border-b border-gray-800 pb-2">
            <span className="w-1.5 h-4 bg-green-500 rounded"></span>
            <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">Pipeline Status</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {PIPELINE_ORDER.map(s => {
              const count = data?.status_counts?.[s] ?? 0;
              if (count === 0) return null;
              const style = STATUS_STYLE[s] ?? { bg: 'bg-gray-700', text: 'text-gray-400', label: s };
              return (
                <button
                  key={s}
                  onClick={() => setFilter(f => f === s ? 'all' : s)}
                  className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${filter === s
                    ? `${style.bg} border-current ${style.text}`
                    : 'bg-gray-800 border-gray-700 text-gray-400 hover:border-gray-600'
                    }`}
                >
                  <span className={filter === s ? style.text : 'text-gray-500'}>{style.label}</span>
                  <span className={`font-bold ${filter === s ? style.text : 'text-gray-300'}`}>{count}</span>
                </button>
              );
            })}
            {filter !== 'all' && (
              <button
                onClick={() => setFilter('all')}
                className="px-3 py-1.5 rounded-lg border border-dashed border-gray-600 text-xs text-gray-500 hover:text-gray-300 transition-colors"
              >
                clear filter
              </button>
            )}
          </div>
        </section>

        {/* Provider health strip */}
        {Object.keys(providerHealth).length > 0 && (
          <section>
            <div className="flex items-center gap-2 mb-3 border-b border-gray-800 pb-2">
              <span className="w-1.5 h-4 bg-purple-500 rounded"></span>
              <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">AI Providers</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {Object.entries(providerHealth).map(([provider, status]) => {
                const isOk = status === 'ok';
                const isUnknown = status === 'unknown';
                return (
                  <div
                    key={provider}
                    className={`flex items-center gap-2 px-3 py-1.5 rounded-lg border text-xs font-medium ${isOk
                      ? 'bg-green-900/20 border-green-700/50 text-green-400'
                      : isUnknown
                        ? 'bg-gray-800 border-gray-700 text-gray-500'
                        : 'bg-red-900/20 border-red-700/50 text-red-400'
                      }`}
                  >
                    <span className={`w-1.5 h-1.5 rounded-full ${isOk ? 'bg-green-500' : isUnknown ? 'bg-gray-500' : 'bg-red-500'
                      }`}></span>
                    <span className="capitalize">{provider}</span>
                    {!isOk && !isUnknown && (
                      <span className="text-[9px] text-red-400 font-mono">backoff</span>
                    )}
                  </div>
                );
              })}
            </div>
          </section>
        )}

        {/* Token warning if we have no real issues */}
        {!loading && realIssues.length === 0 && (
          <div className="bg-yellow-900/20 border border-yellow-700/50 rounded-xl p-4 text-sm">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-yellow-400 font-semibold">⚠ GitHub Token Required</span>
            </div>
            <p className="text-gray-400 text-xs leading-relaxed">
              No real GitHub issues are queued. The pipeline is running in local evolution mode.<br />
              To deepen autonomous background work, a valid GitHub PAT is required.<br />
              <span className="text-yellow-300">HO task →</span> generate a new PAT at{' '}
              <a href="https://github.com/settings/tokens" target="_blank" rel="noreferrer" className="text-blue-400 underline">github.com/settings/tokens</a>
              {' '}with <code className="bg-gray-800 px-1 rounded">repo</code>, <code className="bg-gray-800 px-1 rounded">issues</code>, <code className="bg-gray-800 px-1 rounded">pull_requests</code> permissions, update <code className="bg-gray-800 px-1 rounded">.env GITHUB_TOKEN</code>, then restart the backend.
            </p>
          </div>
        )}

        {/* Task table */}
        <section>
          <div className="flex items-center gap-2 mb-3 border-b border-gray-800 pb-2">
            <span className="w-1.5 h-4 bg-blue-500 rounded"></span>
            <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">
              {filter === 'all' ? 'All Tasks' : `${STATUS_STYLE[filter]?.label ?? filter} Tasks`}
              <span className="ml-2 text-gray-500 font-normal normal-case">({visible.length})</span>
            </h3>
          </div>
          {loading ? (
            <div className="text-gray-500 text-sm text-center py-8">Synchronizing with pipeline...</div>
          ) : visible.length === 0 ? (
            <div className="bg-gray-800/50 p-6 rounded-lg text-center text-gray-500 text-sm">No tasks in this state.</div>
          ) : (
            <div className="space-y-2">
              {visible.map(task => (
                <div
                  key={task.id}
                  className={`bg-gray-800/80 border rounded-lg p-3 flex flex-col gap-1.5 ${task.status === 'failed' ? 'border-red-900/50' :
                    task.status === 'executing' ? 'border-orange-900/50' :
                      ['executed', 'completed'].includes(task.status) ? 'border-green-900/30' :
                        'border-gray-700'
                    }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <StatusChip status={task.status} />
                        {task.is_local ? (
                          <span className="text-[9px] px-1.5 py-0.5 bg-gray-700 text-gray-400 rounded uppercase">local</span>
                        ) : (
                          <span className="text-[9px] px-1.5 py-0.5 bg-blue-900/40 text-blue-400 rounded font-mono">
                            #{task.issue_number}
                          </span>
                        )}
                        <span className="text-[10px] text-gray-500">{task.repo}</span>
                      </div>
                      <p className="text-sm text-gray-200 truncate" title={task.title}>{task.title}</p>
                    </div>
                    <div className="text-right text-[10px] text-gray-500 shrink-0">
                      {task.updated_at && new Date(task.updated_at).toLocaleTimeString()}
                    </div>
                  </div>
                  {(task.branch || task.pr_number) && (
                    <div className="flex items-center gap-3 text-[10px] text-gray-500">
                      {task.branch && <span className="font-mono text-gray-400">{task.branch}</span>}
                      {task.pr_number && (
                        <a
                          href={`https://github.com/${task.repo}/pull/${task.pr_number}`}
                          target="_blank"
                          rel="noreferrer"
                          className="text-blue-400 hover:underline"
                        >
                          PR #{task.pr_number}
                        </a>
                      )}
                    </div>
                  )}
                  {task.error && (
                    <div className="text-[10px] bg-red-900/10 border border-red-900/30 px-2 py-1 rounded text-red-400 font-mono truncate" title={task.error}>
                      {task.error}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
