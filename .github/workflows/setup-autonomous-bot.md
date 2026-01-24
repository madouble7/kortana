# GitHub Autonomous Bot Setup Guide

## Overview
The Kor'tana autonomous workflows require a GitHub bot token to perform actions like:
- Pushing commits to update COVENANT_INDEX.md
- Merging pull requests autonomously
- Creating and managing branches
- Running daily sync operations

## Step 1: Create GitHub Bot Account

1. **Create a new GitHub account** specifically for autonomous operations:
   - Username: `kortana-autonomous[bot]` (or similar)
   - Email: Use a dedicated email for bot operations
   - Add to repository as collaborator with write access

2. **Generate Personal Access Token**:
   - Go to Settings → Developer settings → Personal access tokens → Tokens (classic)
   - Click "Generate new token (classic)"
   - Name: `Kor'tana Autonomous Operations`
   - Expiration: Never (or set to 1 year)
   - Select scopes:
     - ✅ `repo` (Full control of private repositories)
     - ✅ `workflow` (Update GitHub Action workflows)
     - ✅ `read:org` (Read org and team membership)
     - ✅ `write:repo_hook` (Write repository hooks)

## Step 2: Add Token to GitHub Secrets

1. **Navigate to repository Settings** → Secrets and variables → Actions
2. **Add new repository secret**:
   - Name: `KORTANA_AUTONOMOUS_TOKEN`
   - Value: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (the PAT you just created)

## Step 3: Verify Bot Permissions

The bot account needs to be added to the repository with appropriate permissions:

1. **Repository Settings** → Collaborators and teams
2. **Add collaborator**: `kortana-autonomous[bot]`
3. **Assign role**: `Write` (or `Maintain` for more permissions)

## Step 4: Test Bot Functionality

Create a test commit to verify the bot works:

```bash
# Test the bot token works
curl -H "Authorization: token YOUR_BOT_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/repos/KOR-TANA/kortana/issues
```

## Security Notes

- **Never commit the token** to version control
- **Rotate tokens regularly** (every 6-12 months)
- **Monitor bot activity** in repository audit logs
- **Use dedicated bot account** (not personal account)

## Troubleshooting

**Workflow fails with authentication error:**
- Check token hasn't expired
- Verify token has correct scopes
- Confirm bot is repository collaborator

**Permission denied on push/merge:**
- Ensure bot has write access to repository
- Check branch protection rules allow bot operations
- Verify token includes `repo` scope

---

*Once the bot token is configured, the autonomous workflows will be able to execute all scheduled operations.*
