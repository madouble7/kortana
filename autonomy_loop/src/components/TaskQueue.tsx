import React, { useEffect, useState } from 'react';
import { Construction, CheckCircle, Circle, AlertCircle, Clock, ShieldAlert, BrainCircuit } from 'lucide-react';
import { Task } from '../types';
import { API_BASE } from '../services/config';

export default function TaskQueue() {
  const [tasks, setTasks] = useState<Task[]>([]);

  useEffect(() => {
    const fetchTasks = () => {
      fetch(`${API_BASE}/tasks`)
        .then(res => res.json())
        .then(setTasks);
    };
    fetchTasks();
    const interval = setInterval(fetchTasks, 5000);
    return () => clearInterval(interval);
  }, []);

  const [newTask, setNewTask] = useState('');

  const addTask = async () => {
    if (!newTask) return;
    const res = await fetch(`${API_BASE}/tasks`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ description: newTask, priority: 'normal' })
    });
    const task = await res.json();
    setTasks([...tasks, task]);
    setNewTask('');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'verified':
      case 'completed':
        return <CheckCircle className="text-green-500" />;
      case 'proposing':
        return <BrainCircuit className="text-purple-500 animate-pulse" />;
      case 'needs_human':
        return <ShieldAlert className="text-amber-500 animate-bounce" />;
      case 'blocked':
      case 'failed':
        return <AlertCircle className="text-red-500" />;
      case 'new':
      case 'triaged':
      case 'planned':
      case 'in_progress':
      case 'coded':
      case 'tested':
      case 'reviewed':
      case 'approved':
      case 'merged':
        return <Clock className="text-blue-500 animate-pulse" />;
      default:
        return <Circle className="text-gray-400" />;
    }
  };

  return (
    <div className="p-8">
      <h2 className="text-2xl font-bold mb-4">Autonomous Task Queue</h2>
      <div className="flex gap-2 mb-4">
        <input 
          className="border p-2 rounded flex-grow dark:bg-gray-800 dark:border-gray-700"
          value={newTask}
          onChange={e => setNewTask(e.target.value)}
          placeholder="New task description"
        />
        <button className="bg-indigo-600 text-white p-2 rounded hover:bg-indigo-700" onClick={addTask}>Add Task</button>
      </div>
      <div className="space-y-4">
        {tasks.map(task => (
          <div key={task.id} className="p-4 border rounded-lg flex items-center justify-between dark:border-gray-700 dark:bg-gray-800">
            <div>
              <p className="font-semibold">{task.description}</p>
              <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                <span className={`px-2 py-0.5 rounded-full text-xs ${
                  task.priority === 'urgent' ? 'bg-red-100 text-red-800' :
                  task.priority === 'normal' ? 'bg-blue-100 text-blue-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {task.priority}
                </span>
                <span className="font-mono bg-gray-100 dark:bg-gray-700 px-2 py-0.5 rounded text-xs">
                  {task.status}
                </span>
                {task.risk_score !== undefined && (
                  <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs ${
                    task.risk_score > 80 ? 'bg-red-100 text-red-800' :
                    task.risk_score > 50 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-green-100 text-green-800'
                  }`}>
                    <ShieldAlert size={12} />
                    Risk: {Math.round(task.risk_score)}
                  </span>
                )}
                {task.assigned_to && (
                  <span className="text-xs">Agent: {task.assigned_to}</span>
                )}
                {task.plan && (
                  <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded-full dark:bg-purple-900 dark:text-purple-200">
                    Plan: {task.plan.steps?.length || 0} steps
                  </span>
                )}
                {task.changeset && (
                  <span className="text-xs bg-green-100 text-green-800 px-2 py-0.5 rounded-full dark:bg-green-900 dark:text-green-200">
                    Changes: {task.changeset.files_changed?.length || 0} files
                  </span>
                )}
                {task.test_report && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    task.test_report.exit_code === 0 
                      ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200' 
                      : 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                  }`}>
                    Tests: {task.test_report.exit_code === 0 ? 'Passed' : 'Failed'}
                  </span>
                )}
                {task.review_summary && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    task.review_summary.approved 
                      ? 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200' 
                      : 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                  }`}>
                    Review: {task.review_summary.approved ? 'Approved' : 'Rejected'}
                  </span>
                )}
                {task.merge_result && (
                  <span className="text-xs bg-indigo-100 text-indigo-800 px-2 py-0.5 rounded-full dark:bg-indigo-900 dark:text-indigo-200">
                    Merged: {task.merge_result.merge_sha.substring(0, 7)}
                  </span>
                )}
              </div>
            </div>
            {getStatusIcon(task.status)}
          </div>
        ))}
        {tasks.length === 0 && (
          <div className="text-center p-8 text-gray-500 border border-dashed rounded-lg dark:border-gray-700">
            No tasks in queue. Add a task to start the autonomy loop.
          </div>
        )}
      </div>
    </div>
  );
}
