import { useState, useEffect } from 'react';
import { Github, ExternalLink, GitBranch, Loader2, Plus } from 'lucide-react';
import { api } from '../lib/api';
import { formatRelativeTime } from '../lib/utils';
import type { GitHubIssue } from '../types';

export default function GitHubPanel() {
  const [issues, setIssues] = useState<GitHubIssue[]>([]);
  const [loading, setLoading] = useState(true);
  const [repo, setRepo] = useState('');
  const [creating, setCreating] = useState<number | null>(null);

  useEffect(() => {
    fetchIssues();
  }, []);

  const fetchIssues = async () => {
    try {
      setLoading(true);
      const data = await api.getGitHubIssues(repo || undefined);
      setIssues(data);
    } catch (error) {
      console.error('Failed to fetch GitHub issues:', error);
      setIssues([]);
    } finally {
      setLoading(false);
    }
  };

  const createTaskFromIssue = async (issue: GitHubIssue) => {
    if (!repo) {
      alert('Please specify a repository first');
      return;
    }

    try {
      setCreating(issue.number);
      await api.createTaskFromIssue(issue, repo);
      alert('Task created successfully!');
    } catch (error: any) {
      alert(`Failed to create task: ${error.message}`);
    } finally {
      setCreating(null);
    }
  };

  return (
    <div className="flex flex-col h-full bg-gray-900">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-800">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Github className="w-5 h-5 text-gray-400" />
            <h2 className="text-lg font-semibold text-white">GitHub Integration</h2>
          </div>
        </div>

        {/* Repository Input */}
        <div className="flex gap-2">
          <input
            type="text"
            value={repo}
            onChange={(e) => setRepo(e.target.value)}
            placeholder="owner/repository"
            className="flex-1 bg-gray-800 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <button
            onClick={fetchIssues}
            className="bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg px-4 py-2 transition-colors"
          >
            Load Issues
          </button>
        </div>
      </div>

      {/* Issues List */}
      <div className="flex-1 overflow-y-auto px-6 py-4">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <Loader2 className="w-8 h-8 text-indigo-400 animate-spin" />
          </div>
        ) : issues.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <GitBranch className="w-16 h-16 text-gray-600 mb-4" />
            <h3 className="text-xl font-semibold text-white mb-2">No Issues</h3>
            <p className="text-gray-400 max-w-md">
              {repo
                ? 'No issues found in this repository.'
                : 'Enter a repository to view issues.'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {issues.map((issue) => (
              <div
                key={issue.number}
                className="bg-gray-800 rounded-lg p-4 hover:bg-gray-750 transition-colors"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="text-sm text-gray-500">#{issue.number}</span>
                      <h3 className="text-white font-medium">{issue.title}</h3>
                    </div>
                    {issue.body && (
                      <p className="text-gray-400 text-sm line-clamp-2 mb-3">
                        {issue.body}
                      </p>
                    )}
                    <div className="flex items-center gap-2 flex-wrap">
                      <span
                        className={`text-xs px-2 py-1 rounded ${
                          issue.state === 'open'
                            ? 'bg-green-900/20 text-green-400'
                            : 'bg-gray-700 text-gray-400'
                        }`}
                      >
                        {issue.state}
                      </span>
                      {issue.labels.map((label) => (
                        <span
                          key={label}
                          className="text-xs px-2 py-1 rounded bg-blue-900/20 text-blue-400"
                        >
                          {label}
                        </span>
                      ))}
                      <span className="text-xs text-gray-500 ml-auto">
                        {formatRelativeTime(issue.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => createTaskFromIssue(issue)}
                      disabled={creating === issue.number}
                      className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-gray-700 text-white rounded-lg px-3 py-2 transition-colors text-sm flex items-center gap-1"
                      title="Create task from issue"
                    >
                      {creating === issue.number ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                      ) : (
                        <Plus className="w-4 h-4" />
                      )}
                    </button>
                    <a
                      href={`https://github.com/${repo}/issues/${issue.number}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-gray-400 hover:text-gray-300 transition-colors p-2"
                      title="View on GitHub"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </a>
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
