import { useState } from 'react'

// Constants
const GITHUB_API_BASE = 'https://api.github.com'
const DEFAULT_ISSUES_PER_PAGE = 15

interface GitHubIssue {
  id: number
  number: number
  title: string
  body: string
  user: {
    login: string
    avatar_url: string
  }
  labels: Array<{
    name: string
    color: string
  }>
  html_url: string
  created_at: string
}

// Placeholder function for Gemini API integration
async function analyzeIssueWithGemini(title: string, _body: string): Promise<string> {
  // TODO: Integrate with Gemini API
  // This is where you would call the Gemini API to analyze the issue
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(`Analysis ready for: ${title}`)
    }, 1000)
  })
}

export default function GitHubIssueAnalyzer() {
  const [repoUrl, setRepoUrl] = useState('')
  const [issues, setIssues] = useState<GitHubIssue[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [analyzingIssue, setAnalyzingIssue] = useState<number | null>(null)
  const [analysisResult, setAnalysisResult] = useState<string | null>(null)

  const fetchIssues = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setIssues([])
    
    // Parse the repository URL or owner/repo format
    let owner = ''
    let repo = ''
    
    try {
      // Handle both "owner/repo" and full GitHub URLs
      if (repoUrl.includes('://')) {
        // Parse as URL
        const url = new URL(repoUrl)
        if (url.hostname !== 'github.com') {
          throw new Error('Only github.com URLs are supported')
        }
        const pathParts = url.pathname.split('/').filter(part => part.length > 0)
        if (pathParts.length < 2) {
          throw new Error('Invalid GitHub URL format')
        }
        owner = pathParts[0]
        repo = pathParts[1]
      } else if (repoUrl.includes('/')) {
        [owner, repo] = repoUrl.split('/')
      } else {
        throw new Error('Invalid format')
      }
      
      if (!owner || !repo) {
        throw new Error('Invalid repository format')
      }
      
      setLoading(true)
      
      // Fetch issues from GitHub REST API
      const response = await fetch(
        `${GITHUB_API_BASE}/repos/${owner}/${repo}/issues?state=open&per_page=${DEFAULT_ISSUES_PER_PAGE}&sort=created&direction=desc`,
        {
          headers: {
            'Accept': 'application/vnd.github.v3+json',
          },
        }
      )
      
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Repository not found')
        } else if (response.status === 403) {
          throw new Error('Rate limit exceeded. Please try again later.')
        } else {
          throw new Error(`Failed to fetch issues: ${response.statusText}`)
        }
      }
      
      const data = await response.json()
      
      // Filter out pull requests (GitHub API returns PRs as issues)
      const actualIssues = data.filter((issue: GitHubIssue) => !issue.html_url.includes('/pull/'))
      
      setIssues(actualIssues)
      
      if (actualIssues.length === 0) {
        setError('No open issues found in this repository')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyzeIssue = async (issue: GitHubIssue) => {
    setAnalyzingIssue(issue.id)
    setAnalysisResult(null)
    try {
      const result = await analyzeIssueWithGemini(issue.title, issue.body || 'No description provided')
      setAnalysisResult(result)
    } catch (err) {
      setAnalysisResult('Error analyzing issue. Please try again.')
    } finally {
      setAnalyzingIssue(null)
    }
  }

  return (
    <div className="max-w-5xl mx-auto">
      <div className="bg-gray-900 rounded-lg shadow-xl border border-gray-800 p-6 mb-6">
        <form onSubmit={fetchIssues} className="space-y-4">
          <div>
            <label htmlFor="repo-url" className="block text-sm font-medium text-gray-300 mb-2">
              GitHub Repository URL
            </label>
            <input
              id="repo-url"
              type="text"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="e.g., 'owner/repo' or 'https://github.com/owner/repo'"
              className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition"
              required
            />
          </div>
          <button
            type="submit"
            disabled={loading || !repoUrl.trim()}
            className="w-full px-6 py-3 bg-gradient-to-r from-purple-600 to-pink-600 text-white font-semibold rounded-lg hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Loading Issues...
              </span>
            ) : (
              'Fetch Issues'
            )}
          </button>
        </form>

        {error && (
          <div className="mt-4 p-4 bg-red-900/20 border border-red-700 rounded-lg">
            <p className="text-red-400 text-sm">{error}</p>
          </div>
        )}

        {analysisResult && (
          <div className="mt-4 p-4 bg-green-900/20 border border-green-700 rounded-lg">
            <p className="text-green-400 text-sm">{analysisResult}</p>
            <button
              onClick={() => setAnalysisResult(null)}
              className="mt-2 text-xs text-gray-400 hover:text-gray-200 transition"
            >
              Dismiss
            </button>
          </div>
        )}
      </div>

      {issues.length > 0 && (
        <div className="bg-gray-900 rounded-lg shadow-xl border border-gray-800 p-6">
          <h2 className="text-2xl font-semibold mb-4 text-gray-100">
            Open Issues ({issues.length})
          </h2>
          <div className="space-y-4 max-h-[600px] overflow-y-auto pr-2 custom-scrollbar">
            {issues.map((issue) => (
              <div
                key={issue.id}
                className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:border-purple-500 transition"
              >
                <div className="flex items-start gap-4">
                  <img
                    src={issue.user.avatar_url}
                    alt={issue.user.login}
                    className="w-10 h-10 rounded-full flex-shrink-0"
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <h3 className="text-lg font-semibold text-gray-100 break-words">
                        #{issue.number} {issue.title}
                      </h3>
                    </div>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-gray-400 mb-3">
                      <span>by {issue.user.login}</span>
                      <span>•</span>
                      <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>
                    {issue.labels.length > 0 && (
                      <div className="flex flex-wrap gap-2 mb-3">
                        {issue.labels.map((label) => (
                          <span
                            key={label.name}
                            className="px-2 py-1 text-xs rounded-full"
                            style={{
                              backgroundColor: `#${label.color}20`,
                              color: `#${label.color}`,
                              borderColor: `#${label.color}`,
                              borderWidth: '1px',
                            }}
                          >
                            {label.name}
                          </span>
                        ))}
                      </div>
                    )}
                    <div className="flex gap-2">
                      <a
                        href={issue.html_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 bg-gray-700 text-gray-200 text-sm font-medium rounded-lg hover:bg-gray-600 transition"
                      >
                        View on GitHub
                      </a>
                      <button
                        onClick={() => handleAnalyzeIssue(issue)}
                        disabled={analyzingIssue === issue.id}
                        className="px-4 py-2 bg-gradient-to-r from-purple-600 to-pink-600 text-white text-sm font-medium rounded-lg hover:from-purple-700 hover:to-pink-700 focus:outline-none focus:ring-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition"
                      >
                        {analyzingIssue === issue.id ? (
                          <span className="flex items-center gap-2">
                            <svg className="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                            </svg>
                            Analyzing...
                          </span>
                        ) : (
                          "Analyze with Kor'tana"
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
