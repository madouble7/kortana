import { useState, useEffect, type FormEvent } from 'react';
import {
  CheckCircle2,
  Circle,
  XCircle,
  Plus,
  Loader2,
  Play,
  Trash2,
  AlertCircle,
} from 'lucide-react';
import { api } from '../lib/api';
import { cn, formatRelativeTime } from '../lib/utils';
import type { Task } from '../types';

export default function Tasks() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [showNewTask, setShowNewTask] = useState(false);
  const [newTask, setNewTask] = useState({ title: '', description: '', priority: 'medium' as const });
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    fetchTasks();
  }, [filter]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const data = await api.getTasks(filter === 'all' ? undefined : filter);
      setTasks(data);
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTask = async (e: FormEvent) => {
    e.preventDefault();
    if (!newTask.title.trim()) return;

    try {
      setCreating(true);
      await api.createTask(newTask);
      setNewTask({ title: '', description: '', priority: 'medium' });
      setShowNewTask(false);
      fetchTasks();
    } catch (error) {
      console.error('Failed to create task:', error);
    } finally {
      setCreating(false);
    }
  };

  const executeTask = async (id: string) => {
    try {
      await api.executeTask(id);
      fetchTasks();
    } catch (error) {
      console.error('Failed to execute task:', error);
    }
  };

  const deleteTask = async (id: string) => {
    if (!confirm('Delete this task?')) return;
    try {
      await api.deleteTask(id);
      fetchTasks();
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const getStatusIcon = (status: Task['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'waiting_for_ho':
        return <AlertCircle className="w-5 h-5 text-yellow-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-500" />;
    }
  };

  const getPriorityColor = (priority: Task['priority']) => {
    switch (priority) {
      case 'high':
        return 'text-red-400 bg-red-900/20';
      case 'medium':
        return 'text-yellow-400 bg-yellow-900/20';
      case 'low':
        return 'text-green-400 bg-green-900/20';
    }
  };

  const filteredTasks = tasks;

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-white">Tasks</h2>
          <button
            onClick={() => setShowNewTask(true)}
            className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-4 py-2 transition-colors"
          >
            <Plus className="w-4 h-4" />
            New Task
          </button>
        </div>

        {/* Filters */}
        <div className="flex gap-2 overflow-x-auto">
          {['all', 'pending', 'running', 'completed', 'failed', 'waiting_for_ho'].map((f) => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={cn(
                'px-3 py-1 rounded-md text-sm transition-colors whitespace-nowrap',
                filter === f
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
              )}
            >
              {f === 'waiting_for_ho' ? 'Waiting HO' : f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {/* New Task Form */}
      {showNewTask && (
        <div className="px-6 py-4 bg-gray-800 border-b border-gray-700">
          <form onSubmit={createTask} className="space-y-3">
            <input
              type="text"
              value={newTask.title}
              onChange={(e) => setNewTask({ ...newTask, title: e.target.value })}
              placeholder="Task title"
              className="w-full bg-gray-900 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              autoFocus
            />
            <textarea
              value={newTask.description}
              onChange={(e) => setNewTask({ ...newTask, description: e.target.value })}
              placeholder="Description (optional)"
              className="w-full bg-gray-900 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 resize-none"
              rows={3}
            />
            <div className="flex items-center gap-2">
              <select
                value={newTask.priority}
                onChange={(e) => setNewTask({ ...newTask, priority: e.target.value as any })}
                className="bg-gray-900 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="low">Low Priority</option>
                <option value="medium">Medium Priority</option>
                <option value="high">High Priority</option>
              </select>
              <button
                type="submit"
                disabled={creating || !newTask.title.trim()}
                className="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white rounded-lg px-4 py-2 transition-colors"
              >
                {creating ? 'Creating...' : 'Create Task'}
              </button>
              <button
                type="button"
                onClick={() => {
                  setShowNewTask(false);
                  setNewTask({ title: '', description: '', priority: 'medium' });
                }}
                className="bg-gray-700 hover:bg-gray-600 text-white rounded-lg px-4 py-2 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Tasks List */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : filteredTasks.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <Circle className="w-16 h-16 text-gray-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Tasks</h3>
            <p className="text-gray-400 max-w-md">
              {filter === 'all'
                ? 'Create a task to get started.'
                : `No ${filter} tasks found.`}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredTasks.map((task) => (
              <div
                key={task.id}
                className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors"
              >
                <div className="flex items-start gap-3">
                  <div className="mt-0.5">{getStatusIcon(task.status)}</div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <h3 className="text-white font-medium">{task.title}</h3>
                      <div className="flex items-center gap-2">
                        {task.status === 'pending' && (
                          <button
                            onClick={() => executeTask(task.id)}
                            className="text-indigo-400 hover:text-indigo-300 transition-colors"
                            title="Execute task"
                          >
                            <Play className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => deleteTask(task.id)}
                          className="text-red-400 hover:text-red-300 transition-colors"
                          title="Delete task"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>
                    {task.description && (
                      <p className="text-gray-400 text-sm mt-1">{task.description}</p>
                    )}
                    <div className="flex items-center gap-2 mt-2">
                      <span className={cn('text-xs px-2 py-1 rounded', getPriorityColor(task.priority))}>
                        {task.priority}
                      </span>
                      {task.hop_capable && (
                        <span className="text-xs px-2 py-1 rounded bg-purple-900/20 text-purple-400">
                          HOP-capable
                        </span>
                      )}
                      {task.hop_executed_by && (
                        <span className="text-xs px-2 py-1 rounded bg-blue-900/20 text-blue-400">
                          Executed by {task.hop_executed_by}
                        </span>
                      )}
                      <span className="text-xs text-gray-500 ml-auto">
                        {formatRelativeTime(task.created_at)}
                      </span>
                    </div>
                    {task.result && (
                      <p className="text-green-400 text-sm mt-2 bg-green-900/10 rounded px-2 py-1">
                        Result: {task.result}
                      </p>
                    )}
                    {task.error && (
                      <p className="text-red-400 text-sm mt-2 bg-red-900/10 rounded px-2 py-1">
                        Error: {task.error}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
