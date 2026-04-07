import React, { useState, useEffect } from "react";
import { 
  Activity, 
  Cpu, 
  Database, 
  Zap, 
  ShieldAlert, 
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Clock
} from "lucide-react";
import { motion } from "framer-motion";

interface SystemMetrics {
  cpu: number;
  memory: number;
  latency: number;
  resonance: number;
  status: "stable" | "degraded" | "critical";
}

const SystemMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics>({
    cpu: 0,
    memory: 0,
    latency: 0,
    resonance: 0,
    status: "stable",
  });

  useEffect(() => {
    const interval = setInterval(() => {
      setMetrics({
        cpu: Math.floor(Math.random() * 40) + 10,
        memory: Math.floor(Math.random() * 30) + 20,
        latency: Math.floor(Math.random() * 50) + 5,
        resonance: Math.floor(Math.random() * 20) + 80,
        status: "stable",
      });
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  const MetricCard = ({ 
    title, 
    value, 
    unit, 
    icon: Icon, 
    color 
  }: { 
    title: string; 
    value: number | string; 
    unit: string; 
    icon: any; 
    color: string;
  }) => (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-zinc-900 border border-zinc-800 p-4 rounded-xl"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-zinc-500 text-xs font-mono uppercase tracking-wider">{title}</span>
        <Icon className={`w-4 h-4 ${color}`} />
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold font-mono text-zinc-100">{value}</span>
        <span className="text-zinc-500 text-xs font-mono">{unit}</span>
      </div>
    </motion.div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-sm font-mono uppercase tracking-widest text-zinc-500 flex items-center gap-2">
          <Activity className="w-4 h-4" />
          System Telemetry
        </h2>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/20 rounded-full">
          <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-[10px] font-mono text-emerald-500 uppercase">Core Stable</span>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <MetricCard 
          title="Neural Load" 
          value={metrics.cpu} 
          unit="%" 
          icon={Cpu} 
          color="text-blue-400" 
        />
        <MetricCard 
          title="Memory Matrix" 
          value={metrics.memory} 
          unit="GB" 
          icon={Database} 
          color="text-purple-400" 
        />
        <MetricCard 
          title="Synaptic Lag" 
          value={metrics.latency} 
          unit="ms" 
          icon={Zap} 
          color="text-amber-400" 
        />
        <MetricCard 
          title="Ethical Resonance" 
          value={metrics.resonance} 
          unit="%" 
          icon={ShieldCheck} 
          color="text-emerald-400" 
        />
      </div>

      <div className="bg-zinc-900/50 border border-zinc-800/50 p-6 rounded-2xl">
        <div className="flex items-center gap-4 mb-6">
          <div className="p-3 bg-zinc-800 rounded-xl">
            <ShieldAlert className="w-6 h-6 text-zinc-400" />
          </div>
          <div>
            <h3 className="text-zinc-100 font-medium">Governance Protocol</h3>
            <p className="text-zinc-500 text-xs">Active monitoring of autonomous task execution and ethical alignment.</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/30">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-zinc-300 font-mono">Kill Switch Status</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-500 uppercase bg-emerald-500/10 px-2 py-0.5 rounded">Disengaged</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/30">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-4 h-4 text-emerald-500" />
              <span className="text-xs text-zinc-300 font-mono">Audit Logging</span>
            </div>
            <span className="text-[10px] font-mono text-emerald-500 uppercase bg-emerald-500/10 px-2 py-0.5 rounded">Active</span>
          </div>

          <div className="flex items-center justify-between p-3 bg-zinc-800/30 rounded-lg border border-zinc-700/30">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-4 h-4 text-amber-500" />
              <span className="text-xs text-zinc-300 font-mono">Escalation Threshold</span>
            </div>
            <span className="text-[10px] font-mono text-amber-500 uppercase bg-amber-500/10 px-2 py-0.5 rounded">Dynamic</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemMonitor;
