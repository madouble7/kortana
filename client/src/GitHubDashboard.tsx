import React, { useState, useEffect } from 'react';
import './GitHubDashboard.css';

interface Issue {
  number: number;
  title: string;
  state: string;
  html_url: string;
  user: {
    login: string;
  };
  created_at: string;
}

interface PullRequest {
  number: number;
  title: string;
  state: string;
  html_url: string;
  user: {
    login: string;
  };
  created_at: string;
}

interface Repository {
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  stargazers_count: number;
  open_issues_count: number;
}

interface Analysis {
  issuesAnalysis: string;
  pullRequestsAnalysis: string;
  overallInsights: string;
}

const GitHubDashboard: React.FC = () => {
  const [token, setToken] = useState<string>('');
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [repos, setRepos] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<string>('');
  const [issues, setIssues] = useState<Issue[]>([]);
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>('');

  const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:3001';

  const handleAuthenticate = async () => {
    if (!token) {
      setError('Please enter a GitHub token');
      return;
    }

    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/github/user`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      setIsAuthenticated(true);
      localStorage.setItem('github_token', token);
      await fetchRepositories();
    } catch (err) {
      setError('Failed to authenticate. Please check your token.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRepositories = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/api/github/repos`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to fetch repositories');
      }

      const data = await response.json();
      setRepos(data);
    } catch (err) {
      setError('Failed to fetch repositories');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchRepoData = async (repoFullName: string) => {
    const [owner, repo] = repoFullName.split('/');
    setLoading(true);
    setError('');

    try {
      const [issuesRes, prsRes] = await Promise.all([
        fetch(`${API_BASE}/api/github/repos/${owner}/${repo}/issues`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch(`${API_BASE}/api/github/repos/${owner}/${repo}/pulls`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (!issuesRes.ok || !prsRes.ok) {
        throw new Error('Failed to fetch repository data');
      }

      const issuesData = await issuesRes.json();
      const prsData = await prsRes.json();

      setIssues(issuesData);
      setPullRequests(prsData);
    } catch (err) {
      setError('Failed to fetch repository data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleRepoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const repoFullName = e.target.value;
    setSelectedRepo(repoFullName);
    setAnalysis(null);
    if (repoFullName) {
      fetchRepoData(repoFullName);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedRepo) return;

    const [owner, repo] = selectedRepo.split('/');
    setLoading(true);
    setError('');

    try {
      const response = await fetch(`${API_BASE}/api/github/analyze`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ owner, repo }),
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const data = await response.json();
      setAnalysis(data.analysis);
    } catch (err) {
      setError('Failed to analyze repository. Make sure GEMINI_API_KEY is configured.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const savedToken = localStorage.getItem('github_token');
    if (savedToken) {
      setToken(savedToken);
    }
  }, []);

  if (!isAuthenticated) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h1>🚀 Kor'tana GitHub Dashboard</h1>
          <p>Connect your GitHub account to analyze repositories</p>
          <input
            type="password"
            placeholder="Enter GitHub Personal Access Token"
            value={token}
            onChange={(e) => setToken(e.target.value)}
            className="token-input"
          />
          <button onClick={handleAuthenticate} disabled={loading} className="auth-button">
            {loading ? 'Authenticating...' : 'Connect'}
          </button>
          {error && <div className="error">{error}</div>}
          <div className="help-text">
            <small>
              Need a token?{' '}
              <a
                href="https://github.com/settings/tokens/new"
                target="_blank"
                rel="noopener noreferrer"
              >
                Create one here
              </a>{' '}
              (needs repo scope)
            </small>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <h1>🚀 Kor'tana GitHub Dashboard</h1>
        <button onClick={() => setIsAuthenticated(false)} className="logout-button">
          Logout
        </button>
      </header>

      <div className="dashboard-content">
        <div className="repo-selector">
          <label htmlFor="repo-select">Select Repository:</label>
          <select
            id="repo-select"
            value={selectedRepo}
            onChange={handleRepoChange}
            className="repo-select"
          >
            <option value="">-- Choose a repository --</option>
            {repos.map((repo) => (
              <option key={repo.full_name} value={repo.full_name}>
                {repo.full_name} ⭐ {repo.stargazers_count}
              </option>
            ))}
          </select>
        </div>

        {error && <div className="error">{error}</div>}

        {selectedRepo && (
          <>
            <div className="data-section">
              <div className="card">
                <h2>📋 Issues ({issues.length})</h2>
                <div className="items-list">
                  {issues.length === 0 ? (
                    <p>No open issues</p>
                  ) : (
                    issues.slice(0, 5).map((issue) => (
                      <div key={issue.number} className="item">
                        <a href={issue.html_url} target="_blank" rel="noopener noreferrer">
                          #{issue.number}: {issue.title}
                        </a>
                        <span className="item-meta">
                          by {issue.user.login} • {new Date(issue.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>

              <div className="card">
                <h2>🔀 Pull Requests ({pullRequests.length})</h2>
                <div className="items-list">
                  {pullRequests.length === 0 ? (
                    <p>No open pull requests</p>
                  ) : (
                    pullRequests.slice(0, 5).map((pr) => (
                      <div key={pr.number} className="item">
                        <a href={pr.html_url} target="_blank" rel="noopener noreferrer">
                          #{pr.number}: {pr.title}
                        </a>
                        <span className="item-meta">
                          by {pr.user.login} • {new Date(pr.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>

            <div className="analyze-section">
              <button
                onClick={handleAnalyze}
                disabled={loading}
                className="analyze-button"
              >
                {loading ? 'Analyzing with Kor\'tana AI...' : '🤖 Analyze with Kor\'tana AI'}
              </button>
            </div>

            {analysis && (
              <div className="analysis-section">
                <div className="card">
                  <h2>🔍 Issues Analysis</h2>
                  <div className="analysis-content">{analysis.issuesAnalysis}</div>
                </div>

                <div className="card">
                  <h2>🔍 Pull Requests Analysis</h2>
                  <div className="analysis-content">{analysis.pullRequestsAnalysis}</div>
                </div>

                <div className="card highlight">
                  <h2>💡 Overall Insights</h2>
                  <div className="analysis-content">{analysis.overallInsights}</div>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default GitHubDashboard;
