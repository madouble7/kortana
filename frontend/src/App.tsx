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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  useEffect(() => {
    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      setDeferredPrompt(e);
    });

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
      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-kor-surface border-r border-kor-accent/20 flex flex-col transition-transform duration-300 transform
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        md:relative md:translate-x-0
      `}>
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
              onClick={() => {
                setActiveTab(item.id);
                setSidebarOpen(false);
              }}
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
          {deferredPrompt && (
            <button
              onClick={() => {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choice: any) => {
                  if (choice.outcome === 'accepted') setDeferredPrompt(null);
                });
              }}
              className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-kor-accent text-kor-deep rounded-lg font-bold text-xs hover:shadow-[0_0_10px_rgba(0,212,255,0.3)] transition-all"
            >
              <Zap size={14} className="fill-current" />
              INSTALL KOR'TANA
            </button>
          )}
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
        <header className="h-16 bg-kor-surface/50 backdrop-blur-md border-b border-kor-accent/10 flex items-center justify-between px-4 md:px-8 z-10">
          <div className="flex items-center gap-4">
            <button
              className="md:hidden p-2 text-gray-400 hover:text-kor-accent"
              onClick={() => setSidebarOpen(true)}
            >
              <Activity size={20} />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-gray-400 text-sm hidden sm:block">Constellation /</span>
              <span className="text-kor-accent text-sm font-semibold capitalize">{activeTab}</span>
            </div>
          </div>
          <div className="flex items-center gap-4 md:gap-6">
            <div className="flex items-center gap-2">
              <div className={`w-2 h-2 rounded-full ${health?.status === 'alive' ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]'}`}></div>
              <span className="text-xs font-medium text-gray-400 hidden sm:block">Node Status</span>
            </div>
            <button className="text-gray-400 hover:text-kor-accent transition-colors">
              <Settings size={18} />
            </button>
          </div>
        </header>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 custom-scrollbar">
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

export default App;
