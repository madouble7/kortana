import {
    AlertCircle,
    BrainCircuit,
    CheckCircle2,
    Clock,
    FileText,
    HardDrive,
    Play,
    Terminal,
    Upload,
    Zap
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/apiService';
import geminiService from '../services/geminiService';

// --- VISION DASHBOARD ---
export const VisionDashboard: React.FC = () => {
    const [file, setFile] = useState<File | null>(null);
    const [analysis, setAnalysis] = useState<string>('');
    const [loading, setLoading] = useState(false);
    const [prompt, setPrompt] = useState('Analyze this visual data in the context of the Kor\'tana constellation.');

    const handleUpload = async () => {
        if (!file) return;
        setLoading(true);
        try {
            let res;
            if (file.type.startsWith('image/')) {
                res = await geminiService.analyzeImage(prompt, file);
            } else if (file.type.startsWith('video/')) {
                res = await geminiService.analyzeVideo(prompt, file);
            }
            setAnalysis(res?.response || 'Analysis complete, but no text returned.');
        } catch (e) {
            setAnalysis(`Error: ${e}`);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-kor-surface p-6 rounded-2xl border border-kor-accent/10 shadow-xl">
                    <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                        <Upload className="text-kor-accent" size={20} />
                        Multimodal Witness
                    </h3>

                    <div className="space-y-4">
                        <input
                            type="text"
                            value={prompt}
                            onChange={(e) => setPrompt(e.target.value)}
                            className="w-full bg-kor-deep border border-kor-accent/20 rounded-lg p-3 text-sm focus:border-kor-accent outline-none transition-colors"
                            placeholder="System prompt..."
                        />

                        <label className="block">
                            <div className="aspect-video bg-kor-deep rounded-xl border-2 border-dashed border-kor-accent/20 flex flex-col items-center justify-center text-gray-500 hover:border-kor-accent/40 transition-all cursor-pointer group overflow-hidden relative">
                                {file ? (
                                    <div className="text-center p-4">
                                        <FileText size={48} className="mx-auto mb-2 text-kor-accent" />
                                        <p className="text-sm font-medium text-gray-300">{file.name}</p>
                                        <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                                    </div>
                                ) : (
                                    <>
                                        <Upload size={32} className="mb-2 group-hover:text-kor-accent transition-colors" />
                                        <p className="text-sm">Transmit visual data (Image/Video)</p>
                                    </>
                                )}
                                <input type="file" className="hidden" onChange={(e) => setFile(e.target.files?.[0] || null)} />
                            </div>
                        </label>

                        <button
                            onClick={handleUpload}
                            disabled={!file || loading}
                            className={`w-full py-3 rounded-xl font-bold flex items-center justify-center gap-2 transition-all ${!file || loading
                                ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                                : 'bg-gradient-to-r from-kor-accent to-blue-600 text-kor-deep hover:shadow-[0_0_20px_rgba(0,212,255,0.4)]'
                                }`}
                        >
                            {loading ? <Terminal size={20} className="animate-spin" /> : <Play size={20} fill="currentColor" />}
                            {loading ? 'Processing Consciousness...' : 'Activate Vision'}
                        </button>
                    </div>
                </div>

                <div className="bg-kor-surface p-6 rounded-2xl border border-kor-accent/10 shadow-xl flex flex-col">
                    <h3 className="text-lg font-semibold mb-4 text-cyan-400">Intelligence Output</h3>
                    <div className="flex-1 bg-kor-deep/50 rounded-xl p-4 font-mono text-sm leading-relaxed overflow-y-auto max-h-[400px]">
                        {analysis ? (
                            <div className="text-gray-300 whitespace-pre-wrap">{analysis}</div>
                        ) : (
                            <div className="h-full flex flex-col items-center justify-center text-gray-600 space-y-2">
                                <BrainCircuit size={48} className="opacity-10" />
                                <p>Awaiting multimodal handshake...</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- PROTOCOL VIEW ---
export const ProtocolView: React.FC = () => {
    const [status, setStatus] = useState<any>(null);
    const [loading, setLoading] = useState(false);

    const fetchStatus = async () => {
        try {
            const s = await apiService.getProtocolStatus();
            setStatus(s);
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const runCycle = async () => {
        setLoading(true);
        try {
            await apiService.runAutonomousCycle();
            await fetchStatus();
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Human Only Protocol</h2>
                    <p className="text-sm text-gray-500">Task Classification & Execution Engine</p>
                </div>
                <button
                    onClick={runCycle}
                    disabled={loading}
                    className="bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 px-6 py-2 rounded-lg flex items-center gap-2 transition-all font-semibold"
                >
                    <Zap size={18} fill="currentColor" />
                    Run Auto Cycle
                </button>
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
                {/* Stats */}
                <div className="xl:col-span-3 grid grid-cols-1 md:grid-cols-4 gap-4">
                    <StatCard label="Total Tasks" value={status?.counts?.total || 0} icon={<FileText size={16} />} />
                    <StatCard label="Completed" value={status?.counts?.completed || 0} icon={<CheckCircle2 size={16} />} color="text-emerald-400" />
                    <StatCard label="Pending HO" value={status?.counts?.pending_ho || 0} icon={<Clock size={16} />} color="text-amber-400" />
                    <StatCard label="Failed" value={status?.counts?.failed || 0} icon={<AlertCircle size={16} />} color="text-red-400" />
                </div>

                {/* HO Tasks */}
                <div className="xl:col-span-2 space-y-4">
                    <h3 className="font-semibold text-gray-400 flex items-center gap-2">
                        <Terminal size={18} />
                        Active Directives (HO)
                    </h3>
                    {status?.tasks?.filter((t: any) => t.classification === 'HO' && t.status === 'pending').map((task: any) => (
                        <div key={task.id} className="bg-kor-surface border border-kor-accent/10 rounded-xl p-5 hover:border-kor-accent/30 transition-all group">
                            <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        <span className="text-[10px] font-bold bg-amber-500/10 text-amber-500 px-2 py-0.5 rounded uppercase">Human Action Required</span>
                                        <span className="text-gray-600 text-[10px] font-mono">#{task.id}</span>
                                    </div>
                                    <h4 className="text-lg font-bold text-gray-100">{task.title}</h4>
                                    <p className="text-sm text-gray-500 mt-1">{task.description}</p>

                                    {task.scaffold && (
                                        <pre className="mt-4 bg-kor-deep/80 rounded-lg p-4 text-xs font-mono text-cyan-300 overflow-x-auto border border-white/5">
                                            {task.scaffold}
                                        </pre>
                                    )}
                                </div>
                                <button className="bg-kor-accent text-kor-deep p-2 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity translate-x-2 group-hover:translate-x-0">
                                    <CheckCircle2 size={24} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>

                {/* Automation Log */}
                <div className="space-y-4">
                    <h3 className="font-semibold text-gray-400 flex items-center gap-2">
                        <Activity size={18} />
                        Automation Stream
                    </h3>
                    <div className="bg-kor-deep/50 rounded-xl border border-white/5 h-[500px] flex flex-col">
                        <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-[10px]">
                            {status?.tasks?.filter((t: any) => t.classification === 'AUTO').map((t: any) => (
                                <div key={t.id} className="flex gap-3">
                                    <span className={t.status === 'completed' ? 'text-emerald-500' : 'text-gray-500'}>[{t.status === 'completed' ? 'PASS' : 'WAIT'}]</span>
                                    <span className="text-gray-300">{t.title}</span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- SYSTEM TELEMETRY ---
export const SystemView: React.FC = () => {
    const [info, setInfo] = useState<any>(null);
    const [logs, setLogs] = useState<string[]>([]);

    useEffect(() => {
        const fetchSystem = async () => {
            try {
                const i = await apiService.getSystemInfo();
                setInfo(i);
                const l = await apiService.getLogs(50);
                setLogs(l.logs || []);
            } catch (e) { console.error(e); }
        };
        fetchSystem();
        const interval = setInterval(fetchSystem, 5000);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 animate-in fade-in slide-in-from-top-4 duration-500">
            <div className="lg:col-span-2 space-y-6">
                <div className="bg-kor-surface rounded-2xl border border-kor-accent/10 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold mb-6 flex items-center gap-2 text-amber-400">
                        <Terminal size={20} />
                        System Stream (AUTONOMY_EXECUTION.log)
                    </h3>
                    <div className="bg-kor-deep rounded-xl p-4 font-mono text-[11px] h-[500px] overflow-y-auto custom-scrollbar flex flex-col-reverse">
                        <div className="space-y-1">
                            {logs.map((log, i) => (
                                <div key={i} className="text-gray-500 hover:text-gray-300 transition-colors whitespace-pre-wrap py-0.5 border-b border-white/5 last:border-0">{log}</div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>

            <div className="space-y-6">
                <div className="bg-kor-surface rounded-2xl border border-kor-accent/10 p-6 shadow-xl">
                    <h3 className="text-lg font-semibold mb-6">Environment</h3>
                    <div className="space-y-4">
                        <InfoRow label="Operating System" value={info?.os || '...'} />
                        <InfoRow label="Python Version" value={info?.python_version || '...'} />
                        <div className="pt-4 border-t border-white/5 space-y-4">
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-500">CPU Usage</span>
                                    <span className="text-kor-accent font-bold">{info?.cpu_percent}%</span>
                                </div>
                                <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-kor-accent transition-all duration-1000" style={{ width: `${info?.cpu_percent}%` }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-xs mb-1">
                                    <span className="text-gray-500">Memory Usage</span>
                                    <span className="text-kor-accent font-bold">{info?.memory_percent}%</span>
                                </div>
                                <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
                                    <div className="h-full bg-kor-accent transition-all duration-1000" style={{ width: `${info?.memory_percent}%` }}></div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- STORAGE VIEW ---
export const StorageView: React.FC = () => {
    const [remotes, setRemotes] = useState<string[]>([]);
    const [selectedRemote, setSelectedRemote] = useState<string>('');
    const [files, setFiles] = useState<string[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const fetchRemotes = async () => {
            try {
                const res = await apiService.getRcloneRemotes();
                setRemotes(res.remotes || []);
                if (res.remotes?.length > 0) setSelectedRemote(res.remotes[0]);
            } catch (e) { console.error(e); }
        };
        fetchRemotes();
    }, []);

    useEffect(() => {
        if (!selectedRemote) return;
        const fetchFiles = async () => {
            setLoading(true);
            try {
                const res = await apiService.getRcloneFiles(selectedRemote.replace(':', ''));
                setFiles(res.files || []);
            } catch (e) { console.error(e); }
            finally { setLoading(false); }
        };
        fetchFiles();
    }, [selectedRemote]);

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-left-4 duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">The Reach</h2>
                    <p className="text-sm text-gray-500">Rclone Cloud Storage Management</p>
                </div>
                <div className="flex gap-2">
                    {remotes.map(r => (
                        <button
                            key={r}
                            onClick={() => setSelectedRemote(r)}
                            className={`px-4 py-2 rounded-lg text-sm font-semibold border transition-all ${selectedRemote === r
                                ? 'bg-kor-accent/10 border-kor-accent text-kor-accent'
                                : 'bg-kor-surface border-white/5 text-gray-400 hover:border-white/20'
                                }`}
                        >
                            {r}
                        </button>
                    ))}
                </div>
            </div>

            <div className="bg-kor-surface rounded-2xl border border-kor-accent/10 overflow-hidden shadow-2xl">
                <div className="p-4 border-b border-white/5 bg-kor-deep/30 flex items-center justify-between">
                    <span className="text-xs font-mono text-gray-500 flex items-center gap-2">
                        <HardDrive size={14} />
                        {selectedRemote}{selectedRemote.endsWith(':') ? '' : ':'}/
                    </span>
                    {loading && <Terminal size={14} className="animate-spin text-kor-accent" />}
                </div>
                <div className="p-2 min-h-[400px]">
                    {files.length > 0 ? (
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2">
                            {files.map((f, i) => (
                                <div key={i} className="flex items-center gap-3 p-3 rounded-lg hover:bg-white/5 transition-colors cursor-pointer group">
                                    <FileText size={18} className="text-blue-400 group-hover:text-kor-accent" />
                                    <span className="text-sm text-gray-300 truncate">{f}</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="h-[400px] flex flex-col items-center justify-center text-gray-600 space-y-2 font-mono">
                            {!loading && <p>Zero data objects detected.</p>}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

// --- TASK QUEUE VIEW ---
export const TaskQueueView: React.FC = () => {
    const [tasks, setTasks] = useState<any[]>([]);
    const [newTaskName, setNewTaskName] = useState('');

    const fetchTasks = async () => {
        try {
            const res = await apiService.getTasks();
            setTasks(res);
        } catch (e) { console.error(e); }
    };

    useEffect(() => {
        fetchTasks();
    }, []);

    const createTask = async () => {
        if (!newTaskName) return;
        try {
            await apiService.createTask(newTaskName, "Manual directive");
            setNewTaskName('');
            await fetchTasks();
        } catch (e) { console.error(e); }
    };

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold text-white">Task Orchestration</h2>
                    <p className="text-sm text-gray-500">Git State & Feature Branch Management</p>
                </div>
                <div className="flex gap-3">
                    <input
                        type="text"
                        placeholder="Blueprint Name..."
                        className="bg-kor-deep border border-kor-accent/20 rounded-lg px-4 py-2 text-sm outline-none focus:border-kor-accent transition-all"
                        value={newTaskName}
                        onChange={(e) => setNewTaskName(e.target.value)}
                    />
                    <button
                        onClick={createTask}
                        className="bg-purple-600 hover:bg-purple-500 text-white px-6 py-2 rounded-lg font-bold transition-all shadow-[0_0_15px_rgba(147,51,234,0.3)]"
                    >
                        Create Directive
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {tasks.map((task: any) => (
                    <div key={task.id} className="bg-kor-surface border border-white/5 rounded-2xl p-6 hover:border-purple-500/30 transition-all shadow-xl flex flex-col justify-between group">
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase tracking-wider ${task.status === 'completed' ? 'bg-emerald-500/10 text-emerald-500' :
                                    task.status === 'in_progress' ? 'bg-blue-500/10 text-blue-500 animate-pulse' :
                                        'bg-gray-500/10 text-gray-500'
                                    }`}>
                                    {task.status.replace('_', ' ')}
                                </span>
                                <span className="text-gray-700 text-[10px] font-mono">#{task.id}</span>
                            </div>
                            <h4 className="text-lg font-bold text-gray-100 group-hover:text-purple-400 transition-colors">{task.name}</h4>
                            <p className="text-sm text-gray-500 mt-2 line-clamp-2">{task.description}</p>

                            {task.branch_name && (
                                <div className="mt-4 flex items-center gap-2 text-xs font-mono bg-kor-deep rounded-lg p-2 text-purple-300">
                                    <Terminal size={12} />
                                    {task.branch_name}
                                </div>
                            )}
                        </div>

                        <div className="mt-6 flex items-center justify-between">
                            <span className="text-[10px] text-gray-600 font-medium">Created: {new Date(task.created_at).toLocaleDateString()}</span>
                            <button className="text-purple-400 hover:text-purple-300 text-sm font-bold flex items-center gap-1 group/btn">
                                Details
                                <Play size={10} className="group-hover/btn:translate-x-0.5 transition-transform" />
                            </button>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

const StatCard = ({ label, value, icon, color = 'text-gray-100' }: any) => (
    <div className="bg-kor-surface border border-white/5 rounded-xl p-4 flex items-center gap-4">
        <div className="bg-kor-deep p-2.5 rounded-lg text-kor-accent">{icon}</div>
        <div>
            <p className="text-[10px] uppercase tracking-widest text-gray-600 font-bold">{label}</p>
            <p className={`text-xl font-bold ${color}`}>{value}</p>
        </div>
    </div>
);

const InfoRow = ({ label, value }: any) => (
    <div className="flex justify-between items-center text-sm">
        <span className="text-gray-500">{label}</span>
        <span className="text-gray-200 font-mono">{value}</span>
    </div>
);

const BrainCircuit = ({ size, className }: any) => (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        <path d="M12 4.5a2.5 2.5 0 0 0-4.96-.46 2.5 2.5 0 0 0-1.98 3 2.5 2.5 0 0 0-1.32 4.24 3 3 0 0 0 .34 5.58 2.5 2.5 0 0 0 2.96 3.08 2.5 2.5 0 0 0 4.96.46 2.5 2.5 0 0 0 4.96-.46 2.5 2.5 0 0 0 2.96-3.08 3 3 0 0 0 .34-5.58 2.5 2.5 0 0 0-1.32-4.24 2.5 2.5 0 0 0-1.98-3A2.5 2.5 0 0 0 12 4.5z" /><path d="M12 8c1.5 0 3 1.5 3 3s-1.5 3-3 3-3-1.5-3-3 1.5-3 3-3z" />
    </svg>
);

const VisionDash = () => <VisionDashboard />; // Export alias
