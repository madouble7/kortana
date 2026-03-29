import { useEffect, useState } from "react";

type ArchitectureMemory = {
    id: string;
    component_name: string;
    description: string;
    knowledge_factors: string[];
    evolution_stage: number;
    updated_at: string;
};

type AutonomyCycle = {
    id: string;
    start_time: string;
    end_time: string;
    tasks_processed: number;
    tasks_succeeded: number;
    tasks_failed: number;
    tasks_deferred: number;
    approvals_processed: number;
    incidents_recorded: number;
};

type IncidentMemory = {
    id: string;
    incident_type: string;
    description: string;
    resolution_strategy: string;
    resolved: boolean;
    created_at: string;
    repair_branch?: string | null;
    pr_url?: string | null;
    fix_status?: string | null;
};

type AkashicData = {
    architecture_memory: ArchitectureMemory[];
    recent_cycles: AutonomyCycle[];
    recent_incidents: IncidentMemory[];
};

export default function AkashicRecord() {
    const [data, setData] = useState<AkashicData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchMemory = async () => {
        try {
            const res = await fetch("http://localhost:8000/api/always-on/memory");
            if (!res.ok) throw new Error("Failed to fetch memory");
            const json = await res.json();
            if (json.status === "success" && json.data) {
                setData(json.data);
            }
        } catch (err: any) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMemory();
        const interval = setInterval(fetchMemory, 5000);
        return () => clearInterval(interval);
    }, []);

    const calculateConfidence = () => {
        if (!data?.recent_cycles || data.recent_cycles.length === 0) return 100;
        let totalProcessed = 0;
        let totalFailed = 0;
        data.recent_cycles.forEach(c => {
            totalProcessed += c.tasks_processed;
            totalFailed += c.tasks_failed;
        });
        if (totalProcessed === 0) return 100;
        return Math.max(0, Math.round(((totalProcessed - totalFailed) / totalProcessed) * 100));
    };

    if (loading && !data) {
        return <div className="p-6 text-gray-400 flex items-center justify-center h-full">Synchronizing with Akashic Record...</div>;
    }

    if (error && !data) {
        return <div className="p-6 text-red-400 flex items-center justify-center h-full">Error: {error}</div>;
    }

    const confidence = calculateConfidence();

    return (
        <div className="flex flex-col h-full bg-gray-900 overflow-y-auto">
            {/* Header */}
            <div className="px-6 py-4 border-b border-gray-800 flex justify-between items-center bg-gray-900/90 sticky top-0 backdrop-blur-sm z-10">
                <div className="flex items-center gap-3">
                    <span className="text-2xl">🌌</span>
                    <div>
                        <h2 className="text-lg font-semibold text-purple-400">Akashic Record</h2>
                        <p className="text-xs text-gray-500">Vector Gamma Persistent Memory</p>
                    </div>
                </div>
                <div className="flex flex-col items-end">
                    <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-gray-400">Core Confidence:</span>
                        <span className={`text-lg font-bold ${confidence > 80 ? "text-green-400" : confidence > 50 ? "text-yellow-400" : "text-red-400"}`}>
                            {confidence}%
                        </span>
                    </div>
                    <div className="text-[10px] text-gray-500 flex items-center gap-1">
                        <div className="w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></div> Live Sync
                    </div>
                </div>
            </div>

            <div className="p-6 space-y-8 max-w-7xl mx-auto w-full">
                {/* Cycles */}
                <section>
                    <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
                        <span className="w-1.5 h-4 bg-blue-500 rounded"></span>
                        <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">Daemon Cycles (Last 50)</h3>
                    </div>
                    {!data?.recent_cycles?.length ? (
                        <div className="bg-gray-800/50 p-4 rounded-lg text-center text-gray-500 text-sm">No recent cycles structural data recorded.</div>
                    ) : (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3">
                            {data.recent_cycles.slice(0, 12).map((cycle) => (
                                <div key={cycle.id} className="bg-gray-800 border border-gray-700 p-3 rounded-lg flex flex-col gap-2">
                                    <div className="flex justify-between items-center text-xs pb-2 border-b border-gray-700/50">
                                        <span className="text-gray-400 font-mono">
                                            {new Date(cycle.start_time).toLocaleTimeString()} - {new Date(cycle.end_time).toLocaleTimeString()}
                                        </span>
                                    </div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="bg-gray-900/50 px-2 py-1 rounded border border-gray-750 flex justify-between">
                                            <span className="text-gray-500">Processed</span>
                                            <span className="font-bold text-gray-300">{cycle.tasks_processed}</span>
                                        </div>
                                        <div className="bg-gray-900/50 px-2 py-1 rounded border border-green-900/30 flex justify-between">
                                            <span className="text-gray-500">Success</span>
                                            <span className="font-bold text-green-400">{cycle.tasks_succeeded}</span>
                                        </div>
                                        <div className="bg-gray-900/50 px-2 py-1 rounded border border-red-900/30 flex justify-between">
                                            <span className="text-gray-500">Failed</span>
                                            <span className="font-bold text-red-400">{cycle.tasks_failed}</span>
                                        </div>
                                        <div className="bg-gray-900/50 px-2 py-1 rounded border border-orange-900/30 flex justify-between">
                                            <span className="text-gray-500">Incidents</span>
                                            <span className="font-bold text-orange-400">{cycle.incidents_recorded}</span>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* Incidents */}
                <section>
                    <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
                        <span className="w-1.5 h-4 bg-orange-500 rounded"></span>
                        <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">Incident Memory</h3>
                    </div>
                    {!data?.recent_incidents?.length ? (
                        <div className="bg-green-900/10 border border-green-900/30 p-4 rounded-lg text-center text-green-500 text-sm">
                            System operating maximally. No unresolved structural incidents.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            {data.recent_incidents.map(inc => (
                                <div key={inc.id} className={`p-4 rounded-lg border ${inc.resolved ? "bg-gray-800 border-gray-700" : "bg-red-900/10 border-red-900/50"}`}>
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="flex items-center gap-2">
                                            <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${inc.resolved ? "bg-gray-700 text-gray-400" : "bg-red-900/50 text-red-400"}`}>
                                                {inc.incident_type}
                                            </span>
                                            <span className="text-xs text-gray-500 font-mono">{new Date(inc.created_at).toLocaleString()}</span>
                                        </div>
                                        {inc.resolved && <span className="text-xs text-green-500 font-bold flex items-center gap-1">✓ Resolved</span>}
                                    </div>
                                    <div className="text-sm text-gray-300 font-mono bg-gray-950 p-2 rounded border border-gray-800 whitespace-pre-wrap overflow-x-auto max-h-32">
                                        {inc.description}
                                    </div>
                                    {inc.fix_status && (
                                        <div className="mt-3 text-xs bg-blue-900/10 border border-blue-900/30 p-2 rounded flex flex-col gap-1">
                                            <div className="flex items-center gap-2">
                                                <span className="text-blue-400 font-semibold">Vector Alpha Healing Status:</span>
                                                <span className="px-1.5 py-0.5 bg-blue-900/30 text-blue-300 rounded text-[10px] uppercase font-bold">{inc.fix_status}</span>
                                            </div>
                                            {inc.repair_branch && (
                                                <div className="text-gray-400 font-mono mt-1">Branch: <span className="text-gray-300">{inc.repair_branch}</span></div>
                                            )}
                                            {inc.pr_url && (
                                                <div className="text-gray-400 mt-1">
                                                    PR: <a href={inc.pr_url} target="_blank" rel="noreferrer" className="text-blue-400 hover:underline">{inc.pr_url}</a>
                                                </div>
                                            )}
                                            {inc.resolution_strategy && (
                                                <div className="text-gray-500 mt-1 line-clamp-2" title={inc.resolution_strategy}>Strategy: {inc.resolution_strategy}</div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            ))}
                        </div>
                    )}
                </section>

                {/* Architecture */}
                <section>
                    <div className="flex items-center gap-2 mb-4 border-b border-gray-800 pb-2">
                        <span className="w-1.5 h-4 bg-purple-500 rounded"></span>
                        <h3 className="text-sm font-semibold text-gray-200 tracking-wide uppercase">Active Architecture Neural Map</h3>
                    </div>
                    {!data?.architecture_memory?.length ? (
                        <div className="bg-gray-800/50 p-4 rounded-lg text-center text-gray-500 text-sm">No deep architecture factors evaluated yet.</div>
                    ) : (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                            {data.architecture_memory.map(node => (
                                <div key={node.id} className="bg-gradient-to-br from-gray-800 to-gray-900 border border-purple-900/30 p-4 rounded-xl flex flex-col">
                                    <div className="flex justify-between items-start mb-2">
                                        <div className="text-sm font-bold font-mono text-purple-300">{node.component_name}</div>
                                        <div className="text-[10px] uppercase px-1.5 py-0.5 bg-purple-900/30 text-purple-400 rounded">Lv {node.evolution_stage}</div>
                                    </div>
                                    <p className="text-xs text-gray-400 mb-4 line-clamp-3 flex-1">{node.description}</p>
                                    {node.knowledge_factors && node.knowledge_factors.length > 0 && (
                                        <div className="flex flex-wrap gap-1.5">
                                            {node.knowledge_factors.map((kf, i) => (
                                                <span key={i} className="px-2 py-0.5 bg-gray-950 border border-gray-800 text-gray-400 text-[10px] rounded-full">
                                                    {kf}
                                                </span>
                                            ))}
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
