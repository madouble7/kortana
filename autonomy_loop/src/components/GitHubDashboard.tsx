import React, { useState } from 'react';
import { Github, Search, Loader2, AlertCircle, CheckCircle2, GitPullRequest, CircleDot } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { API_BASE } from '../services/config';

export default function GitHubDashboard() {
  const [repoUrl, setRepoUrl] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [githubToken, setGithubToken] = useState('');

  const handleAnalyze = async () => {
    if (!repoUrl.trim() || !githubToken.trim()) {
      setError('Please provide both a GitHub repository URL and a Personal Access Token.');
      return;
    }

    // Extract owner and repo from URL
    let owner = '';
    let repo = '';
    try {
      const urlObj = new URL(repoUrl);
      const parts = urlObj.pathname.split('/').filter(Boolean);
      if (parts.length >= 2) {
        owner = parts[0];
        repo = parts[1];
      } else {
        throw new Error('Invalid URL format');
      }
    } catch (e) {
      setError('Invalid GitHub repository URL. Format should be: https://github.com/owner/repo');
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch(`${API_BASE}/github/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${githubToken}`
        },
        body: JSON.stringify({ owner, repo }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to analyze repository');
      }

      const result = await response.json();
      setAnalysis(result);
    } catch (err: any) {
      setError(err.message || 'Failed to analyze GitHub repository. Please ensure the URL and token are correct.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="mb-8">
        <h2 className="text-2xl font-bold mb-2 flex items-center gap-2">
          <Github className="text-gray-900 dark:text-white" />
          GitHub Repository Analyzer
        </h2>
        <p className="text-gray-500">Analyze entire GitHub repositories for insights on issues and pull requests using Kor'tana AI.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-8">
        <div className="flex flex-col gap-4">
          <div className="relative">
            <input
              type="password"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="GitHub Personal Access Token (Required for API access)"
              className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl px-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
            <p className="text-xs text-gray-500 mt-1 ml-1">Your token is only sent to the backend and never stored.</p>
          </div>
          <div className="flex gap-4">
            <div className="relative flex-1">
              <Github className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
              <input
                type="text"
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
                placeholder="https://github.com/owner/repo"
                className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
              />
            </div>
            <button
              onClick={handleAnalyze}
              disabled={isLoading || !repoUrl.trim() || !githubToken.trim()}
              className="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white px-6 py-3 rounded-xl font-medium transition-colors flex items-center gap-2"
            >
              {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
              Analyze Repo
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-4 p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl flex items-start gap-3">
            <AlertCircle className="shrink-0 mt-0.5" size={20} />
            <p>{error}</p>
          </div>
        )}
      </div>

      {analysis && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700">
            <div className="flex items-center gap-3 mb-6">
              <CheckCircle2 className="text-emerald-500" size={24} />
              <h3 className="text-xl font-semibold">Analysis Complete for {analysis.repository}</h3>
            </div>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
              <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center gap-3">
                <CircleDot className="text-indigo-500" />
                <div>
                  <p className="text-sm text-gray-500">Open Issues Analyzed</p>
                  <p className="text-xl font-bold">{analysis.metadata.issuesCount}</p>
                </div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-900 p-4 rounded-xl border border-gray-200 dark:border-gray-700 flex items-center gap-3">
                <GitPullRequest className="text-emerald-500" />
                <div>
                  <p className="text-sm text-gray-500">Open PRs Analyzed</p>
                  <p className="text-xl font-bold">{analysis.metadata.pullRequestsCount}</p>
                </div>
              </div>
            </div>

            <div className="space-y-8">
              <div>
                <h4 className="text-lg font-semibold mb-3 text-indigo-600 dark:text-indigo-400 border-b pb-2">Overall Insights</h4>
                <div className="prose prose-slate dark:prose-invert max-w-none">
                  <ReactMarkdown>{analysis.analysis.overallInsights}</ReactMarkdown>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3 text-indigo-600 dark:text-indigo-400 border-b pb-2">Issues Analysis</h4>
                <div className="prose prose-slate dark:prose-invert max-w-none">
                  <ReactMarkdown>{analysis.analysis.issuesAnalysis}</ReactMarkdown>
                </div>
              </div>

              <div>
                <h4 className="text-lg font-semibold mb-3 text-indigo-600 dark:text-indigo-400 border-b pb-2">Pull Requests Analysis</h4>
                <div className="prose prose-slate dark:prose-invert max-w-none">
                  <ReactMarkdown>{analysis.analysis.pullRequestsAnalysis}</ReactMarkdown>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
