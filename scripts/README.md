# Kor'tana Scripts

Utility scripts for setup, deployment, testing, and maintenance of the Kor'tana system.

## 📁 Organization

```
scripts/
├── setup/                    # Environment setup and initialization
│   └── setup-environment.py  # Install dependencies and configure environment
├── deployment/               # Deployment and continuous operations
│   ├── daily_sync.py         # Daily repository synchronization
│   ├── update_covenant.py    # Update governance/covenant files
│   └── unseal-kortana.js     # Unsealing/unlocking system operations
└── testing/                  # Testing and validation
    ├── test-backend-endpoints.py   # Test backend API endpoints
    └── test-bot-token.py           # Validate bot authentication tokens
```

## 🛠️ Setup Scripts

### setup-environment.py

Initializes the development environment with all dependencies.

**Usage:**

```bash
python scripts/setup/setup-environment.py
```

**What it does:**

- Installs backend Python dependencies
- Installs frontend Node.js dependencies
- Creates environment configuration files
- Validates GCP and GitHub credentials
- Sets up pre-commit hooks (if configured)

**Requirements:**

- Python 3.9+
- Node.js 16+
- git

---

## 🚀 Deployment Scripts

### daily_sync.py

Synchronizes the repository with the Kor'tana constellation daily.

**Usage:**

```bash
python scripts/deployment/daily_sync.py
```

**Features:**

- Pulls latest changes from main branch
- Syncs code to cloud deployment
- Updates memory system with new commits
- Validates deployment health
- Logs synchronization results

**Configuration:**

- Runs on schedule (cron job recommended)
- Requires GitHub token in environment
- Requires GCP credentials

### update_covenant.py

Updates governance and covenant documents based on system state.

**Usage:**

```bash
python scripts/deployment/update_covenant.py
```

**Actions:**

- Updates COVENANT_INDEX.md
- Records system decisions
- Generates compliance reports
- Maintains governance audit trail

**Environment Variables:**

- `GITHUB_TOKEN` - GitHub API access
- `GCP_PROJECT_ID` - Google Cloud project

### unseal-kortana.js

Administrative script for unsealing/unlocking system operations.

**Usage:**

```bash
node scripts/deployment/unseal-kortana.js
```

**Operations:**

- Unlock autonomous operations
- Reset system locks
- Emergency procedures
- Validate ritual/covenant requirements

**⚠️ Security**: Requires elevated permissions and validation.

---

## 🧪 Testing Scripts

### test-backend-endpoints.py

Validates all backend API endpoints are responding correctly.

**Usage:**

```bash
python scripts/testing/test-backend-endpoints.py
```

**Tests:**

- Health check endpoint
- Gemini API integration
- Memory system endpoints
- Agent orchestration endpoints
- GitHub integration endpoints
- Autonomy system status
- Task queue functionality

**Output:**

- Summary of all endpoint status codes
- Response time metrics
- Error details for failed tests

### test-bot-token.py

Validates GitHub bot/authentication tokens.

**Usage:**

```bash
python scripts/testing/test-bot-token.py
```

**Validation:**

- Token validity and expiration
- Required permissions/scopes
- GitHub API rate limits
- Bot account status

**Environment Variables:**

- `GITHUB_TOKEN` - GitHub personal access token
- `BOT_GITHUB_TOKEN` - Bot account token (optional)

---

## 📋 Running Scripts

### Manual Execution

```bash
# From project root
python scripts/setup/setup-environment.py
python scripts/testing/test-backend-endpoints.py
```

### Automated Scheduling

#### Linux/macOS (crontab)

```bash
# Daily sync at 2 AM
0 2 * * * cd /path/to/kortana && python scripts/deployment/daily_sync.py

# Update covenant daily at 3 AM
0 3 * * * cd /path/to/kortana && python scripts/deployment/update_covenant.py
```

#### Windows (Task Scheduler)

```powershell
# Create scheduled task for daily sync
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts/deployment/daily_sync.py" -WorkingDirectory "C:\KOR-TANA\kortana"
Register-ScheduledTask -TaskName "Kortana Daily Sync" -Trigger $trigger -Action $action
```

---

## 🔐 Environment Setup

Before running scripts, ensure these environment variables are set:

```bash
# GitHub
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export GITHUB_OWNER=KOR-TANA
export GITHUB_REPO=kortana

# Google Cloud
export GOOGLE_PROJECT_ID=your-project-id
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
export GEMINI_API_KEY=your-gemini-key

# System
export ENVIRONMENT=development  # or production
```

---

## 📊 Monitoring

Scripts produce logs in:

- `scripts/logs/` directory (if configured)
- Console output during execution
- GitHub Actions logs (for CI/CD runs)

Recommended monitoring setup:

```bash
# Watch script execution
tail -f scripts/logs/daily_sync.log

# Monitor deployment health
python scripts/testing/test-backend-endpoints.py
```

---

## 🐛 Troubleshooting

### Script Fails to Run

```bash
# Check permissions
chmod +x scripts/setup/*.py
chmod +x scripts/deployment/*.py
chmod +x scripts/testing/*.py

# Verify Python version
python --version  # Should be 3.9+
```

### Authentication Errors

```bash
# Verify tokens are set
echo $GITHUB_TOKEN
echo $GEMINI_API_KEY

# Test GitHub access
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

### Backend Not Responding

```bash
# Check if backend is running
curl http://localhost:8000/api/health

# Check backend logs
cd backend && tail -f logs/app.log
```

---

## 📝 Contributing

To add new scripts:

1. Place in appropriate subdirectory (`setup/`, `deployment/`, or `testing/`)
2. Add usage documentation in this README
3. Include error handling and logging
4. Validate all environment variables
5. Test before committing

---

**The mechanisms that sustain the constellation.**
