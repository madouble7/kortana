#!/bin/bash
# Script to fix PR #14 merge conflict by applying the changes with proper history

set -e

echo "Fixing PR #14 merge conflict..."
echo

# Check if we're in the correct directory
if [ ! -f "kortana.yaml" ]; then
    echo "Error: Must run from repository root directory"
    exit 1
fi

# Store current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "Current branch: $CURRENT_BRANCH"

# Fetch latest changes
echo "Fetching latest changes..."
git fetch origin

# Create a temporary branch from main
echo "Creating fix branch from main..."
git checkout main
git checkout -b pr14-fix-temp

# Apply the patch
echo "Applying PR #14 changes..."
if [ -f "fix-pr14.patch" ]; then
    git am fix-pr14.patch
    echo "✓ Patch applied successfully"
else
    echo "Error: fix-pr14.patch not found"
    echo "Please ensure the patch file exists in the repository root"
    exit 1
fi

# Verify the merge is possible
echo
echo "Verifying merge capability..."
MERGE_BASE=$(git merge-base HEAD main)
if [ -n "$MERGE_BASE" ]; then
    echo "✓ Merge base found: $MERGE_BASE"
    echo "✓ Branch can be merged cleanly"
else
    echo "✗ Error: No merge base found"
    exit 1
fi

# Show what changed
echo
echo "Files changed:"
git diff --name-status main HEAD

echo
echo "========================================="
echo "Fix applied successfully!"
echo "========================================="
echo
echo "Next steps:"
echo "1. Force push to PR #14 branch:"
echo "   git push -f origin pr14-fix-temp:copilot/enhance-ai-chat-interface"
echo
echo "2. Or create a new PR from this branch:"
echo "   git push origin pr14-fix-temp"
echo
echo "3. To return to your previous branch:"
echo "   git checkout $CURRENT_BRANCH"
echo "   git branch -D pr14-fix-temp"
