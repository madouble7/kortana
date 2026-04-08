import { Brain, Database, Loader2, Search } from 'lucide-react';
import { useEffect, useState, type FormEvent } from 'react';
import { api } from '../lib/api';
import { formatRelativeTime } from '../lib/utils';
import type { Memory } from '../types';

export default function MemoryPanel() {
  const [memories, setMemories] = useState<Memory[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    fetchMemories();
  }, []);

  const fetchMemories = async () => {
    try {
      setLoading(true);
      const data = await api.getMemories();
      setMemories(data);
    } catch (error) {
      console.error('Failed to fetch memories:', error);
      setMemories([]);
    } finally {
      setLoading(false);
    }
  };

  const searchMemories = async (e: FormEvent) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      fetchMemories();
      return;
    }

    try {
      setSearching(true);
      const data = await api.searchMemory(searchQuery);
      setMemories(data);
    } catch (error) {
      console.error('Failed to search memories:', error);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Database className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">Memory</h2>
          </div>
          <span className="text-sm text-gray-500">{memories.length} items</span>
        </div>

        {/* Search */}
        <form onSubmit={searchMemories} className="flex gap-2">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search memories..."
              className="w-full bg-gray-800 text-white rounded-lg pl-10 pr-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="submit"
            disabled={searching}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-700 text-white rounded-lg px-4 py-2 transition-colors"
          >
            {searching ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              'Search'
            )}
          </button>
        </form>
      </div>

      {/* Memories List */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          </div>
        ) : memories.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Brain className="w-16 h-16 text-gray-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Memories</h3>
            <p className="text-gray-400 max-w-md">
              {searchQuery
                ? 'No memories found matching your search.'
                : 'Memories will appear here as you interact with Kor\'tana.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {memories.map((memory) => (
              <div
                key={memory.id}
                className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors"
              >
                <p className="text-gray-100 text-sm leading-relaxed">{memory.content}</p>
                <div className="flex items-center gap-3 mt-3">
                  {memory.relevance_score && (
                    <span className="text-xs px-2 py-1 rounded bg-blue-900/20 text-blue-400">
                      Relevance: {(memory.relevance_score * 100).toFixed(0)}%
                    </span>
                  )}
                  <span className="text-xs text-gray-500 ml-auto">
                    {formatRelativeTime(memory.created_at)}
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
