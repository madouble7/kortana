import { Octokit } from '@octokit/rest';

export interface GitHubIssue {
  number: number;
  title: string;
  state: string;
  html_url: string;
  user: {
    login: string;
  };
  created_at: string;
  updated_at: string;
  body: string | null;
}

export interface GitHubPullRequest {
  number: number;
  title: string;
  state: string;
  html_url: string;
  user: {
    login: string;
  };
  created_at: string;
  updated_at: string;
  body: string | null;
}

export interface GitHubRepo {
  name: string;
  full_name: string;
  description: string | null;
  html_url: string;
  stargazers_count: number;
  open_issues_count: number;
}

export class GitHubConnector {
  private octokit: Octokit;

  constructor(authToken: string) {
    this.octokit = new Octokit({
      auth: authToken,
    });
  }

  /**
   * Get authenticated user information
   */
  async getAuthenticatedUser() {
    try {
      const { data } = await this.octokit.users.getAuthenticated();
      return data;
    } catch (error) {
      throw new Error(`Failed to get authenticated user: ${error}`);
    }
  }

  /**
   * Get repository information
   */
  async getRepository(owner: string, repo: string): Promise<GitHubRepo> {
    try {
      const { data } = await this.octokit.repos.get({
        owner,
        repo,
      });
      return {
        name: data.name,
        full_name: data.full_name,
        description: data.description,
        html_url: data.html_url,
        stargazers_count: data.stargazers_count,
        open_issues_count: data.open_issues_count,
      };
    } catch (error) {
      throw new Error(`Failed to get repository: ${error}`);
    }
  }

  /**
   * Get issues for a repository
   */
  async getIssues(owner: string, repo: string, state: 'open' | 'closed' | 'all' = 'open'): Promise<GitHubIssue[]> {
    try {
      const { data } = await this.octokit.issues.listForRepo({
        owner,
        repo,
        state,
        per_page: 30,
      });
      
      // Filter out pull requests (GitHub API returns both)
      return data
        .filter((item) => !item.pull_request)
        .map((issue) => ({
          number: issue.number,
          title: issue.title,
          state: issue.state,
          html_url: issue.html_url,
          user: {
            login: issue.user?.login || 'unknown',
          },
          created_at: issue.created_at,
          updated_at: issue.updated_at,
          body: issue.body || null,
        }));
    } catch (error) {
      throw new Error(`Failed to get issues: ${error}`);
    }
  }

  /**
   * Get pull requests for a repository
   */
  async getPullRequests(owner: string, repo: string, state: 'open' | 'closed' | 'all' = 'open'): Promise<GitHubPullRequest[]> {
    try {
      const { data } = await this.octokit.pulls.list({
        owner,
        repo,
        state,
        per_page: 30,
      });
      
      return data.map((pr) => ({
        number: pr.number,
        title: pr.title,
        state: pr.state,
        html_url: pr.html_url,
        user: {
          login: pr.user?.login || 'unknown',
        },
        created_at: pr.created_at,
        updated_at: pr.updated_at,
        body: pr.body || null,
      }));
    } catch (error) {
      throw new Error(`Failed to get pull requests: ${error}`);
    }
  }

  /**
   * Get user's repositories
   */
  async getUserRepositories(username?: string) {
    try {
      if (username) {
        const { data } = await this.octokit.repos.listForUser({
          username,
          per_page: 30,
          sort: 'updated',
        });
        return data;
      } else {
        const { data } = await this.octokit.repos.listForAuthenticatedUser({
          per_page: 30,
          sort: 'updated',
        });
        return data;
      }
    } catch (error) {
      throw new Error(`Failed to get repositories: ${error}`);
    }
  }
}
