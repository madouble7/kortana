import React, { useState, useEffect } from 'react';
import { History, Plus, Loader2, Trash2, Shield } from 'lucide-react';
import { getMemories, saveMemory, deleteMemory } from '../services/apiService';
import { motion, AnimatePresence } from 'framer-motion';

export default function CovenantOpsLog() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [newLog, setNewLog] = useState('');

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const memories = await getMemories();
      setLogs(memories);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    
    // Record the specific fact requested by the user
    const recordFact = async () => {
      try {
        const memories = await getMemories();
        const fact = "harvest's favorite animal is a horse";
        if (!memories.some(m => m.content === fact)) {
          await saveMemory(fact);
          fetchLogs();
        }
      } catch (e) {
        console.error("Failed to record initial fact", e);
      }
    };
    recordFact();
  }, []);

  const handleAddLog = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newLog.trim()) return;
    try {
      await saveMemory(newLog);
      setNewLog('');
      fetchLogs();
    } catch (error) {
      console.error('Failed to save log:', error);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      fetchLogs();
    } catch (error) {
      console.error('Failed to delete log:', error);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto space-y-8 pb-24">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-3 bg-rose-500 rounded-xl text-white shadow-lg">
            <History size={24} />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Covenant Ops Log</h2>
            <p className="text-sm text-gray-500">Audit trail of autonomous intelligence operations</p>
          </div>
        </div>
        <div className="flex items-center gap-4">
          <div className="hidden md:flex items-center gap-2 px-3 py-1 bg-emerald-500/10 text-emerald-600 rounded-full border border-emerald-500/20">
            <Shield size={12} />
            <span className="text-[10px] font-bold uppercase tracking-widest">Encrypted</span>
          </div>
          <button 
            onClick={fetchLogs}
            className="p-2 text-gray-500 hover:text-indigo-600 transition-colors"
            title="Refresh Logs"
          >
            <Loader2 className={loading ? 'animate-spin' : ''} size={20} />
          </button>
        </div>
      </div>

      <form onSubmit={handleAddLog} className="bg-white dark:bg-gray-800 p-4 rounded-2xl border border-gray-200 dark:border-gray-700 shadow-sm flex gap-2 focus-within:border-indigo-500 transition-colors">
        <input
          type="text"
          value={newLog}
          onChange={(e) => setNewLog(e.target.value)}
          placeholder="Record a new operational fact or event..."
          className="flex-1 bg-transparent border-none focus:ring-0 text-sm text-gray-900 dark:text-gray-100 placeholder:text-gray-400"
        />
        <button 
          type="submit"
          disabled={!newLog.trim()}
          className="bg-indigo-600 text-white p-2 rounded-xl hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Plus size={20} />
        </button>
      </form>

      <div className="space-y-4">
        {loading && logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-24 space-y-4">
            <Loader2 className="animate-spin text-indigo-500" size={40} />
            <p className="text-sm text-gray-400 font-mono animate-pulse">DECRYPTING LOGS...</p>
          </div>
        ) : logs.length === 0 ? (
          <div className="text-center p-12 bg-gray-50 dark:bg-gray-800/50 rounded-3xl border border-dashed border-gray-200 dark:border-gray-700">
            <p className="text-gray-500 italic">No operational logs recorded yet.</p>
          </div>
        ) : (
          <AnimatePresence mode="popLayout">
            {logs.map((log) => (
              <motion.div
                key={log.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="group bg-white dark:bg-gray-800 p-5 rounded-2xl border border-gray-100 dark:border-white/5 shadow-sm hover:shadow-md transition-all flex items-start justify-between gap-4"
              >
                <div className="space-y-2 flex-1">
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-rose-500" />
                    <div className="text-[10px] font-mono uppercase tracking-widest text-gray-400">
                      {new Date(log.timestamp).toLocaleString()}
                    </div>
                  </div>
                  <p className="text-gray-700 dark:text-gray-300 leading-relaxed text-sm md:text-base">
                    {log.content}
                  </p>
                </div>
                <button 
                  onClick={() => handleDelete(log.id)}
                  className="opacity-0 group-hover:opacity-100 p-2 text-gray-400 hover:text-rose-500 transition-all rounded-lg hover:bg-rose-50 dark:hover:bg-rose-900/20"
                  title="Delete Log"
                >
                  <Trash2 size={16} />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
}
