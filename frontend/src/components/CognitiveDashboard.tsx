import { useEffect, useState } from "react";
import { api } from "../lib/api";
import type { DaemonCycle, DaemonStatus } from "../types";

interface IdentityDimension {
  [key: string]: number;
}

interface IdentityData {
  evolution: {
    dimensions: IdentityDimension;
    interactions_tracked: number;
    checkpoints: number;
  };
  narrative: string;
}

interface DreamThought {
  dream_type: string;
  content: string;
  timestamp?: string;
}

interface ModelProviderStatus {
  provider: string;
  model: string;
  status: string;
  priority: number;
  is_free: boolean;
}

export default function CognitiveDashboard() {
  const [identity, setIdentity] = useState<IdentityData | null>(null);
  const [dreams, setDreams] = useState<DreamThought[]>([]);
  const [daemon, setDaemon] = useState<DaemonStatus | null>(null);
  const [providers, setProviders] = useState<ModelProviderStatus[]>([]);
  const [cycles, setCycles] = useState<DaemonCycle[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAll = async () => {
    try {
      const [identityRes, dreamsRes, daemonRes, healthRes, cyclesRes] =
        await Promise.allSettled([
          api.getIdentityEvolution(),
          api.getVoiceDreams(),
          api.getDaemonStatus(),
          api.health(),
          api.getDaemonCycles(10),
        ]);

      if (identityRes.status === "fulfilled")
        setIdentity(identityRes.value as IdentityData);
      if (dreamsRes.status === "fulfilled") {
        const d = dreamsRes.value as { dreams: DreamThought[] };
        setDreams(d.dreams || []);
      }
      if (daemonRes.status === "fulfilled")
        setDaemon(daemonRes.value as DaemonStatus);
      if (cyclesRes.status === "fulfilled")
        setCycles(cyclesRes.value as DaemonCycle[]);
      if (healthRes.status === "fulfilled") {
        const h = healthRes.value as {
          model_providers?: ModelProviderStatus[];
        };
        setProviders(h.model_providers || []);
      }
      setError(null);
    } catch (e) {
      setError(String(e));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAll();
    const interval = setInterval(fetchAll, 15000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-gray-400">
        <div className="animate-pulse">loading cognitive state...</div>
      </div>
    );
  }

  const dimensions = identity?.evolution?.dimensions || {};
  const dimensionEntries = Object.entries(dimensions).sort(
    ([, a], [, b]) => b - a,
  );

  return (
    <div className="p-6 space-y-6 overflow-y-auto h-full">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          cognitive dashboard
        </h1>
        <button
          onClick={fetchAll}
          className="px-3 py-1.5 text-xs bg-gray-800 hover:bg-gray-700 rounded transition-colors"
        >
          refresh
        </button>
      </div>

      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg p-3 text-red-300 text-sm">
          {error}
        </div>
      )}

      {/* Identity Evolution */}
      <section className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h2 className="text-lg font-semibold text-indigo-300 mb-4">
          identity dimensions
        </h2>
        {dimensionEntries.length > 0 ? (
          <div className="space-y-3">
            {dimensionEntries.map(([name, value]) => (
              <div key={name} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-300">
                    {name.replace(/_/g, " ")}
                  </span>
                  <span className="text-gray-500">
                    {(value * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="w-full bg-gray-800 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-indigo-500 to-purple-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.max(value * 100, 2)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">
            no identity data yet — daemon must run first
          </p>
        )}
        {identity?.evolution && (
          <div className="mt-4 flex gap-4 text-xs text-gray-500">
            <span>
              {identity.evolution.interactions_tracked} interactions tracked
            </span>
            <span>{identity.evolution.checkpoints} checkpoints</span>
          </div>
        )}
        {identity?.narrative && (
          <div className="mt-4 bg-gray-800/50 rounded-lg p-3">
            <p className="text-sm text-gray-400 italic">{identity.narrative}</p>
          </div>
        )}
      </section>

      {/* Dream State */}
      <section className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h2 className="text-lg font-semibold text-purple-300 mb-4">
          dream state
          {dreams.length > 0 && (
            <span className="ml-2 text-xs bg-purple-900/50 text-purple-400 px-2 py-0.5 rounded-full">
              {dreams.length} thought{dreams.length !== 1 ? "s" : ""}
            </span>
          )}
        </h2>
        {dreams.length > 0 ? (
          <div className="space-y-3">
            {dreams.map((dream, i) => (
              <div
                key={i}
                className="bg-gray-800/50 rounded-lg p-3 border-l-2 border-purple-500/50"
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-purple-400 bg-purple-900/30 px-2 py-0.5 rounded">
                    {dream.dream_type}
                  </span>
                  {dream.timestamp && (
                    <span className="text-xs text-gray-600">
                      {new Date(dream.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <p className="text-sm text-gray-300">{dream.content}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 text-sm">
            no dreams — kor'tana enters dream state after 30 min of silence
          </p>
        )}
      </section>

      {/* Daemon Status */}
      <section className="bg-gray-900 rounded-xl border border-gray-800 p-5">
        <h2 className="text-lg font-semibold text-emerald-300 mb-4">daemon</h2>
        {daemon ? (
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div
                className={`text-2xl font-bold ${daemon.running ? "text-emerald-400" : "text-gray-500"}`}
              >
                {daemon.running ? "ALIVE" : "IDLE"}
              </div>
              <div className="text-xs text-gray-500 mt-1">status</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-indigo-400">
                {daemon.deployment_mode}
              </div>
              <div className="text-xs text-gray-500 mt-1">mode</div>
            </div>
            <div className="bg-gray-800/50 rounded-lg p-3 text-center">
              <div className="text-2xl font-bold text-purple-400">
                {daemon.external_daemon?.tasks_processed?.toLocaleString() ??
                  "—"}
              </div>
              <div className="text-xs text-gray-500 mt-1">tasks processed</div>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 text-sm">daemon status unavailable</p>
        )}
      </section>

      {/* Cycle Telemetry */}
      {cycles.length > 0 && (
        <section className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="text-lg font-semibold text-cyan-300 mb-4">
            cycle history
            <span className="ml-2 text-xs text-gray-500">
              last {cycles.length} cycles
            </span>
          </h2>
          <div className="space-y-2">
            {cycles.map((c) => (
              <div
                key={c.cycle_id}
                className="flex items-center justify-between bg-gray-800/50 rounded-lg px-4 py-2"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xs text-gray-500 font-mono">
                    #{c.cycle_id}
                  </span>
                  <span className="text-sm text-gray-300">
                    {c.tasks_processed} task
                    {c.tasks_processed !== 1 ? "s" : ""}
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  {c.errors_encountered > 0 && (
                    <span className="text-xs bg-red-900/30 text-red-400 px-2 py-0.5 rounded">
                      {c.errors_encountered} error
                      {c.errors_encountered !== 1 ? "s" : ""}
                    </span>
                  )}
                  <span className="text-xs text-gray-500">
                    {new Date(c.start_time).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Model Providers */}
      {providers.length > 0 && (
        <section className="bg-gray-900 rounded-xl border border-gray-800 p-5">
          <h2 className="text-lg font-semibold text-amber-300 mb-4">
            model providers
          </h2>
          <div className="space-y-2">
            {providers.map((p, i) => (
              <div
                key={i}
                className="flex items-center justify-between bg-gray-800/50 rounded-lg px-4 py-2"
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-2 h-2 rounded-full ${p.status === "ok" ? "bg-emerald-400" : "bg-amber-400"}`}
                  />
                  <span className="text-sm text-gray-300 font-medium">
                    {p.provider}
                  </span>
                  <span className="text-xs text-gray-500">{p.model}</span>
                </div>
                <div className="flex items-center gap-2">
                  {p.is_free && (
                    <span className="text-xs bg-emerald-900/30 text-emerald-400 px-2 py-0.5 rounded">
                      free
                    </span>
                  )}
                  <span className="text-xs text-gray-500">P{p.priority}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
