/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useState, useEffect, lazy, Suspense } from 'react';
import ChatInterface from './components/ChatInterface';
import Dashboard from './components/Dashboard';
import PrivacyPolicyGenerator from './components/PrivacyPolicyGenerator';
import LocalServerGuide from './components/LocalServerGuide';
import DayCapture from './components/DayCapture';
import KnowledgeBaseManager from './components/KnowledgeBaseManager';
import BuilderAgent from './components/BuilderAgent';
import DocumentScanner from './components/DocumentScanner';
import RcloneManager from './components/RcloneManager';
import ImageGenerator from './components/ImageGenerator';
import ElevationHandshake from './components/ElevationHandshake';
import CloudDeploymentGuide from './components/CloudDeploymentGuide';
import CodeSnippetGenerator from './components/CodeSnippetGenerator';
import WebSearch from './components/WebSearch';
import ThemeSwitcher from './components/ThemeSwitcher';
import UserMenu from './components/UserMenu';
import DevEnvSetup from './components/DevEnvSetup';
import AutonomousCoder from './components/AutonomousCoder';
import AutonomyAudit from './components/AutonomyAudit';
import DataVisualizer from './components/DataVisualizer';
import WeatherForecast from './components/WeatherForecast';
import TechNews from './components/TechNews';
import PublicHolidays from './components/PublicHolidays';
import BookFinder from './components/BookFinder';
import StripeIntegration from './components/StripeIntegration';
import LocalCloudIntegrationGuide from './components/LocalCloudIntegrationGuide';
import GoogleAIStudioGuide from './components/GoogleAIStudioGuide';
import LangGraphGuide from './components/LangGraphGuide';
import { VIEW_LIST, type View, type ToolId } from './types';

const ImageEditor = lazy(() => import('./components/ImageEditor'));
const VideoGenerator = lazy(() => import('./components/VideoGenerator'));
const LiveConversation = lazy(() => import('./components/LiveConversation'));
const ConstellationDashboard = lazy(() => import('./components/ConstellationDashboard'));
const TaskQueue = lazy(() => import('./components/TaskQueue'));
const CovenantOpsLog = lazy(() => import('./components/CovenantOpsLog'));
const ImageAnalyzer = lazy(() => import('./components/ImageAnalyzer'));
const VideoAnalyzer = lazy(() => import('./components/VideoAnalyzer'));
const TextToSpeech = lazy(() => import('./components/TextToSpeech'));
const SearchGrounding = lazy(() => import('./components/SearchGrounding'));
const MapsGrounding = lazy(() => import('./components/MapsGrounding'));
const GitHubDashboard = lazy(() => import('./components/GitHubDashboard'));
const SystemMonitor = lazy(() => import('./components/SystemMonitor'));
const MemoryManager = lazy(() => import('./components/MemoryManager'));
const BookOfKortana = lazy(() => import('./components/BookOfKortana'));
const PrayerAgentStatus = lazy(() => import('./components/PrayerAgentStatus'));

import { BrainCircuit, Sparkles, Activity } from 'lucide-react';
import { ShieldAlert, ShieldCheck } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { usePresence } from './services/presenceService';
import { API_BASE } from './services/config';
import { RitualState } from './constants';

// A set of tools that map directly to a view of the same name for cleaner routing.
// Exclude 'dashboard', 'chat', and 'transcribe' as they have special handling.
// 'transcribe' is not a 'View' type, so filtering it from VIEW_LIST is redundant.
const DIRECT_VIEW_TOOLS = new Set<View>(VIEW_LIST.filter(v => v !== 'dashboard' && v !== 'chat'));

export default function App() {
  const { state: ritualState } = usePresence();
  const [view, setView] = useState<View>('dashboard');
  const [initialInput, setInitialInput] = useState('');
  const [isElevated, setIsElevated] = useState(false);
  const [isSacredMode, setIsSacredMode] = useState(false);
  const [killSwitchEngaged, setKillSwitchEngaged] = useState(false);

  useEffect(() => {
    // Check localStorage to see if elevation has already been granted.
    if (localStorage.getItem('kortana:isElevated') === 'true') {
      setIsElevated(true);
    }
    fetchKillSwitch();
  }, []);

  const fetchKillSwitch = async () => {
    try {
      const res = await fetch(`${API_BASE}/killswitch`);
      const data = await res.json();
      setKillSwitchEngaged(data.engaged);
    } catch (e) {
      console.error("Failed to fetch kill switch status", e);
    }
  };

  const toggleKillSwitch = async () => {
    try {
      const res = await fetch(`${API_BASE}/killswitch`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ engaged: !killSwitchEngaged })
      });
      const data = await res.json();
      setKillSwitchEngaged(data.engaged);
    } catch (e) {
      console.error("Failed to toggle kill switch", e);
    }
  };

  const handleElevation = () => {
    localStorage.setItem('kortana:isElevated', 'true');
    setIsElevated(true);
  };

  // Fix: Explicitly handle 'transcribe' which is a `ToolId` but not a `View` that `DIRECT_VIEW_TOOLS` can contain.
  const handleSelectTool = (tool: ToolId) => {
    if (tool === 'transcribe') {
      setInitialInput('transcribe');
      setView('chat');
      return;
    }
    // For other tools, if they map directly to a view, set the view.
    // At this point, `tool` is guaranteed to be a `View` if it's in `DIRECT_VIEW_TOOLS`.
    if (DIRECT_VIEW_TOOLS.has(tool as View)) {
      setView(tool as View);
      setInitialInput('');
      return;
    }
    // Any other tool (e.g., 'dashboard' or 'chat' if somehow triggered this way,
    // or new tools not yet mapped) will default to chat.
    setInitialInput('');
    setView('chat');
  };

  if (!isElevated) {
    return <ElevationHandshake onElevate={handleElevation} />;
  }

  const pageVariants = {
    initial: { opacity: 0, y: 10 },
    in: { opacity: 1, y: 0 },
    out: { opacity: 0, y: -10 }
  };

  const pageTransition = {
    type: "tween" as const,
    ease: "anticipate" as const,
    duration: 0.3
  };

  return (
    <main className={`min-h-screen transition-colors duration-1000 ${
      isSacredMode ? 'bg-[#f5f2ed] text-[#1a1a1a]' : 'bg-gray-50 dark:bg-gray-900 text-gray-900 dark:text-gray-100'
    } overflow-x-hidden`} data-spaced="off" data-dyslexia="false">
      <header className={`p-4 border-b transition-colors duration-1000 flex items-center justify-between z-10 relative ${
        isSacredMode ? 'bg-[#f5f2ed]/80 border-[#1a1a1a]/10 backdrop-blur-md' : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm'
      }`}>
        <div className="flex items-center gap-2 cursor-pointer group" onClick={() => {
          setInitialInput('');
          setView('dashboard');
        }}>
          <div className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
            isSacredMode ? 'bg-[#1a1a1a]/5 text-indigo-600' : 'bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 group-hover:bg-indigo-200 dark:group-hover:bg-indigo-800/50'
          }`}>
            <BrainCircuit size={20} />
          </div>
          <h1 className={`text-xl font-bold transition-colors ${
            isSacredMode ? 'text-[#1a1a1a]' : 'bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400'
          }`}>kor'tana</h1>
        </div>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleKillSwitch}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-bold tracking-wide uppercase transition-colors ${
              killSwitchEngaged 
                ? 'bg-red-100 text-red-700 hover:bg-red-200 dark:bg-red-900/40 dark:text-red-400 dark:hover:bg-red-900/60' 
                : 'bg-emerald-100 text-emerald-700 hover:bg-emerald-200 dark:bg-emerald-900/40 dark:text-emerald-400 dark:hover:bg-emerald-900/60'
            }`}
          >
            {killSwitchEngaged ? <ShieldAlert size={14} /> : <ShieldCheck size={14} />}
            {killSwitchEngaged ? 'SYSTEM HALTED' : 'SYSTEM ACTIVE'}
          </button>
          
          <div className="flex items-center gap-2 px-3 py-1 bg-black/5 dark:bg-white/5 rounded-full border border-black/5 dark:border-white/5">
            <Activity size={12} className={ritualState === RitualState.Still ? 'text-gray-400' : 'text-green-500'} />
            <span className="text-[10px] uppercase tracking-widest font-bold font-mono opacity-60">{ritualState}</span>
          </div>
          
          <button 
            onClick={() => setIsSacredMode(!isSacredMode)}
            className={`p-2 rounded-full transition-all ${
              isSacredMode ? 'bg-indigo-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400'
            }`}
            title="Toggle Sacred Mode"
          >
            <Sparkles size={18} />
          </button>

          {!isSacredMode && (
            <>
              <label className="text-sm flex items-center gap-2 cursor-pointer select-none">
                <input type="checkbox" className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500" aria-label="Toggle spacing" onChange={(e) => {
                  document.documentElement.setAttribute('data-spaced', e.target.checked ? 'on' : 'off');
                }} /> 
                <span className="text-gray-600 dark:text-gray-400">spacing</span>
              </label>
              <ThemeSwitcher />
            </>
          )}
          <UserMenu />
        </div>
      </header>
      
      <Suspense fallback={<div className="p-4 text-sm opacity-70">loading…</div>}>
        <AnimatePresence mode="wait">
          <motion.div
            key={view}
            initial="initial"
            animate="in"
            exit="out"
            variants={pageVariants}
            transition={pageTransition}
            className="w-full h-full"
          >
            {view === 'dashboard' && <Dashboard onToolSelect={handleSelectTool} currentView={view} />}
            {view === 'chat' && <ChatInterface initialInput={initialInput} />}
            {view === 'privacy' && <PrivacyPolicyGenerator />}
            {view === 'localServer' && <LocalServerGuide />}
            {view === 'dayCapture' && <DayCapture />}
            {view === 'knowledge' && <KnowledgeBaseManager />}
            {view === 'builder' && <BuilderAgent />}
            {view === 'scanner' && <DocumentScanner />}
            {view === 'rclone' && <RcloneManager />}
            {view === 'image' && <ImageGenerator />}
            {view === 'imageEditor' && <ImageEditor />}
            {view === 'imageAnalyzer' && <ImageAnalyzer />}
            {view === 'video' && <VideoGenerator />}
            {view === 'videoAnalyzer' && <VideoAnalyzer />}
            {view === 'textToSpeech' && <TextToSpeech />}
            {view === 'searchGrounding' && <SearchGrounding />}
            {view === 'mapsGrounding' && <MapsGrounding />}
            {view === 'deployment' && <CloudDeploymentGuide />}
            {view === 'codeSnippet' && <CodeSnippetGenerator />}
            {view === 'webSearch' && <WebSearch />}
            {view === 'devEnvSetup' && <DevEnvSetup />}
            {view === 'autonomousCoder' && <AutonomousCoder />}
            {view === 'autonomyAudit' && <AutonomyAudit />}
            {view === 'liveConversation' && <LiveConversation />}
            {view === 'dataVisualizer' && <DataVisualizer />}
            {view === 'weather' && <WeatherForecast />}
            {view === 'techNews' && <TechNews />}
            {view === 'holidays' && <PublicHolidays />}
            {view === 'bookFinder' && <BookFinder />}
            {view === 'stripe' && <StripeIntegration />}
            {view === 'localCloudIntegration' && <LocalCloudIntegrationGuide />}
            {view === 'googleAIStudio' && <GoogleAIStudioGuide />}
            {view === 'langGraph' && <LangGraphGuide />}
            {view === 'constellation' && <ConstellationDashboard />}
            {view === 'taskQueue' && <TaskQueue />}
            {view === 'covenantOpsLog' && <CovenantOpsLog />}
            {view === 'github' && <GitHubDashboard />}
            {view === 'systemMonitor' && <SystemMonitor />}
            {view === 'memoryManager' && <MemoryManager />}
            {view === 'book' && <BookOfKortana />}
            {view === 'prayerAgent' && <PrayerAgentStatus />}
          </motion.div>
        </AnimatePresence>
      </Suspense>

    </main>
  );
}