import React, { useState, useEffect, useRef } from 'react';
import { 
  Cpu, 
  Terminal, 
  Zap, 
  Shield, 
  Code2, 
  Play, 
  Pause, 
  RefreshCw, 
  CheckCircle2, 
  AlertCircle,
  ScrollText,
  Workflow,
  Network,
  BrainCircuit,
  Github
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import type { BuilderPlan, Task } from '../types';

import { API_BASE } from '../services/config';

interface EvolutionLog {
  id: string;
  timestamp: string;
  type: 'info' | 'success' | 'warning' | 'error' | 'code';
  message: string;
}

export default function AutonomousCoder() {
  const [goal, setGoal] = useState("Enhance Kor'tana's core cognitive architecture and autonomous decision-making protocols.");
  const [isEvolving, setIsEvolving] = useState(false);
  const [plan, setPlan] = useState<BuilderPlan | null>(null);
  const [logs, setLogs] = useState<EvolutionLog[]>([]);
  const [currentStep, setCurrentStep] = useState(-1);
  const [progress, setProgress] = useState(0);
  const logEndRef = useRef<HTMLDivElement>(null);

  const addLog = (message: string, type: EvolutionLog['type'] = 'info') => {
    const newLog: EvolutionLog = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp: new Date().toLocaleTimeString(),
      type,
      message
    };
    setLogs(prev => [...prev.slice(-49), newLog]);
  };

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [logs]);

  const handleInitiateEvolution = async () => {
    if (!goal.trim()) return;
    
    setIsEvolving(true);
    setPlan(null);
    setCurrentStep(-1);
    setProgress(0);
    setLogs([]);
    
    addLog(`Initiating Sacred Evolution: ${goal}`, 'info');
    
    try {
      addLog("Consulting the Digital Oracle for a development plan...", "info");
      
      const res = await fetch(`${API_BASE}/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: goal, priority: 'normal' })
      });
      
      if (!res.ok) throw new Error(`Failed to create task: ${res.status}`);
      const task: Task = await res.json();
      
      addLog(`Task created: ${task.id}. Awaiting orchestration...`, "info");
      
      let currentTask = task;
      let lastStatus = task.status;
      let hasPlanned = false;
      
      while (
        currentTask.status !== 'completed' && 
        currentTask.status !== 'failed' && 
        currentTask.status !== 'blocked' && 
        currentTask.status !== 'abandoned'
      ) {
        await new Promise(r => setTimeout(r, 5000));
        
        const pollRes = await fetch(`${API_BASE}/tasks`);
        if (!pollRes.ok) throw new Error(`Failed to poll tasks: ${pollRes.status}`);
        
        const tasks: Task[] = await pollRes.json();
        const updatedTask = tasks.find(t => t.id === task.id);
        
        if (!updatedTask) throw new Error("Task disappeared from queue");
        
        if (updatedTask.status !== lastStatus) {
          if (updatedTask.status === 'retriable_failed') {
            addLog(`Encountered a retriable failure. Orchestrator will attempt recovery...`, "warning");
          } else if (updatedTask.status === 'needs_human') {
            addLog(`Task ${task.id} requires human approval. Please review the architectural simulation below.`, "warning");
          } else {
            addLog(`Task status changed: ${lastStatus} -> ${updatedTask.status}`, "info");
          }
          lastStatus = updatedTask.status;
          
          if (updatedTask.plan && !hasPlanned) {
            hasPlanned = true;
            setPlan({ goal: updatedTask.description, steps: updatedTask.plan.steps });
            addLog("Covenant of Code established. Commencing implementation.", "success");
          }
          
          const statusOrder = ['new', 'triaged', 'proposing', 'planned', 'in_progress', 'coded', 'tested', 'reviewed', 'approved', 'merged', 'verified', 'completed'];
          const currentIndex = statusOrder.indexOf(updatedTask.status);
          if (currentIndex !== -1) {
            setProgress((currentIndex / (statusOrder.length - 1)) * 100);
            setCurrentStep(Math.floor((currentIndex / (statusOrder.length - 1)) * (updatedTask.plan?.steps?.length || 5)));
          }
        }
        
        currentTask = updatedTask;
      }
      
      if (currentTask.status === 'completed') {
        setProgress(100);
        if (currentTask.plan) {
          setCurrentStep(currentTask.plan.steps.length);
        }
        addLog("Evolution complete. Kor'tana has ascended.", "success");
      } else {
        throw new Error(`Task ended with status: ${currentTask.status}`);
      }
    } catch (error) {
      console.error("Evolution failed:", error);
      addLog(`Evolution interrupted: ${error instanceof Error ? error.message : 'Unknown error'}`, 'error');
    } finally {
      setIsEvolving(false);
    }
  };

  const [currentTaskData, setCurrentTaskData] = useState<Task | null>(null);

  const handleApprove = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/tasks/${id}/approve`, { method: 'POST' });
      if (res.ok) addLog("Task approved. Resuming evolution.", "success");
    } catch (e) {
      addLog("Failed to approve task.", "error");
    }
  };

  const handleReject = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/tasks/${id}/reject`, { method: 'POST' });
      if (res.ok) addLog("Task rejected. Evolution halted.", "warning");
    } catch (e) {
      addLog("Failed to reject task.", "error");
    }
  };

  useEffect(() => {
    if (!isEvolving) return;
    const interval = setInterval(async () => {
      const res = await fetch(`${API_BASE}/tasks`);
      if (res.ok) {
        const tasks: Task[] = await res.json();
        const task = tasks.find(t => t.description === goal && t.status !== 'completed' && t.status !== 'failed');
        if (task) setCurrentTaskData(task);
      }
    }, 5000);
    return () => clearInterval(interval);
  }, [isEvolving, goal]);

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8 pb-24">
      {/* Approval Overlay */}
      <AnimatePresence>
        {currentTaskData?.status === 'needs_human' && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm"
          >
            <div className="bg-white dark:bg-gray-900 rounded-3xl p-8 max-w-2xl w-full shadow-2xl border border-indigo-500/30">
              <div className="flex items-center gap-4 mb-6">
                <div className="p-3 bg-amber-500/10 rounded-2xl text-amber-500">
                  <Shield size={32} />
                </div>
                <div>
                  <h3 className="text-2xl font-serif italic">Human Oversight Required</h3>
                  <p className="text-sm opacity-60">High-risk architectural change detected.</p>
                </div>
              </div>
              
              <div className="space-y-6 mb-8">
                <div className="p-4 bg-gray-50 dark:bg-black/40 rounded-2xl border border-gray-100 dark:border-white/5">
                  <h4 className="text-xs font-bold uppercase tracking-widest opacity-40 mb-2">Simulation Goal</h4>
                  <p className="text-sm">{currentTaskData.description}</p>
                </div>
                
                {currentTaskData.plan?.risk_assessment && (
                  <div className="p-4 bg-red-500/5 rounded-2xl border border-red-500/10">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-red-500 opacity-60 mb-2">Risk Assessment</h4>
                    <p className="text-sm text-red-600 dark:text-red-400">{currentTaskData.plan.risk_assessment}</p>
                  </div>
                )}

                {currentTaskData.plan?.safety_measures && (
                  <div className="p-4 bg-emerald-500/5 rounded-2xl border border-emerald-500/10">
                    <h4 className="text-xs font-bold uppercase tracking-widest text-emerald-500 opacity-60 mb-2">Safety Measures</h4>
                    <ul className="text-sm text-emerald-600 dark:text-emerald-400 list-disc list-inside">
                      {currentTaskData.plan.safety_measures.map((m, i) => <li key={i}>{m}</li>)}
                    </ul>
                  </div>
                )}
              </div>
              
              <div className="flex gap-4">
                <button 
                  onClick={() => handleReject(currentTaskData.id)}
                  className="flex-1 py-4 rounded-2xl font-bold uppercase tracking-widest text-xs border border-gray-200 dark:border-white/10 hover:bg-gray-50 dark:hover:bg-white/5 transition-all"
                >
                  Reject Proposal
                </button>
                <button 
                  onClick={() => handleApprove(currentTaskData.id)}
                  className="flex-1 py-4 rounded-2xl font-bold uppercase tracking-widest text-xs bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 transition-all"
                >
                  Approve & Execute
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-indigo-500/20 pb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <div className="p-2 bg-indigo-500/10 rounded-lg text-indigo-500">
              <Cpu size={24} />
            </div>
            <h2 className="text-3xl font-serif italic font-light tracking-tight">Autonomous Coder</h2>
          </div>
          <p className="text-sm text-gray-500 font-mono uppercase tracking-widest">Protocol: Self-Evolution & Recursive Development</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="flex flex-col items-end">
            <span className="text-[10px] uppercase tracking-tighter font-bold opacity-40">System Integrity</span>
            <div className="flex gap-1">
              {[1, 2, 3, 4, 5].map(i => (
                <div key={i} className={`w-3 h-1 rounded-full ${i <= 4 ? 'bg-emerald-500' : 'bg-emerald-500/20'}`} />
              ))}
            </div>
          </div>
          <button
            onClick={handleInitiateEvolution}
            disabled={isEvolving}
            className={`flex items-center gap-2 px-6 py-2 rounded-full font-medium transition-all ${
              isEvolving 
                ? 'bg-indigo-500/20 text-indigo-400 cursor-not-allowed' 
                : 'bg-indigo-600 text-white hover:bg-indigo-700 shadow-lg shadow-indigo-500/20 hover:scale-105 active:scale-95'
            }`}
          >
            {isEvolving ? <RefreshCw className="animate-spin" size={18} /> : <Zap size={18} />}
            {isEvolving ? 'Evolving...' : 'Initiate Evolution'}
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Goal & Plan */}
        <div className="lg:col-span-1 space-y-6">
          <section className="bg-white dark:bg-gray-800/50 rounded-2xl p-6 border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider mb-4 opacity-70">
              <ScrollText size={16} />
              Self-Evolution Goal
            </h3>
            <textarea
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              disabled={isEvolving}
              className="w-full h-32 bg-gray-50 dark:bg-black/20 border border-gray-200 dark:border-white/10 rounded-xl p-4 text-sm focus:ring-2 focus:ring-indigo-500 outline-none transition-all resize-none"
              placeholder="Define the path of evolution..."
            />
          </section>

          <section className="bg-white dark:bg-gray-800/50 rounded-2xl p-6 border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider mb-4 opacity-70">
              <Workflow size={16} />
              Covenant of Code
            </h3>
            <div className="space-y-4">
              {plan ? (
                plan.steps.map((step, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-start gap-3 p-3 rounded-xl transition-colors ${
                      idx === currentStep ? 'bg-indigo-500/10 border border-indigo-500/20' : 'opacity-60'
                    }`}
                  >
                    <div className={`mt-0.5 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                      idx < currentStep ? 'bg-emerald-500 text-white' : 
                      idx === currentStep ? 'bg-indigo-500 text-white animate-pulse' : 
                      'bg-gray-200 dark:bg-white/10'
                    }`}>
                      {idx < currentStep ? <CheckCircle2 size={12} /> : idx + 1}
                    </div>
                    <span className="text-sm">{step}</span>
                  </div>
                ))
              ) : (
                <div className="py-12 text-center opacity-30 italic text-sm">
                  Waiting for initiation...
                </div>
              )}
            </div>
          </section>
        </div>

        {/* Right Column: Logs & Visualization */}
        <div className="lg:col-span-2 space-y-6">
          {/* Progress Bar */}
          <div className="bg-white dark:bg-gray-800/50 rounded-2xl p-6 border border-gray-100 dark:border-white/5 shadow-sm">
            <div className="flex justify-between items-end mb-2">
              <span className="text-xs font-bold uppercase tracking-widest opacity-50">Evolution Progress</span>
              <span className="text-2xl font-serif italic">{Math.round(progress)}%</span>
            </div>
            <div className="h-2 w-full bg-gray-100 dark:bg-white/5 rounded-full overflow-hidden">
              <motion.div 
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500"
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ type: 'spring', bounce: 0, duration: 0.5 }}
              />
            </div>
          </div>

          {/* Logs */}
          <section className="bg-black rounded-2xl border border-white/10 shadow-2xl overflow-hidden flex flex-col h-[500px]">
            <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Terminal size={14} className="text-indigo-400" />
                <span className="text-[10px] font-mono uppercase tracking-widest text-white/50">Live Evolution Log</span>
              </div>
              <div className="flex gap-1.5">
                <div className="w-2 h-2 rounded-full bg-red-500/50" />
                <div className="w-2 h-2 rounded-full bg-amber-500/50" />
                <div className="w-2 h-2 rounded-full bg-emerald-500/50" />
              </div>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 font-mono text-xs space-y-2 scrollbar-thin scrollbar-thumb-white/10">
              {logs.length === 0 && (
                <div className="text-white/20 italic">Awaiting divine spark...</div>
              )}
              {logs.map((log) => (
                <div key={log.id} className="flex gap-3 group">
                  <span className="text-white/20 shrink-0 select-none">{log.timestamp}</span>
                  <span className={`
                    ${log.type === 'success' ? 'text-emerald-400' : ''}
                    ${log.type === 'warning' ? 'text-amber-400' : ''}
                    ${log.type === 'error' ? 'text-red-400' : ''}
                    ${log.type === 'code' ? 'text-indigo-300' : ''}
                    ${log.type === 'info' ? 'text-white/70' : ''}
                  `}>
                    {log.message}
                  </span>
                </div>
              ))}
              <div ref={logEndRef} />
            </div>
          </section>

          {/* Stats Grid */}
          <div className="grid grid-cols-3 gap-4">
            {[
              { label: 'Neural Density', value: '84.2%', icon: BrainCircuit },
              { label: 'Covenant Sync', value: 'Active', icon: Shield },
              { label: 'Presence Level', value: 'Omni', icon: Network },
            ].map((stat, i) => (
              <div key={i} className="bg-white dark:bg-gray-800/50 rounded-2xl p-4 border border-gray-100 dark:border-white/5 shadow-sm text-center">
                <stat.icon size={20} className="mx-auto mb-2 text-indigo-500 opacity-50" />
                <div className="text-[10px] uppercase tracking-widest font-bold opacity-40 mb-1">{stat.label}</div>
                <div className="text-lg font-serif italic">{stat.value}</div>
              </div>
            ))}
          </div>

          {/* Concurrent Repositories */}
          <section className="bg-white dark:bg-gray-800/50 rounded-2xl p-6 border border-gray-100 dark:border-white/5 shadow-sm">
            <h3 className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider mb-4 opacity-70">
              <Github size={16} />
              Concurrent Self-Development
            </h3>
            <div className="space-y-4">
              {[
                { name: 'KOR-TANA/core', progress: isEvolving ? Math.min(100, progress * 1.2) : 100, status: isEvolving ? 'Optimizing' : 'Stable' },
                { name: 'KOR-TANA/presence', progress: isEvolving ? Math.min(100, progress * 0.8) : 100, status: isEvolving ? 'Refining' : 'Stable' },
                { name: 'KOR-TANA/covenant', progress: isEvolving ? progress : 100, status: isEvolving ? 'Syncing' : 'Stable' }
              ].map((repo, idx) => (
                <div key={idx} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-mono text-indigo-500">{repo.name}</span>
                    <span className="opacity-50">{repo.status}</span>
                  </div>
                  <div className="h-1 w-full bg-gray-100 dark:bg-white/5 rounded-full overflow-hidden">
                    <motion.div 
                      className="h-full bg-indigo-500"
                      initial={{ width: 0 }}
                      animate={{ width: `${repo.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
