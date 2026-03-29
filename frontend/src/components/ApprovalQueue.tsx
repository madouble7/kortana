import { AlertTriangle, CheckCircle, Loader2, XCircle } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../lib/api';

export function ApprovalQueue() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actioningId, setActioningId] = useState<string | null>(null);

  const fetchQueue = async () => {
    try {
      const data = await api.getApprovalQueue();
      setTasks(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch approval queue');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQueue();
    // Poll every 10 seconds
    const interval = setInterval(fetchQueue, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleAction = async (taskId: string, approved: boolean) => {
    setActioningId(taskId);
    try {
      const notes = prompt(`Any notes for this ${approved ? 'approval' : 'rejection'}? (Optional)`);
      if (notes === null) {
        // Cancelled prompt
        setActioningId(null);
        return;
      }
      await api.resolveApproval(taskId, approved, notes);
      await fetchQueue();
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to resolve approval');
    } finally {
      setActioningId(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 bg-gray-800/50 rounded-lg border border-yellow-900/30">
        <Loader2 className="w-6 h-6 text-yellow-500 animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/20 border border-red-500/50 rounded-lg text-red-400 text-sm">
        {error}
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <div className="bg-gray-800/50 rounded-lg p-6 border border-gray-700/50 text-center">
        <p className="text-gray-400">No tasks currently pending approval.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <AlertTriangle className="w-5 h-5 text-yellow-500" />
        <h3 className="text-lg font-semibold text-white">Pending Approvals</h3>
        <span className="bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded-full text-xs font-medium">
          {tasks.length}
        </span>
      </div>

      <div className="grid gap-4">
        {tasks.map((item) => {
          const t = item.task || {};
          const taskId = item.github_task_id || item.id;
          return (
          <div key={item.id} className="bg-gray-800/80 rounded-lg p-5 border border-yellow-900/40 hover:border-yellow-700/50 transition-colors">
            <div className="flex justify-between items-start mb-3">
              <div>
                <h4 className="text-white font-medium">{t.title || item.title || 'Unknown Task'}</h4>
                <p className="text-xs text-gray-500 mt-1 font-mono">{taskId}</p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleAction(taskId, true)}
                  disabled={actioningId === taskId}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-green-500/10 hover:bg-green-500/20 text-green-400 rounded-md text-sm transition-colors disabled:opacity-50"
                >
                  <CheckCircle className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={() => handleAction(taskId, false)}
                  disabled={actioningId === taskId}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 hover:bg-red-500/20 text-red-400 rounded-md text-sm transition-colors disabled:opacity-50"
                >
                  <XCircle className="w-4 h-4" />
                  Reject
                </button>
              </div>
            </div>

            {(item.rationale || (item.context && item.context.rationale) || (t.context && t.context.rationale)) && (
              <div className="mt-3 p-3 bg-gray-900/50 rounded border border-gray-800">
                <p className="text-sm text-gray-300">
                  <span className="text-gray-500 font-semibold mr-2">Rationale:</span>
                  {item.rationale || (item.context && item.context.rationale) || (t.context && t.context.rationale)}
                </p>
              </div>
            )}

            {(item.tool_name || t.tool_name) && (
              <div className="mt-3 flex gap-2">
                <span className="px-2 py-1 bg-gray-900 rounded text-xs text-gray-400 border border-gray-800">
                  Tool: {item.tool_name || t.tool_name}
                </span>
                {(item.priority || t.priority) && (
                  <span className="px-2 py-1 bg-gray-900 rounded text-xs text-gray-400 border border-gray-800">
                    Priority: {item.priority || t.priority}
                  </span>
                )}
              </div>
            )}
          </div>
        )})}
      </div>
    </div>
  );
}
