import {
  Activity,
  Brain,
  CheckSquare,
  Database,
  Github,
  Menu,
  MessageSquare,
  Settings as SettingsIcon,
  WifiOff,
  X,
} from 'lucide-react';
import type { ElementType } from 'react';
import { useState } from 'react';
import AkashicRecord from './components/AkashicRecord';
import Autonomy from './components/Autonomy';
import Chat from './components/Chat';
import GitHubPanel from './components/GitHub';
import GitHubDashboard from './components/GitHubDashboard';
import Memory from './components/Memory';
import OperatorDashboard from './components/OperatorDashboard';
import Settings from './components/Settings';
import Tasks from './components/Tasks';
import { useRuntimeTelemetry } from './hooks/useRuntimeTelemetry';
import { cn, formatRelativeTime } from './lib/utils';

type View = 'chat' | 'tasks' | 'autonomy' | 'memory' | 'github' | 'settings' | 'akashic' | 'operator';

interface NavItem {
  id: View;
  label: string;
  icon: ElementType;
  enabled: boolean;
}

function GitHubViewWithTabs() {
  const [tab, setTab] = useState<'pipeline' | 'browse'>('pipeline');
  return (
    <div className="flex flex-col h-full">
      <div className="flex border-b border-gray-800 bg-gray-900 shrink-0">
        {(['pipeline', 'browse'] as const).map(t => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-6 py-3 text-sm font-medium transition-colors ${tab === t
              ? 'text-green-400 border-b-2 border-green-400 bg-gray-800/40'
              : 'text-gray-400 hover:text-gray-200'
              }`}
          >
            {t === 'pipeline' ? '⚙ Pipeline' : '🔍 Browse Issues'}
          </button>
        ))}
      </div>
      <div className="flex-1 overflow-hidden">
        {tab === 'pipeline' ? <GitHubDashboard /> : <GitHubPanel />}
      </div>
    </div>
  );
}

function App() {
  const [currentView, setCurrentView] = useState<View>('chat');
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { health, daemon, errors, lastUpdatedAt } = useRuntimeTelemetry();

  const offline = health?.status === 'down' || (!!errors.health && !health);
  const daemonStatus = daemon;
  const daemonAlive = daemonStatus?.deployment_mode === 'embedded'
    ? daemonStatus.running
    : daemonStatus?.external_daemon?.alive;
  const providerHealth = daemonStatus?.provider_health ?? daemonStatus?.external_daemon?.provider_health ?? {};
  const providerNeedsAttention = Object.values(providerHealth).some(
    (state) => state !== 'ok' && state !== 'unknown'
  );
  const voiceStatus = daemonStatus?.voice_daemon;
  const presenceLabel = daemonAlive ? 'Silent Presence Active' : 'Presence Offline';
  const daemonLabel = daemonStatus?.deployment_mode === 'embedded'
    ? daemonStatus?.running
      ? 'Daemon Running'
      : 'Daemon Idle'
    : daemonStatus?.external_daemon?.alive
      ? 'Worker Fresh'
      : daemonStatus?.external_daemon?.state === 'stale'
        ? 'Worker Stale'
        : 'Worker Unknown';

  const navItems: NavItem[] = [
    {
      id: 'operator' as View,
      label: 'Operator',
      icon: Activity,
      enabled: true,
    },
    {
      id: 'chat',
      label: 'Chat',
      icon: MessageSquare,
      enabled: import.meta.env.VITE_ENABLE_CHAT !== 'false',
    },
    {
      id: 'tasks',
      label: 'Tasks',
      icon: CheckSquare,
      enabled: import.meta.env.VITE_ENABLE_TASKS !== 'false',
    },
    {
      id: 'autonomy',
      label: 'Autonomy',
      icon: Brain,
      enabled: import.meta.env.VITE_ENABLE_AUTONOMY !== 'false',
    },

    {
      id: 'akashic',
      label: 'Akashic',
      icon: Database,
      enabled: true,
    },
    {
      id: 'memory',
      label: 'Memory',
      icon: Database,
      enabled: import.meta.env.VITE_ENABLE_MEMORY !== 'false',
    },
    {
      id: 'github',
      label: 'GitHub',
      icon: Github,
      enabled: import.meta.env.VITE_ENABLE_GITHUB !== 'false',
    },
    {
      id: 'settings',
      label: 'Settings',
      icon: SettingsIcon,
      enabled: true,
    },
  ];

  const enabledNavItems = navItems.filter((item) => item.enabled);

  const renderView = () => {
    switch (currentView) {
      case 'operator':
        return <OperatorDashboard />;
      case 'chat':
        return <Chat />;
      case 'tasks':
        return <Tasks />;
      case 'autonomy':
        return <Autonomy />;

      case 'akashic':
        return <AkashicRecord />;
      case 'memory':
        return <Memory />;
      case 'github':
        return <GitHubViewWithTabs />;
      case 'settings':
        return <Settings />;
      default:
        return <Chat />;
    }
  };

  return (
    <div className="flex h-screen bg-gray-950 text-white">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-gray-900 border-b border-gray-800 flex items-center justify-between px-4 z-50">
        <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
          Kor'tana
        </h1>
        <button
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="text-gray-400 hover:text-white transition-colors"
        >
          {sidebarOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Sidebar */}
      <div
        className={cn(
          'fixed lg:static inset-y-0 left-0 w-64 bg-gray-900 border-r border-gray-800 transform transition-transform duration-300 ease-in-out z-40',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        )}
      >
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="hidden lg:flex items-center gap-3 px-6 py-6 border-b border-gray-800">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
              <span className="text-xl font-bold">K</span>
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                Kor'tana
              </h1>
              <p className="text-xs text-gray-500">AI Constellation</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-3 py-6 mt-16 lg:mt-0">
            <div className="space-y-1">
              {enabledNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      setCurrentView(item.id);
                      setSidebarOpen(false);
                    }}
                    className={cn(
                      'w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors',
                      currentView === item.id
                        ? 'bg-indigo-600 text-white'
                        : 'text-gray-400 hover:bg-gray-800 hover:text-white'
                    )}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="font-medium">{item.label}</span>
                  </button>
                );
              })}
            </div>
          </nav>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-800">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <div className={cn('w-2 h-2 rounded-full', offline ? 'bg-amber-500' : 'bg-green-500 animate-pulse')} />
                <span className="text-sm text-gray-400">{offline ? 'Demo Mode' : presenceLabel}</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  setCurrentView('autonomy');
                  setSidebarOpen(false);
                }}
                className="w-full flex items-center justify-between rounded-lg bg-gray-800/80 px-3 py-2 text-left hover:bg-gray-800 transition-colors"
              >
                <span className="text-xs text-gray-400 uppercase tracking-wide">Silent Autonomy</span>
                <span className="flex items-center gap-2">
                  <span className={cn('w-2 h-2 rounded-full', daemonAlive ? 'bg-green-500 animate-pulse' : 'bg-red-500')} />
                  <span className="text-sm text-gray-300">{daemonLabel}</span>
                </span>
              </button>
              {providerNeedsAttention && (
                <div className="text-xs text-yellow-300">
                  Provider attention required
                </div>
              )}
              {voiceStatus ? (
                <div className="text-xs text-gray-500">
                  voice dormant · {voiceStatus.status}
                </div>
              ) : (
                <div className="text-xs text-gray-500">
                  voice dormant
                </div>
              )}
              {lastUpdatedAt ? (
                <div className="text-[11px] text-gray-500">
                  runtime {formatRelativeTime(lastUpdatedAt)}
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Overlay */}
      {sidebarOpen && (
        <div
          className="lg:hidden fixed inset-0 bg-black/50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content */}
      <div className="flex-1 flex flex-col mt-16 lg:mt-0">
        {offline && (
          <div className="bg-amber-900/60 border-b border-amber-700 px-4 py-2 flex items-center gap-2 text-amber-200 text-sm">
            <WifiOff className="w-4 h-4 shrink-0" />
            <span>Backend offline — running in demo mode. UI is fully functional once the API is deployed.</span>
          </div>
        )}
        {renderView()}
      </div>
    </div>
  );
}

export default App;
