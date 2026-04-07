#!/bin/bash
# Test script to verify autonomy heartbeat system

set -e

echo "🔍 Testing Kor'tana Autonomy Heartbeat System"
echo "=============================================="
echo ""

# Test 1: Check if logs/autonomy directory exists
echo "Test 1: Checking logs/autonomy directory..."
if [ -d "logs/autonomy" ]; then
    echo "✅ Directory exists"
else
    echo "❌ Directory missing"
    exit 1
fi

# Test 2: Run daily_sync.py
echo ""
echo "Test 2: Running daily_sync.py..."
python scripts/deployment/daily_sync.py
if [ $? -eq 0 ]; then
    echo "✅ Script executed successfully"
else
    echo "❌ Script failed"
    exit 1
fi

# Test 3: Check for recent logs (modified in last 24 hours)
echo ""
echo "Test 3: Checking for recent autonomy logs..."
RECENT_LOGS=$(find logs/autonomy -type f -mtime -1 2>/dev/null | wc -l)
if [ "$RECENT_LOGS" -gt 0 ]; then
    echo "✅ Found $RECENT_LOGS recent logs"
else
    echo "❌ No recent logs found"
    exit 1
fi

# Test 4: Verify latest.md exists
echo ""
echo "Test 4: Checking latest.md..."
if [ -f "logs/autonomy/latest.md" ]; then
    echo "✅ latest.md exists"
else
    echo "❌ latest.md missing"
    exit 1
fi

# Test 5: Verify log content
echo ""
echo "Test 5: Verifying log content..."
if grep -q "ALIVE" logs/autonomy/latest.md && grep -q "Heartbeat Status" logs/autonomy/latest.md; then
    echo "✅ Log content is valid"
else
    echo "❌ Log content is invalid"
    exit 1
fi

echo ""
echo "=============================================="
echo "✅ All heartbeat tests passed!"
echo "=============================================="
