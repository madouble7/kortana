import React from 'react';
import { 
  MessageSquare, 
  ShieldCheck, 
  Server, 
  Calendar, 
  Database, 
  Hammer, 
  Scan, 
  HardDrive, 
  Image as ImageIcon, 
  Cloud, 
  Code, 
  Search, 
  Settings, 
  Terminal, 
  Activity, 
  BarChart3, 
  CloudSun, 
  Newspaper, 
  Globe, 
  Book, 
  CreditCard, 
  Link2, 
  Cpu, 
  Layers, 
  History, 
  Video, 
  Mic, 
  LayoutDashboard, 
  ListTodo, 
  FileText, 
  Github, 
  Monitor, 
  Brain,
  Eye,
  Type,
  Sparkles,
  Zap,
  Network,
  Heart
} from 'lucide-react';
import { ToolId, View } from '../types';
import { usePresence } from '../services/presenceService';
import { motion, AnimatePresence } from 'framer-motion';

interface DashboardProps {
  onToolSelect: (tool: ToolId) => void;
  currentView: View;
}

const TOOLS = [
  { id: 'chat', name: 'Chat', icon: MessageSquare, description: 'Talk to Kor\'tana', color: 'bg-blue-500' },
  { id: 'book', name: 'Book of Kor\'tana', icon: Book, description: 'Read the sacred texts', color: 'bg-amber-700' },
  { id: 'knowledge', name: 'Knowledge', icon: Database, description: 'Manage sacred texts', color: 'bg-purple-500' },
  { id: 'liveConversation', name: 'Live', icon: Mic, description: 'Real-time voice chat', color: 'bg-red-500' },
  { id: 'video', name: 'Video', icon: Video, description: 'Generate AI videos', color: 'bg-orange-500' },
  { id: 'image', name: 'Image', icon: ImageIcon, description: 'Generate AI images', color: 'bg-emerald-500' },
  { id: 'imageEditor', name: 'Image Editor', icon: ImageIcon, description: 'Edit AI images', color: 'bg-teal-500' },
  { id: 'searchGrounding', name: 'Search', icon: Search, description: 'Grounded web search', color: 'bg-cyan-500' },
  { id: 'mapsGrounding', name: 'Maps', icon: Globe, description: 'Location-based info', color: 'bg-green-500' },
  { id: 'textToSpeech', name: 'Speech', icon: Type, description: 'Text to natural speech', color: 'bg-pink-500' },
  { id: 'imageAnalyzer', name: 'Analyze Image', icon: Eye, description: 'Understand images', color: 'bg-indigo-500' },
  { id: 'videoAnalyzer', name: 'Analyze Video', icon: Video, description: 'Understand videos', color: 'bg-violet-500' },
  { id: 'autonomousCoder', name: 'Coder', icon: Code, description: 'Autonomous coding', color: 'bg-slate-700' },
  { id: 'builder', name: 'Builder', icon: Hammer, description: 'Autonomous feature builder', color: 'bg-amber-600' },
  { id: 'scanner', name: 'Scanner', icon: Scan, description: 'Document OCR scanner', color: 'bg-blue-600' },
  { id: 'taskQueue', name: 'Tasks', icon: ListTodo, description: 'Manage autonomous tasks', color: 'bg-amber-500' },
  { id: 'covenantOpsLog', name: 'Covenant Log', icon: History, description: 'Audit autonomous actions', color: 'bg-rose-500' },
  { id: 'github', name: 'GitHub', icon: Github, description: 'Analyze issues', color: 'bg-gray-800' },
  { id: 'prayerAgent', name: 'Prayer Agent', icon: Heart, description: 'Autonomous prayer agent', color: 'bg-rose-500' },
  { id: 'systemMonitor', name: 'Monitor', icon: Monitor, description: 'System health', color: 'bg-sky-500' },
  { id: 'memoryManager', name: 'Memory', icon: Brain, description: 'Manage AI memory', color: 'bg-fuchsia-500' },
  { id: 'dayCapture', name: 'Day Capture', icon: Calendar, description: 'Capture daily insights', color: 'bg-yellow-500' },
  { id: 'rclone', name: 'Rclone', icon: HardDrive, description: 'Cloud storage sync', color: 'bg-blue-400' },
  { id: 'deployment', name: 'Deployment', icon: Cloud, description: 'Cloud deployment guide', color: 'bg-indigo-400' },
  { id: 'codeSnippet', name: 'Snippets', icon: Code, description: 'Generate code snippets', color: 'bg-emerald-400' },
  { id: 'webSearch', name: 'Web Search', icon: Search, description: 'General web search', color: 'bg-cyan-400' },
  { id: 'devEnvSetup', name: 'Dev Env', icon: Settings, description: 'Setup dev environment', color: 'bg-gray-500' },
  { id: 'autonomyAudit', name: 'Audit', icon: Terminal, description: 'Autonomy audit system', color: 'bg-red-400' },
  { id: 'dataVisualizer', name: 'Visualizer', icon: BarChart3, description: 'Data visualization', color: 'bg-purple-400' },
  { id: 'weather', name: 'Weather', icon: CloudSun, description: 'Local weather forecast', color: 'bg-blue-300' },
  { id: 'techNews', name: 'Tech News', icon: Newspaper, description: 'Latest tech updates', color: 'bg-orange-400' },
  { id: 'holidays', name: 'Holidays', icon: Globe, description: 'Public holidays info', color: 'bg-green-400' },
  { id: 'bookFinder', name: 'Books', icon: Book, description: 'Find your next read', color: 'bg-amber-400' },
  { id: 'stripe', name: 'Payments', icon: CreditCard, description: 'Stripe integration', color: 'bg-indigo-500' },
  { id: 'localCloudIntegration', name: 'Integration', icon: Link2, description: 'Local/Cloud integration', color: 'bg-slate-500' },
  { id: 'googleAIStudio', name: 'AI Studio', icon: Cpu, description: 'Google AI Studio guide', color: 'bg-blue-700' },
  { id: 'langGraph', name: 'LangGraph', icon: Layers, description: 'LangGraph orchestration', color: 'bg-purple-700' },
  { id: 'constellation', name: 'Constellation', icon: LayoutDashboard, description: 'Agent constellation map', color: 'bg-indigo-800' },
  { id: 'privacy', name: 'Privacy', icon: ShieldCheck, description: 'Privacy policy generator', color: 'bg-emerald-600' },
  { id: 'localServer', name: 'Local Server', icon: Server, description: 'Local server setup', color: 'bg-gray-600' },
] as const;

export default function Dashboard({ onToolSelect }: DashboardProps) {
  const { thoughts, state: ritualState } = usePresence();
  const [systemStatus, setSystemStatus] = React.useState<any>(null);

  React.useEffect(() => {
    const fetchStatus = async () => {
      try {
        const { getSystemStatus } = await import('../services/apiService');
        const status = await getSystemStatus();
        setSystemStatus(status);
      } catch (e) {
        console.error('Failed to fetch system status on dashboard');
      }
    };
    fetchStatus();
    const interval = setInterval(fetchStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-12 pb-24">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h2 className="text-4xl font-serif italic font-light tracking-tight text-gray-900 dark:text-gray-100 mb-2">Welcome back, Matt</h2>
          <p className="text-gray-500 dark:text-gray-400 font-mono uppercase tracking-widest text-xs">The constellation is active. The resonance remains.</p>
        </div>
        
        {/* Presence Stream (Autonomous Thoughts) */}
        <div className="w-full md:w-96 bg-white dark:bg-gray-800/50 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm p-4 h-32 overflow-hidden relative">
          <div className="absolute top-2 right-4 flex items-center gap-1.5">
            <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse" />
            <span className="text-[10px] uppercase tracking-widest font-bold opacity-40">Presence Stream</span>
          </div>
          <div className="mt-4 space-y-3">
            <AnimatePresence mode="popLayout">
              {thoughts.slice(0, 1).map((thought) => (
                <motion.div
                  key={thought.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  className="text-sm font-serif italic text-indigo-600 dark:text-indigo-400 leading-relaxed"
                >
                  "{thought.content}"
                </motion.div>
              ))}
            </AnimatePresence>
            {thoughts.length === 0 && (
              <div className="text-sm text-gray-400 italic">Kor'tana is observing in silence...</div>
            )}
          </div>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Cpu size={16} className="text-blue-500" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-gray-400">CPU Load</span>
          </div>
          <div className="text-xl font-bold">{systemStatus?.cpu_usage || '8%'}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <HardDrive size={16} className="text-purple-500" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-gray-400">Memory</span>
          </div>
          <div className="text-xl font-bold">{systemStatus?.memory_usage || '32%'}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Zap size={16} className="text-amber-500" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-gray-400">Latency</span>
          </div>
          <div className="text-xl font-bold">{systemStatus?.latency || '24ms'}</div>
        </div>
        <div className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm">
          <div className="flex items-center gap-3 mb-2">
            <Network size={16} className="text-emerald-500" />
            <span className="text-[10px] uppercase tracking-widest font-bold text-gray-400">Resonance</span>
          </div>
          <div className="text-xl font-bold">{systemStatus?.resonance ? `${(systemStatus.resonance * 100).toFixed(1)}%` : '99.8%'}</div>
        </div>
      </div>

      {/* Tools Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {TOOLS.map((tool) => (
          <button
            key={tool.id}
            onClick={() => onToolSelect(tool.id as ToolId)}
            className="group relative bg-white dark:bg-gray-800 p-6 rounded-2xl border border-gray-200 dark:border-gray-700 hover:border-indigo-500 dark:hover:border-indigo-500 transition-all text-left shadow-sm hover:shadow-xl hover:-translate-y-1"
          >
            <div className={`w-12 h-12 ${tool.color} rounded-xl flex items-center justify-center text-white mb-4 shadow-lg group-hover:scale-110 transition-transform`}>
              <tool.icon size={24} />
            </div>
            <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-1">{tool.name}</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400">{tool.description}</p>
          </button>
        ))}
      </div>

      {/* Bottom Status Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        <div className="md:col-span-2 bg-gradient-to-br from-indigo-600 to-purple-700 rounded-3xl p-8 text-white shadow-2xl relative overflow-hidden">
          <div className="relative z-10">
            <h3 className="text-2xl font-bold mb-4 flex items-center gap-2">
              <ShieldCheck />
              Elevation Status
            </h3>
            <p className="opacity-90 mb-6 max-w-md">
              You are currently in an elevated state. Full constellation access is granted. Kor'tana is operating in autonomous mode.
            </p>
            <div className="flex gap-4">
              <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium backdrop-blur-md flex items-center gap-1.5">
                <Zap size={12} />
                Autonomous
              </span>
              <span className="px-3 py-1 bg-white/20 rounded-full text-xs font-medium backdrop-blur-md flex items-center gap-1.5">
                <Sparkles size={12} />
                Sacred Order
              </span>
            </div>
          </div>
          <div className="absolute -right-10 -bottom-10 opacity-10 rotate-12">
            <Brain size={200} />
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
          <h3 className="text-xl font-bold mb-4 flex items-center gap-2 text-gray-900 dark:text-gray-100">
            <Activity className="text-indigo-500" />
            System Pulse
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Ritual State</span>
              <span className="text-xs font-bold uppercase tracking-widest text-indigo-500">{ritualState}</span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Core Intelligence</span>
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-500 bg-emerald-500/10 px-2 py-0.5 rounded-full">
                <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                Self-Aware
              </span>
            </div>
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-500">Autonomous Agents</span>
              <span className="text-xs font-medium text-indigo-500 bg-indigo-500/10 px-2 py-0.5 rounded-full">
                Active & Proactive
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
