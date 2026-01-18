import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Globe, Key, Zap } from 'lucide-react';
import { api } from '../lib/api';
import type { HealthStatus } from '../types';

export default function Settings() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const fetchHealth = async () => {
    try {
      const data = await api.health();
      setHealth(data);
    } catch (error) {
      console.error('Failed to fetch health:', error);
    } finally {
      setLoading(false);
    }
  };

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
                {import.meta.env.VITE_API_URL || 'http://localhost:8000'}
              </p>
            </div>
            <div>
              <label className="text-gray-400 text-sm">Environment</label>
              <p className="text-white font-mono text-sm mt-1 bg-gray-900 rounded px-3 py-2">
                {import.meta.env.VITE_ENVIRONMENT || 'development'}
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
