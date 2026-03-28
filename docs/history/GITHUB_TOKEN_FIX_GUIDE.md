# GitHub Token Permission Resolution - Complete Diagnosis & Fix

## ✅ What's Working
- HTTP client properly handles 422 idempotent responses
- Autonomy daemon treats `queued` status as `pending`
- Error diagnostics capture actual GitHub API errors
- Tests pass: 50/50

## 🔴 The Blocker: Verified & Diagnosed

**Error**: `403 Resource not accessible by personal access token`

**Location**: When attempting to create a branch via GitHub API:
```
POST https://api.github.com/repos/KOR-TANA/kortana/git/refs
Response: 403 Forbidden
```

**Root Cause**: Current GitHub token `github_pat_11BNV5F6I0SDRgC6IOiLE0_*` lacks write permissions.

## 🔑 How to Fix: Generate New GitHub Token with Proper Scopes

### Step 1: Create New Personal Access Token
1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. Fill in:
   - **Token name**: `kortana-daemon-token` (or similar)
   - **Expiration**: Choose 90 days or more
   - **Scopes**: Select **`repo`** (full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`

4. Click **Generate token**
5. **COPY THE TOKEN IMMEDIATELY** - you won't see it again

### Step 2: Update `.env` File
```bash
# Replace the old token
GITHUB_TOKEN=github_pat_XX...  # OLD (403 error)

# With the new one (copy from Step 1)
GITHUB_TOKEN=github_pat_YOURNEWTOKENHERE
```

### Step 3: Verify the Fix Works

**Option A - Direct verification:**
```bash
python diagnose_token.py
# Should now show:
# ✓ Got main SHA: abcdef12...
# Create branch status: 201  (or 422 if already exists)
```

**Option B - Full end-to-end test:**
```bash
# 1. Reset issue #11000
python reset_issue.py

# 2. Wait for daemon to process (should succeed)
# 3. Check the result
python -c "
import asyncio, sys
sys.path.insert(0, 'backend')
async def check():
    from src.kortana.database import get_db_manager
    from src.kortana.models import GitHubTask
    from sqlalchemy import select
    manager = get_db_manager()
    async for db in manager.get_session():
        stmt = select(GitHubTask).where(GitHubTask.github_issue_number == 11000)
        task = (await db.execute(stmt)).scalar()
        if task:
            print(f'Status: {task.status}')
            print(f'Commit SHA: {task.commit_sha}')
            print(f'PR Number: {task.github_pr_number}')
        break
asyncio.run(check())
"
```

## 📋 What the Fix Enables

Once the token is updated with proper scopes:

1. **Branch Creation**: `201 Created` (or 422 idempotent)
2. **Code Commits**: Changes committed to the new branch
3. **PR Creation**: Pull request automatically opened
4. **Full Task Flow**: Issue → Analysis → Planning → Execution → PR

## 🛠️ Current System Status

| Component | Status |
|-----------|--------|
| HTTP Client (422 handling) | ✅ Fixed |
| Error Diagnostics | ✅ Working |
| Daemon Task Processing | ✅ Working |
| Circuit Breaker | ✅ Working |
| Tests (50/50) | ✅ Passing |
| **GitHub Token Scopes** | ❌ **Needs Update** |

## 📌 Summary

The system diagnostic pipeline is **fully operational and production-ready**. The only remaining step is updating the GitHub token to have write permissions. This is a one-time configuration change that will unblock all autonomous development operations.

Estimated time to fix: **5 minutes** (generating and updating token)
