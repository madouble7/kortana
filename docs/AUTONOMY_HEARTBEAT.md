# Kor'tana Autonomy Heartbeat System

## Overview

The Kor'tana Autonomy Heartbeat System ensures continuous monitoring of the autonomous agent's operations. It provides automated detection, recovery, and alerting for missing heartbeats.

## Architecture

### Components

1. **Daily Sync Script** (`scripts/deployment/daily_sync.py`)
   - Generates heartbeat logs daily at 6 AM UTC
   - Creates logs in `logs/autonomy/` directory
   - Captures system status, git activity, and deployment info

2. **Autonomy Heartbeat Workflow** (`.github/workflows/autonomy-heartbeat.yml`)
   - Runs every 6 hours to check for recent logs
   - Detects missing heartbeats (no logs in last 24 hours)
   - Performs automated recovery when possible
   - Creates/closes GitHub issues for alerts

3. **Daily Sync Workflow** (`.github/workflows/daily-sync.yml`)
   - Runs daily to generate heartbeat logs
   - Commits logs to the repository
   - Uses standard GitHub token (no custom secrets needed)

## How It Works

### Normal Operation

1. **Daily Sync Workflow** runs at 6 AM UTC
2. Executes `daily_sync.py` to generate heartbeat log
3. Commits log to `logs/autonomy/[date].md`
4. Updates `logs/autonomy/latest.md` for quick access

### Heartbeat Detection

1. **Autonomy Heartbeat Workflow** runs every 6 hours
2. Checks for files in `logs/autonomy/` modified in last 24 hours
3. If recent logs exist: ✅ Heartbeat is healthy
4. If no recent logs: ⚠️ Heartbeat is missing

### Automated Recovery

When a missing heartbeat is detected:

1. **Create Alert**: Opens GitHub issue #14 (if not already open)
2. **Attempt Recovery**: Runs `daily_sync.py` to generate heartbeat
3. **Verify Recovery**: Checks if `logs/autonomy/latest.md` exists
4. **Commit & Close**: If successful, commits log and closes alert

### Alert Management

- **When heartbeat is missing**: Creates issue with `autonomy-alert` and `critical` labels
- **When heartbeat is restored**: Automatically closes all open heartbeat issues
- **Prevents duplicates**: Only creates one alert issue at a time

## Log Format

Heartbeat logs contain:

```markdown
# Kor'tana Autonomy Heartbeat - [date]

**Timestamp**: [ISO 8601 timestamp]
**Status**: ✅ ALIVE

## Heartbeat Status
- **Autonomous Mode**: ENABLED
- **Last Check**: [timestamp]
- **Backend**: [online/offline]
- **Current Branch**: [branch name]
- **Uncommitted Changes**: [Yes/No]

## Activity
- **Commits Today**: [count]
- **Last Deployment**: [info]

## Metrics
[JSON with detailed metrics]

## Autonomy Protocol
Kor'tana autonomous heartbeat confirmed. All systems operational.
```

## Testing

Run the test script to verify the heartbeat system:

```bash
./scripts/test_heartbeat.sh
```

Tests performed:
1. ✅ Check `logs/autonomy/` directory exists
2. ✅ Run `daily_sync.py` successfully
3. ✅ Verify recent logs are created
4. ✅ Check `latest.md` exists
5. ✅ Validate log content format

## Monitoring

### Check Heartbeat Status

```bash
# Check for recent logs (last 24 hours)
find logs/autonomy -type f -mtime -1

# View latest heartbeat
cat logs/autonomy/latest.md
```

### Manually Trigger Workflows

```bash
# Trigger daily sync
gh workflow run daily-sync.yml

# Trigger heartbeat check
gh workflow run autonomy-heartbeat.yml
```

### View Workflow Runs

- Daily Sync: https://github.com/KOR-TANA/kortana/actions/workflows/daily-sync.yml
- Heartbeat Check: https://github.com/KOR-TANA/kortana/actions/workflows/autonomy-heartbeat.yml

## Troubleshooting

### Issue: Daily sync workflow failing

**Symptom**: No new logs in `logs/autonomy/`

**Solutions**:
1. Check workflow permissions have `contents: write`
2. Verify Python 3.11 is available
3. Check for script errors in workflow logs

### Issue: Heartbeat check not detecting logs

**Symptom**: False alerts despite logs existing

**Solutions**:
1. Verify logs are committed to repository
2. Check file modification times with `ls -lh logs/autonomy/`
3. Ensure logs are not in `.gitignore`

### Issue: Automated recovery failing

**Symptom**: Alert stays open despite recovery attempts

**Solutions**:
1. Check workflow has `contents: write` permission
2. Verify Python setup step runs before recovery
3. Check for script execution errors in logs

## Configuration

### Schedule Times

- **Daily Sync**: `0 6 * * *` (6 AM UTC daily)
- **Heartbeat Check**: `0 */6 * * *` (Every 6 hours)

To modify, edit the `cron` expressions in workflow files.

### Detection Window

Current detection window: **24 hours**

To change, modify the `-mtime -1` parameter in the heartbeat check step.

## Security

- Uses standard `GITHUB_TOKEN` (no custom secrets needed)
- Requires minimal permissions: `contents: write`, `issues: write`
- Logs contain no sensitive information
- All operations are read-only except log commits

## Maintenance

### Regular Tasks

- Monitor workflow success rates
- Review heartbeat alerts for patterns
- Update documentation as system evolves

### When to Intervene

Manual intervention needed when:
- Automated recovery fails repeatedly
- Workflow permissions are insufficient
- GitHub Actions service is down

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Kor'tana Architecture](README.md)
- [Human Only Protocol](KOR_TANA_AUTONOMOUS_PROTOCOL.md)
