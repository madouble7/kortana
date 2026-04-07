import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import simpleGit from 'simple-git';
import { Octokit } from '@octokit/rest';
import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { execSync } from 'node:child_process';

describe('E2E: Code Generation Pipeline', () => {
  let tempRepoPath: string;
  const git = simpleGit();
  const octokit = new Octokit({ auth: process.env.GITHUB_TOKEN });
  const branchName = `feat/gen-${Date.now()}`;

  beforeAll(async () => {
    tempRepoPath = await mkdtemp(join(tmpdir(), 'gen-test-'));
    // Initialize sandbox
    await git.clone(process.env.TEST_REPO_URL!, tempRepoPath);
    process.chdir(tempRepoPath);
    await git.addConfig('user.email', 'test@example.com');
    await git.addConfig('user.name', 'E2E Test Runner');
  });

  afterAll(async () => {
    // Cleanup: Close PR and delete branch if exists
    try {
      await git.push('origin', branchName, ['--delete']);
    } catch (e) { /* ignore cleanup errors */ }
    await rm(tempRepoPath, { recursive: true, force: true });
  });

  it('should generate code and open a PR successfully', async () => {
    // 1. Generate
    execSync('npm run generate:code -- --output ./src', { stdio: 'inherit' });

    // 2. Git Workflow
    await git.checkoutLocalBranch(branchName);
    await git.add('.');
    await git.commit('feat: auto-generated code');
    await git.push('origin', branchName);

    // 3. API Integration
    const { data: pr } = await octokit.pulls.create({
      owner: process.env.REPO_OWNER!,
      repo: process.env.REPO_NAME!,
      title: 'Auto-generated changes',
      head: branchName,
      base: 'main',
    });

    // 4. Assertions
    expect(pr.number).toBeDefined();
    expect(pr.title).toBe('Auto-generated changes');
  });
});