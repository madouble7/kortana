import { Globe, Key, Settings as SettingsIcon, Zap } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { getDisplayApiBaseUrl, getRuntimeEnvironment } from '../lib/runtimeConfig';
import type { HealthStatus, ModelLaneSummary } from '../types';

export default function Settings() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [modelLaneSummary, setModelLaneSummary] = useState<ModelLaneSummary | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const [healthData, laneData] = await Promise.all([
        api.health(),
        api.getModelLaneSummary().catch(() => null),
      ]);
      setHealth(healthData);
      setModelLaneSummary(laneData);
    } catch (error) {
      console.error('Failed to fetch health:', error);
      setHealth(null);
      setModelLaneSummary(null);
    } finally {
      setLoading(false);
    }
  };

  const persistedUsage = modelLaneSummary?.runtime_usage.persisted;
  const inMemoryUsage = modelLaneSummary?.runtime_usage.memory;
  const costSummary = modelLaneSummary?.cost_router.cost;
  const providerEntries = Object.entries(costSummary?.providers || {}).sort(
    (left, right) => right[1].requests - left[1].requests
  );
  const providerUsageEntries = Object.entries(persistedUsage?.by_provider || {}).sort(
    (left, right) => right[1] - left[1]
  );

  const getStatusColor = (status?: string) => {
    switch (status?.toLowerCase()) {
      case 'alive':
      case 'connected':
      case 'configured':
        return 'text-green-400';
      case 'degraded':
        return 'text-yellow-400';
      default:
        return 'text-red-400';
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900 overflow-y-auto">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800 sticky top-0 bg-gray-900 z-10">
        <div className="flex items-center gap-2">
          <SettingsIcon className="w-5 h-5 text-gray-400" />
          <h2 className="text-lg font-semibold text-white">Settings</h2>
        </div>
      </div>

      <div className="px-6 py-6 space-y-6">
        {/* System Status */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            System Status
          </h3>
          {loading ? (
            <p className="text-gray-400">Loading...</p>
          ) : health ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Backend</span>
                <span className={getStatusColor(health.status)}>
                  {health.status}
                </span>
              </div>
              {health.database && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Database</span>
                  <span className={getStatusColor(health.database)}>
                    {health.database}
                  </span>
                </div>
              )}
              {health.redis && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Redis</span>
                  <span className={getStatusColor(health.redis)}>
                    {health.redis}
                  </span>
                </div>
              )}
              {health.gemini && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Gemini API</span>
                  <span className={getStatusColor(health.gemini)}>
                    {health.gemini}
                  </span>
                </div>
              )}
              {health.version && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Version</span>
                  <span className="text-gray-300">{health.version}</span>
                </div>
              )}
              {health.environment && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Environment</span>
                  <span className="text-gray-300">{health.environment}</span>
                </div>
              )}
              {health.uptime_seconds !== undefined && (
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Uptime</span>
                  <span className="text-gray-300">
                    {Math.floor(health.uptime_seconds / 3600)}h{' '}
                    {Math.floor((health.uptime_seconds % 3600) / 60)}m
                  </span>
                </div>
              )}
            </div>
          ) : (
            <p className="text-red-400">Failed to connect to backend</p>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Model Routing
          </h3>
          {modelLaneSummary ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Active Lane</span>
                <span className="text-indigo-300">{modelLaneSummary.active_lane}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Persisted Generations</span>
                <span className="text-gray-300">{persistedUsage?.total_generations || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Persisted Tokens</span>
                <span className="text-gray-300">{persistedUsage?.total_tokens_used || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">In-Memory Generations</span>
                <span className="text-gray-300">{inMemoryUsage?.total_generations || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">In-Memory Tokens</span>
                <span className="text-gray-300">{inMemoryUsage?.total_tokens_used || 0}</span>
              </div>
              {providerUsageEntries.length ? (
                <div className="pt-3 border-t border-gray-700">
                  <p className="text-xs uppercase tracking-[0.18em] text-gray-500 mb-2">
                    Top Providers
                  </p>
                  <div className="space-y-2">
                    {providerUsageEntries.slice(0, 3).map(([provider, count]) => (
                      <div key={provider} className="flex items-center justify-between text-sm">
                        <span className="text-gray-300">{provider}</span>
                        <span className="text-gray-400">
                          {count} calls · {persistedUsage?.by_provider_tokens?.[provider] || 0} tokens
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  No persisted model usage has been recorded yet.
                </p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              Model routing summary unavailable.
            </p>
          )}
        </div>

        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            Cost & Provider Activity
          </h3>
          {costSummary ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Daily Spend</span>
                <span className="text-gray-300">{costSummary.total_daily_spend}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Monthly Spend</span>
                <span className="text-gray-300">{costSummary.total_monthly_spend}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Tracked Requests</span>
                <span className="text-gray-300">{costSummary.totals.requests}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-400">Tracked Tokens</span>
                <span className="text-gray-300">{costSummary.totals.total_tokens}</span>
              </div>
              {providerEntries.length ? (
                <div className="pt-3 border-t border-gray-700 space-y-2">
                  {providerEntries.slice(0, 4).map(([provider, details]) => (
                    <div key={provider} className="rounded-lg bg-gray-900 px-3 py-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-white">{provider}</span>
                        <span className="text-xs text-gray-500">
                          {details.is_free_tier ? 'free tier' : details.lane}
                        </span>
                      </div>
                      <p className="text-xs text-gray-400 mt-1">
                        {details.model} · {details.requests} requests · {details.total_tokens} tokens
                      </p>
                      {details.last_task_type || details.last_used_at ? (
                        <p className="text-[11px] text-gray-500 mt-1">
                          {[details.last_task_type, details.last_used_at].filter(Boolean).join(' · ')}
                        </p>
                      ) : null}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-gray-500">
                  No provider usage has been recorded yet.
                </p>
              )}
            </div>
          ) : (
            <p className="text-gray-500 text-sm">
              Cost report unavailable.
            </p>
          )}
        </div>

        {/* API Configuration */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Globe className="w-5 h-5" />
            API Configuration
          </h3>
          <div className="space-y-3">
            <div>
              <label className="text-gray-400 text-sm">Backend URL</label>
              <p className="text-white font-mono text-sm mt-1 bg-gray-900 rounded px-3 py-2">
                {getDisplayApiBaseUrl()}
              </p>
            </div>
            <div>
              <label className="text-gray-400 text-sm">Environment</label>
              <p className="text-white font-mono text-sm mt-1 bg-gray-900 rounded px-3 py-2">
                {getRuntimeEnvironment()}
              </p>
            </div>
          </div>
        </div>

        {/* Feature Flags */}
        <div className="bg-gray-800 rounded-lg p-6">
          <h3 className="text-white font-semibold mb-4 flex items-center gap-2">
            <Key className="w-5 h-5" />
            Feature Flags
          </h3>
          <div className="space-y-2">
            {[
              { key: 'VITE_ENABLE_CHAT', label: 'Chat' },
              { key: 'VITE_ENABLE_TASKS', label: 'Tasks' },
              { key: 'VITE_ENABLE_AUTONOMY', label: 'Autonomy' },
              { key: 'VITE_ENABLE_GITHUB', label: 'GitHub' },
              { key: 'VITE_ENABLE_MEMORY', label: 'Memory' },
            ].map(({ key, label }) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-gray-400">{label}</span>
                <span
                  className={
                    import.meta.env[key] === 'true'
                      ? 'text-green-400'
                      : 'text-gray-500'
                  }
                >
                  {import.meta.env[key] === 'true' ? 'Enabled' : 'Disabled'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* About */}
        <div className="bg-gray-800/50 rounded-lg p-6 border border-indigo-900/30">
          <h3 className="text-indigo-400 font-semibold mb-3">About Kor'tana</h3>
          <p className="text-gray-300 text-sm leading-relaxed">
            Kor'tana is an autonomous AI constellation system with multimodal capabilities,
            task orchestration, and human oversight protocols.
          </p>
          <div className="mt-4 pt-4 border-t border-gray-700">
            <p className="text-xs text-gray-500">
              Version: {import.meta.env.VITE_APP_VERSION || '1.0.0'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              Environment: {import.meta.env.VITE_ENVIRONMENT || 'development'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
