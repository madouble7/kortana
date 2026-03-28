import React, { useState } from 'react';
import { Github, Search, Loader2, AlertCircle, CheckCircle2, MessageSquare, Tag, User } from 'lucide-react';
import { analyzeGitHubIssue } from '../services/apiService';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function GitHubIssueAnalyzer() {
  const [issueUrl, setIssueUrl] = useState('');
  const [analysis, setAnalysis] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAnalyze = async () => {
    if (!issueUrl.trim()) return;
    setIsLoading(true);
    setError(null);
    try {
      const result = await analyzeGitHubIssue(issueUrl);
      setAnalysis(result);
    } catch (err) {
      setError('Failed to analyze GitHub issue. Please ensure the URL is correct and public.');
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
          GitHub Issue Analyzer
        </h2>
        <p className="text-gray-500">Analyze GitHub issues for sentiment, complexity, and suggested fixes.</p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 mb-8">
        <div className="flex gap-4">
          <div className="relative flex-1">
            <Github className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              value={issueUrl}
              onChange={(e) => setIssueUrl(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleAnalyze()}
              placeholder="https://github.com/owner/repo/issues/123"
              className="w-full bg-gray-50 dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl pl-12 pr-4 py-3 outline-none focus:ring-2 focus:ring-indigo-500 transition-all"
            />
          </div>
          <button
            onClick={handleAnalyze}
            disabled={isLoading || !issueUrl.trim()}
            className="bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:opacity-90 disabled:opacity-50 px-6 py-3 rounded-xl font-bold flex items-center gap-2 transition-all"
          >
            {isLoading ? <Loader2 className="animate-spin" size={20} /> : <Search size={20} />}
            Analyze
          </button>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-xl mb-8 flex items-center gap-2">
          <AlertCircle size={20} />
          {error}
        </div>
      )}

      {analysis ? (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Issue Header */}
          <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
            <div className="flex items-center gap-2 text-indigo-600 font-bold mb-4">
              <Github size={20} />
              <span>{analysis.repo || 'Repository'}</span>
            </div>
            <h3 className="text-3xl font-bold mb-6">{analysis.title || 'Issue Analysis'}</h3>
            
            <div className="flex flex-wrap gap-4">
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full text-sm">
                <User size={16} />
                <span>{analysis.author || 'Unknown'}</span>
              </div>
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full text-sm">
                <Tag size={16} />
                <span>{analysis.state || 'Open'}</span>
              </div>
              <div className="flex items-center gap-2 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full text-sm">
                <MessageSquare size={16} />
                <span>{analysis.comments_count || 0} comments</span>
              </div>
            </div>
          </div>

          {/* Analysis Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="bg-indigo-50 dark:bg-indigo-900/20 p-6 rounded-3xl border border-indigo-100 dark:border-indigo-800">
              <p className="text-indigo-600 dark:text-indigo-400 text-xs font-bold uppercase tracking-wider mb-2">Sentiment</p>
              <p className="text-2xl font-bold text-indigo-900 dark:text-indigo-100">{analysis.sentiment || 'Neutral'}</p>
            </div>
            <div className="bg-emerald-50 dark:bg-emerald-900/20 p-6 rounded-3xl border border-emerald-100 dark:border-emerald-800">
              <p className="text-emerald-600 dark:text-emerald-400 text-xs font-bold uppercase tracking-wider mb-2">Complexity</p>
              <p className="text-2xl font-bold text-emerald-900 dark:text-emerald-100">{analysis.complexity || 'Medium'}</p>
            </div>
            <div className="bg-amber-50 dark:bg-amber-900/20 p-6 rounded-3xl border border-amber-100 dark:border-amber-800">
              <p className="text-amber-600 dark:text-amber-400 text-xs font-bold uppercase tracking-wider mb-2">Priority</p>
              <p className="text-2xl font-bold text-amber-900 dark:text-amber-100">{analysis.priority || 'Normal'}</p>
            </div>
          </div>

          {/* Summary & Suggestions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
              <h4 className="text-xl font-bold mb-4 flex items-center gap-2">
                <CheckCircle2 className="text-emerald-500" />
                Summary
              </h4>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {analysis.summary || 'No summary available.'}
                </ReactMarkdown>
              </div>
            </div>

            <div className="bg-white dark:bg-gray-800 rounded-3xl p-8 border border-gray-200 dark:border-gray-700 shadow-sm">
              <h4 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertCircle className="text-indigo-500" />
                Suggested Fixes
              </h4>
              <div className="prose dark:prose-invert max-w-none">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {analysis.suggestions || 'No suggestions available.'}
                </ReactMarkdown>
              </div>
            </div>
          </div>
        </div>
      ) : !isLoading && (
        <div className="text-center py-20 opacity-30">
          <Github size={64} className="mx-auto mb-4" />
          <p>Enter a GitHub issue URL to begin analysis</p>
        </div>
      )}
    </div>
  );
}
