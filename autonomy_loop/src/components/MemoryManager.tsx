import React, { useState, useEffect } from 'react';
import { Brain, Plus, Trash2, Search, Loader2, AlertCircle, Save, Clock, Tag } from 'lucide-react';
import { getMemories, saveMemory, deleteMemory } from '../services/apiService';
import { motion, AnimatePresence } from 'framer-motion';

export default function MemoryManager() {
  const [memories, setMemories] = useState<any[]>([]);
  const [newMemory, setNewMemory] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchMemories = async () => {
    setIsLoading(true);
    try {
      const result = await getMemories();
      setMemories(result);
      setError(null);
    } catch (err) {
      setError('Failed to fetch memories.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchMemories();
  }, []);

  const handleSave = async () => {
    if (!newMemory.trim()) return;
    setIsSaving(true);
    try {
      await saveMemory(newMemory);
      setNewMemory('');
      await fetchMemories();
    } catch (err) {
      setError('Failed to save memory.');
      console.error(err);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await deleteMemory(id);
      await fetchMemories();
    } catch (err) {
      setError('Failed to delete memory.');
      console.error(err);
    }
  };

  const filteredMemories = memories.filter(m => 
    m.content.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Brain className="text-purple-600" />
          Memory Manager
        </h2>
        <p className="text-gray-500">Manage the persistent context and long-term memory of your AI agents.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Input Section */}
        <div className="lg:col-span-1 space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
              <Plus size={20} className="text-purple-600" />
              New Memory
            </h3>
            <textarea
              value={newMemory}
              onChange={(e) => setNewMemory(e.target.value)}
              placeholder="Enter a fact, preference, or context to remember..."
              className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-2xl p-4 h-32 outline-none focus:ring-2 focus:ring-purple-500 transition-all mb-4 text-sm"
            />
            <button
              onClick={handleSave}
              disabled={isSaving || !newMemory.trim()}
              className="w-full bg-purple-600 hover:bg-purple-700 disabled:opacity-50 text-white font-bold py-3 rounded-xl flex items-center justify-center gap-2 transition-all"
            >
              {isSaving ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
              Save to Memory
            </button>
          </div>

          {error && (
            <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-2xl flex items-center gap-2 text-sm">
              <AlertCircle size={18} />
              {error}
            </div>
          )}
        </div>

        {/* List Section */}
        <div className="lg:col-span-2 space-y-6">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories..."
              className="w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-2xl pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-purple-500 transition-all shadow-sm"
            />
          </div>

          <div className="space-y-4">
            {isLoading ? (
              <div className="text-center py-20">
                <Loader2 className="animate-spin mx-auto text-purple-600 mb-4" size={32} />
                <p className="text-gray-500">Accessing neural storage...</p>
              </div>
            ) : filteredMemories.length > 0 ? (
              <AnimatePresence mode="popLayout">
                {filteredMemories.map((memory) => (
                  <motion.div
                    key={memory.id}
                    layout
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-white dark:bg-gray-800 p-6 rounded-3xl border border-gray-200 dark:border-gray-700 shadow-sm group"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1">
                        <p className="text-gray-800 dark:text-gray-200 leading-relaxed">{memory.content}</p>
                        <div className="flex items-center gap-4 mt-4 text-[10px] font-bold uppercase tracking-wider text-gray-400">
                          <span className="flex items-center gap-1">
                            <Clock size={12} />
                            {new Date(memory.timestamp).toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Tag size={12} />
                            Context
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDelete(memory.id)}
                        className="p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-all opacity-0 group-hover:opacity-100"
                        title="Delete memory"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            ) : (
              <div className="text-center py-20 bg-gray-50 dark:bg-gray-900 rounded-3xl border-2 border-dashed border-gray-200 dark:border-gray-700">
                <Brain size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">No memories found. Start by adding one!</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
