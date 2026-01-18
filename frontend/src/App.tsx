import {
  Activity,
  BrainCircuit,
  Cloud,
  Eye,
  Settings,
  ShieldCheck,
  Terminal,
  Zap
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import {
  ProtocolView,
  StorageView,
  SystemView,
  TaskQueueView,
  VisionDashboard
} from './components/UnifiedViews';
import { apiService } from './services/apiService';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState('vision');
  const [health, setHealth] = useState<any>(null);
  const [isElevated, setIsElevated] = useState(false);

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const h = await apiService.getHealth();
        setHealth(h);
      } catch (e) {
        console.error("Health check failed", e);
      }
    };
    fetchHealth();
    const timer = setInterval(fetchHealth, 30000);
    return () => clearInterval(timer);
  }, []);

  const navItems = [
    { id: 'vision', name: 'Vision', icon: <Eye size={20} />, color: 'text-cyan-400' },
    { id: 'protocol', name: 'Protocol', icon: <ShieldCheck size={20} />, color: 'text-emerald-400' },
    { id: 'tasks', name: 'Orchestration', icon: <BrainCircuit size={20} />, color: 'text-purple-400' },
    { id: 'storage', name: 'Reach', icon: <Cloud size={20} />, color: 'text-blue-400' },
    { id: 'system', name: 'System', icon: <Terminal size={20} />, color: 'text-amber-400' },
  ];

  return (
    <div className="flex h-screen bg-kor-deep text-gray-200 overflow-hidden font-sans">
      {/* Sidebar */}
      <aside className="w-64 bg-kor-surface border-r border-kor-accent/20 flex flex-col">
        <div className="p-6 border-b border-kor-accent/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-kor-accent to-blue-600 flex items-center justify-center">
              <Zap size={18} className="text-kor-deep fill-current" />
            </div>
            <h1 className="text-xl font-bold tracking-tight text-white">KOR'TANA</h1>
          </div>
          <p className="text-[10px] uppercase tracking-widest text-kor-accent/60 mt-2 font-semibold">Autonomous Intelligence</p>
        </div>

        <nav className="flex-1 p-4 space-y-2 overflow-y-auto">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${activeTab === item.id
                  ? 'bg-kor-accent/10 text-kor-accent border border-kor-accent/20 shadow-[0_0_15px_rgba(0,212,255,0.1)]'
                  : 'text-gray-400 hover:bg-white/5 hover:text-gray-200'
                }`}
            >
              <span className={activeTab === item.id ? 'text-kor-accent' : item.color}>{item.icon}</span>
              <span className="font-medium">{item.name}</span>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-kor-accent/10 space-y-4">
          <div className="flex items-center justify-between px-2 text-xs">
            <span className="text-gray-500">Elevation</span>
            <span className={`flex items-center gap-1 ${isElevated ? 'text-kor-accent' : 'text-gray-600'}`}>
              <Zap size={12} className={isElevated ? 'animate-pulse' : ''} />
              {isElevated ? 'Active' : 'Dormant'}
            </span>
          </div>
          <div className="flex items-center justify-between px-2 text-xs">
            <span className="text-gray-500">Pulse</span>
            <span className="flex items-center gap-1 text-emerald-400">
              <Activity size={12} />
              Steady
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-kor-surface/50 backdrop-blur-md border-b border-kor-accent/10 flex items-center justify-between px-8 z-10">
          <div className="flex items-center gap-2">
            <span className="text-gray-400 text-sm">Constellation /</span>
            <span className="text-kor-accent text-sm font-semibold capitalize">{activeTab}</span>
          </div>
          <div className="flex items-center gap-6">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health?.status === 'alive' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`}></div>
              <span className="text-xs font-medium text-gray-400">Node Status</span>
            </div>
            <button className="text-gray-400 hover:text-kor-accent transition-colors">
              <Settings size={18} />
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          {activeTab === 'vision' && <VisionDashboard />}
          {activeTab === 'protocol' && <ProtocolView />}
          {activeTab === 'tasks' && <TaskQueueView />}
          {activeTab === 'storage' && <StorageView />}
          {activeTab === 'system' && <SystemView />}
        </div>

        {/* Background Aura */}
        <div className="absolute top-[-10%] right-[-10%] w-[40%] h-[40%] bg-kor-accent/5 rounded-full blur-[100px] pointer-events-none"></div>
        <div className="absolute bottom-[-10%] left-[-10%] w-[30%] h-[30%] bg-blue-600/5 rounded-full blur-[80px] pointer-events-none"></div>
      </main>
    </div>
  );
};

// Placeholder components (to be implemented next as part of the unified engine)
const VisionDashboard = () => (
  <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-kor-surface p-6 rounded-2xl border border-kor-accent/10">
        <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <Eye className="text-kor-accent" size={20} />
          Multimodal Witness
        </h3>
        <div className="aspect-video bg-kor-deep rounded-xl border-2 border-dashed border-kor-accent/20 flex flex-col items-center justify-center text-gray-500 hover:border-kor-accent/40 transition-colors cursor-pointer group">
          <Upload size={32} className="mb-2 group-hover:text-kor-accent transition-colors" />
          <p className="text-sm">Drop visual data to activate memory</p>
        </div>
      </div>
      <div className="bg-kor-surface p-6 rounded-2xl border border-kor-accent/10 flex flex-col">
        <h3 className="text-lg font-semibold mb-4">Intelligence Output</h3>
        <div className="flex-1 bg-kor-deep/50 rounded-xl p-4 font-mono text-sm text-gray-400">
          Awaiting input signal...
        </div>
      </div>
    </div>
  </div>
);

const ProtocolView = () => <div className="text-gray-400 italic">Accessing Human Only Protocol registers...</div>;
const TaskQueueView = () => <div className="text-gray-400 italic">Synchronizing task queue with local git state...</div>;
const StorageView = () => <div className="text-gray-400 italic">Polling rclone remotes...</div>;
const SystemView = () => <div className="text-gray-400 italic">Fetching system telemetry...</div>;

const Upload = ({ size, className }: any) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" /><polyline points="17 8 12 3 7 8" /><line x1="12" y1="3" x2="12" y2="15" />
  </svg>
);

export default App;
