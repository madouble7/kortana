import { GoogleGenerativeAI } from '@google/generative-ai';
import { GitHubIssue, GitHubPullRequest } from './GitHubConnector';

export class KortanaAI {
  private genAI: GoogleGenerativeAI;
  private model: any;

  constructor(apiKey: string) {
    this.genAI = new GoogleGenerativeAI(apiKey);
    this.model = this.genAI.getGenerativeModel({ model: 'gemini-pro' });
  }

  /**
   * Analyze GitHub issues using Gemini AI
   */
  async analyzeIssues(issues: GitHubIssue[]): Promise<string> {
    try {
      const issuesSummary = issues.map((issue, idx) => 
        `${idx + 1}. Issue #${issue.number}: ${issue.title}\n   State: ${issue.state}\n   Created: ${new Date(issue.created_at).toLocaleDateString()}\n   Body: ${issue.body?.substring(0, 200) || 'No description'}...`
      ).join('\n\n');

      const prompt = `As Kor'tana, an AI assistant, analyze these GitHub issues and provide insights:

${issuesSummary}

Please provide:
1. A summary of the main themes or patterns
2. Priority suggestions based on issue content
3. Any potential correlations or dependencies between issues
4. Recommendations for the development team

Keep your analysis concise and actionable.`;

      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Failed to analyze issues: ${error}`);
    }
  }

  /**
   * Analyze GitHub pull requests using Gemini AI
   */
  async analyzePullRequests(pullRequests: GitHubPullRequest[]): Promise<string> {
    try {
      const prsSummary = pullRequests.map((pr, idx) => 
        `${idx + 1}. PR #${pr.number}: ${pr.title}\n   State: ${pr.state}\n   Created: ${new Date(pr.created_at).toLocaleDateString()}\n   Author: ${pr.user.login}\n   Body: ${pr.body?.substring(0, 200) || 'No description'}...`
      ).join('\n\n');

      const prompt = `As Kor'tana, an AI assistant, analyze these GitHub pull requests and provide insights:

${prsSummary}

Please provide:
1. Overview of the types of changes being proposed
2. Potential risks or areas needing attention
3. Review priority recommendations
4. Any patterns in the contribution workflow

Keep your analysis concise and actionable.`;

      const result = await this.model.generateContent(prompt);
      const response = await result.response;
      return response.text();
    } catch (error) {
      throw new Error(`Failed to analyze pull requests: ${error}`);
    }
  }

  /**
   * Generate a comprehensive repository analysis
   */
  async analyzeRepository(repoData: {
    issues: GitHubIssue[];
    pullRequests: GitHubPullRequest[];
    repoName: string;
  }): Promise<{
    issuesAnalysis: string;
    pullRequestsAnalysis: string;
    overallInsights: string;
  }> {
    try {
      const issuesAnalysis = await this.analyzeIssues(repoData.issues);
      const pullRequestsAnalysis = await this.analyzePullRequests(repoData.pullRequests);

      const overallPrompt = `As Kor'tana, provide overall insights for the repository "${repoData.repoName}":
- Total open issues: ${repoData.issues.length}
- Total pull requests: ${repoData.pullRequests.length}

Based on this data, what is the current health and activity level of this repository? Provide 2-3 key recommendations.`;

      const result = await this.model.generateContent(overallPrompt);
      const response = await result.response;
      const overallInsights = response.text();

      return {
        issuesAnalysis,
        pullRequestsAnalysis,
        overallInsights,
      };
    } catch (error) {
      throw new Error(`Failed to analyze repository: ${error}`);
    }
  }
}
