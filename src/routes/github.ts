import { Router, Request, Response } from 'express';
import { GitHubConnector } from '../services/GitHubConnector';
import { KortanaAI } from '../services/KortanaAI';

const router = Router();

/**
 * GET /api/github/user
 * Get authenticated user information
 */
router.get('/user', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const connector = new GitHubConnector(authToken);
    const user = await connector.getAuthenticatedUser();
    res.json(user);
  } catch (error) {
    console.error('Error fetching user:', error);
    res.status(500).json({ error: 'Failed to fetch user information' });
  }
});

/**
 * GET /api/github/repos
 * Get user repositories
 */
router.get('/repos', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const connector = new GitHubConnector(authToken);
    const repos = await connector.getUserRepositories();
    res.json(repos);
  } catch (error) {
    console.error('Error fetching repositories:', error);
    res.status(500).json({ error: 'Failed to fetch repositories' });
  }
});

/**
 * GET /api/github/repos/:owner/:repo
 * Get specific repository information
 */
router.get('/repos/:owner/:repo', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const { owner, repo } = req.params;
    const connector = new GitHubConnector(authToken);
    const repository = await connector.getRepository(owner, repo);
    res.json(repository);
  } catch (error) {
    console.error('Error fetching repository:', error);
    res.status(500).json({ error: 'Failed to fetch repository' });
  }
});

/**
 * GET /api/github/repos/:owner/:repo/issues
 * Get repository issues
 */
router.get('/repos/:owner/:repo/issues', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const { owner, repo } = req.params;
    const state = (req.query.state as 'open' | 'closed' | 'all') || 'open';
    
    const connector = new GitHubConnector(authToken);
    const issues = await connector.getIssues(owner, repo, state);
    res.json(issues);
  } catch (error) {
    console.error('Error fetching issues:', error);
    res.status(500).json({ error: 'Failed to fetch issues' });
  }
});

/**
 * GET /api/github/repos/:owner/:repo/pulls
 * Get repository pull requests
 */
router.get('/repos/:owner/:repo/pulls', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const { owner, repo } = req.params;
    const state = (req.query.state as 'open' | 'closed' | 'all') || 'open';
    
    const connector = new GitHubConnector(authToken);
    const pullRequests = await connector.getPullRequests(owner, repo, state);
    res.json(pullRequests);
  } catch (error) {
    console.error('Error fetching pull requests:', error);
    res.status(500).json({ error: 'Failed to fetch pull requests' });
  }
});

/**
 * POST /api/github/analyze
 * Analyze repository data using Kor'tana's Gemini AI
 */
router.post('/analyze', async (req: Request, res: Response) => {
  try {
    const authToken = req.headers.authorization?.replace('Bearer ', '');
    if (!authToken) {
      return res.status(401).json({ error: 'Authorization token required' });
    }

    const geminiApiKey = process.env.GEMINI_API_KEY;
    if (!geminiApiKey) {
      return res.status(500).json({ error: 'Gemini API key not configured' });
    }

    const { owner, repo } = req.body;
    if (!owner || !repo) {
      return res.status(400).json({ error: 'Owner and repo parameters required' });
    }

    const connector = new GitHubConnector(authToken);
    const kortanaAI = new KortanaAI(geminiApiKey);

    // Fetch repository data
    const [issues, pullRequests] = await Promise.all([
      connector.getIssues(owner, repo, 'open'),
      connector.getPullRequests(owner, repo, 'open'),
    ]);

    // Analyze with Kor'tana AI
    const analysis = await kortanaAI.analyzeRepository({
      issues,
      pullRequests,
      repoName: `${owner}/${repo}`,
    });

    res.json({
      repository: `${owner}/${repo}`,
      analysis,
      metadata: {
        issuesCount: issues.length,
        pullRequestsCount: pullRequests.length,
        analyzedAt: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error('Error analyzing repository:', error);
    res.status(500).json({ error: 'Failed to analyze repository' });
  }
});

export default router;
