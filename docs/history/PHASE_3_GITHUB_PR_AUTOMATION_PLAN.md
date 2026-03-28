# PHASE 3: GitHub PR Automation Implementation Plan

**Status**: READY FOR IMPLEMENTATION
**Target Autonomy**: 100% (Full Autonomous Evolution Loop)
**Prerequisite**: Phase 1-2 Complete ✅

---

## Overview

Phase 3 automates the GitHub PR lifecycle, enabling KOR'TANA to autonomously create, validate, and merge pull requests when evolution/ branches reach stable state.

---

## Implementation Scope

### 3.1 Auto-Create PR Endpoint

**Endpoint**: `POST /api/pr/create`
**Trigger**: When evolution/ branch passes all local tests
**Action**:

```bash
gh pr create \
  --base main \
  --head evolution/{branch_name} \
  --title "Autonomous Evolution: {task_type}" \
  --body "Auto-generated PR from autonomous remediation cycle"
```

**Implementation File**: `backend/src/kortana/routers/github_pr.py`
**Lines**: ~80 lines

### 3.2 Check CI Status Endpoint

**Endpoint**: `GET /api/pr/{pr_id}/ci-status`
**Action**: Poll GitHub Actions for build/test results
**Logic**:

- Track PR status every 30 seconds
- Fail fast if any check fails
- Escalate to HO if manual review needed

**Implementation File**: Same as 3.1
**Lines**: ~60 lines

### 3.3 Auto-Merge PR Endpoint

**Endpoint**: `POST /api/pr/{pr_id}/merge`
**Conditions**:

- All CI checks PASSING ✅
- No conflicts with base branch
- No manual review comments

**Command**:

```bash
gh pr merge {pr_id} \
  --auto \
  --squash \
  --delete-branch
```

**Implementation File**: Same as 3.1
**Lines**: ~50 lines

### 3.4 Autonomous Evolution Cycle Controller

**File**: `backend/src/kortana/routers/autonomous_evolution.py`
**Responsibility**: Orchestrate Phase 1-2-3 workflow
**Logic**:

1. Monitor evolution/ branches
2. Run Phase 1 classification
3. Execute Phase 2 task queue
4. If all pass → Trigger Phase 3 PR workflow
5. Auto-merge if CI passes
6. Report autonomy metrics

**Lines**: ~120 lines

---

## Integration Points

### With Phase 1-2

- Use existing `HumanOnlyProtocol.classify_task()` to determine PR urgency
- Leverage `TaskClassification.SELF_CORRECTION` to identify auto-mergeable PRs
- Hook into task_queue completion events

### With External Systems

- **GitHub CLI**: Execute `gh` commands for PR operations
- **GitHub API**: Fallback REST API for status polling
- **GitHub Actions**: Monitor CI workflow results

---

## Success Criteria

| Criterion | Requirement |
|-----------|-------------|
| Auto-create PR | PR created within 5 minutes of evolution/ branch passing tests |
| CI monitoring | Status polled every 30 seconds |
| Auto-merge | PR merged within 2 minutes of all CI passing |
| Error handling | Escalates to HO on merge conflicts or failed checks |
| Audit trail | All automation logged with timestamps and decisions |

---

## Implementation Sequence

### Step 1: Create GitHub PR Router (30 mins)

```python
# backend/src/kortana/routers/github_pr.py
from fastapi import APIRouter, HTTPException
from src.kortana.logger import get_logger

router = APIRouter(prefix="/api/pr", tags=["github-pr"])
logger = get_logger(__name__)

@router.post("/create")
async def create_pr(evolution_branch: str, task_type: str) -> dict:
    """Auto-create pull request from evolution/ branch"""
    # Implementation
    pass

@router.get("/{pr_id}/ci-status")
async def get_ci_status(pr_id: str) -> dict:
    """Check CI status for PR"""
    # Implementation
    pass

@router.post("/{pr_id}/merge")
async def merge_pr(pr_id: str) -> dict:
    """Auto-merge PR if all conditions met"""
    # Implementation
    pass
```

### Step 2: Integrate with Main Router (15 mins)

```python
# backend/src/kortana/main.py
from src.kortana.routers.github_pr import router as pr_router
app.include_router(pr_router)
```

### Step 3: Create Autonomous Evolution Controller (45 mins)

```python
# backend/src/kortana/routers/autonomous_evolution.py
# Orchestrates Phase 1-2-3 workflow
```

### Step 4: Update Task Queue to Trigger Phase 3 (20 mins)

```python
# backend/src/kortana/routers/task_queue.py
# When SELF_CORRECTION task completes → trigger PR workflow
```

### Step 5: Testing & Validation (60 mins)

- Unit tests for PR creation logic
- Integration tests for CI polling
- End-to-end test of full Phase 1-2-3 cycle

---

## Dependencies

```
PyPI Packages Needed:
- gh (GitHub CLI wrapper for Python) - already available via system
- httpx - for async HTTP to GitHub API - already installed

System Requirements:
- GitHub CLI (gh) installed and authenticated
- GITHUB_TOKEN environment variable set
- Write access to repository
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Accidental merge to main | Require all CI checks passing + no conflicts before auto-merge |
| Stale PR stuck in review | Manual HO step if PR pending >4 hours without CI resolution |
| Network failures | Retry logic with exponential backoff, escalate to HO after 3 failures |
| Concurrent PRs | Queue PR operations, lock advancement per branch |

---

## Expected Deliverables

After Phase 3 implementation:

- ✅ Autonomous PR creation
- ✅ Autonomous CI monitoring
- ✅ Autonomous PR merging
- ✅ 100% autonomous evolution loop (from code change → merged PR)
- ✅ Full audit trail of all autonomous decisions
- ✅ HO escalation for edge cases

---

## Autonomy Progression

```
Phase 1: Task Classification        40% autonomy
Phase 2: Task Queue Integration     60% autonomy
Phase 3: GitHub PR Automation     +40% = 100% AUTONOMY
         (Full Autonomous Evolution)
```

---

## Timeline Estimate

**Total Implementation Time**: ~3-4 hours

- Router creation: 30 mins
- Main integration: 15 mins
- Evolution controller: 45 mins
- Task queue update: 20 mins
- Testing: 60 mins
- Buffer: 30 mins

**Suggestion**: Execute Phase 3 immediately after Phase 1-2 deployment to achieve full autonomous evolution capability.

---

## Sign-Off

This plan bridges Phase 1-2 (current: 60% autonomy) to Phase 3 (target: 100% autonomy) with clear implementation steps, success criteria, and risk mitigation.

**Ready for Implementation**: ✅ YES
**Prerequisite Status**: ✅ Phase 1-2 COMPLETE AND OPERATIONAL
**Next Action**: Execution of Phase 3 implementation schedule
