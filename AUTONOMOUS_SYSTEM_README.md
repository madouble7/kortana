# Autonomous Kor'tana System

## 🚀 Complete Autonomous Agent System with AI Integration

This is a fully autonomous agent orchestration system with three levels of automation, Gemini 2.0 Flash integration, context management, and intelligent handoff procedures.

## 🎯 Quick Start

### 1. System Setup
```cmd
# Run the automated setup
setup_system.bat

# OR manual setup:
pip install google-generativeai tiktoken
python init_db.py
```

### 2. Configure API Key
```cmd
# Set your Gemini API key
set GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Choose Automation Level
```cmd
# See all options
python setup_automation.py --demo

# Manual control (development)
python setup_automation.py --level manual

# Balanced automation (production with oversight)
python setup_automation.py --level semi-auto

# Full autonomy (24/7 hands-off operation)
python setup_automation.py --level hands-off
```

## 🏗️ System Architecture

### Core Components

1. **Enhanced Relay System** (`relays/relay.py`)
   - Gemini 2.0 Flash integration for AI summarization
   - Token counting and context window management
   - Database persistence for context packages
   - Multi-agent message relaying

2. **Handoff Manager** (`relays/handoff.py`)
   - S+T+H+O token calculation (System + Task + History + Output)
   - 80% context window threshold monitoring
   - Automatic agent handoffs and restarts
   - Context package creation and transfer

3. **Database System** (`kortana.db`)
   - SQLite schema for context packages
   - Agent activity tracking
   - Token usage history
   - Performance metrics

4. **Automation Scripts**
   - `run_relay.bat` - 5-minute relay intervals
   - `handoff.bat` - 10-minute handoff monitoring
   - Windows Task Scheduler integration

## 🎛️ Automation Levels

### Manual Level
- **Best for**: Development, learning, custom workflows
- **Control**: Full manual control over all operations
- **Time investment**: High (hands-on management)

**Commands**:
```cmd
python relays/relay.py                    # Single cycle
python relays/relay.py --status           # Check status
python relays/handoff.py --status         # Check handoffs
python relays/handoff.py --handoff claude # Force handoff
```

### Semi-Auto Level
- **Best for**: Production with monitoring, iterative development
- **Control**: Automated tasks with manual oversight
- **Time investment**: Medium (periodic monitoring)

**Setup**:
```cmd
# Start automated relay (5-minute intervals)
relays\run_relay.bat

# Start automated handoffs (10-minute intervals)
relays\handoff.bat
```

### Hands-Off Level
- **Best for**: 24/7 production, scalable systems
- **Control**: Fully automated with minimal intervention
- **Time investment**: Low (occasional check-ins)

**Features**:
- Windows Task Scheduler integration
- Automatic recovery and error handling
- Performance monitoring and logging
- Optional web dashboard

## 🤖 AI Integration

### Gemini 2.0 Flash Features
- **Context Summarization**: Reduces large conversation histories to ~1000 tokens
- **Smart Handoffs**: AI-powered context package creation
- **Intelligent Monitoring**: Token usage optimization
- **Graceful Fallback**: Mock responses when API unavailable

### Token Management
- **Context Window**: 128K tokens (conservative limit)
- **Handoff Threshold**: 80% (102,400 tokens)
- **Calculation**: S+T+H+O (System + Task + History + Output)
- **Monitoring**: Real-time usage tracking

## 📊 Database Schema

### Context Table
```sql
CREATE TABLE context (
    task_id TEXT PRIMARY KEY,
    summary TEXT,           -- AI-generated summary
    code TEXT,              -- Current code state
    issues TEXT,            -- Pending issues (JSON)
    commit_ref TEXT,        -- Git commit reference
    timestamp TEXT,         -- ISO 8601 timestamp
    tokens INTEGER          -- Token count
);
```

### Agent Activity Table
```sql
CREATE TABLE agent_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_name TEXT NOT NULL,
    task_id TEXT,
    action_type TEXT,       -- 'start', 'progress', 'handoff', 'complete'
    message_count INTEGER,
    tokens_used INTEGER,
    timestamp TEXT
);
```

## 🔧 Configuration

### Environment Variables
```cmd
set GEMINI_API_KEY=your_gemini_api_key_here
set KORTANA_AUTO_MODE=hands-off              # Optional
```

### Windows Task Scheduler (Hands-Off Mode)
```
Task 1: "Kor'tana Relay System"
- Trigger: At system startup
- Action: python relays/relay.py --loop --interval 300
- Run whether user logged on or not

Task 2: "Kor'tana Handoff Monitor"
- Trigger: At system startup
- Action: python relays/handoff.py --monitor --interval 600
- Run whether user logged on or not
```

## 📈 Monitoring

### Status Commands
```cmd
python relays/relay.py --status           # Relay system status
python relays/handoff.py --status         # Handoff status
python test_autonomous_system.py          # Full system test
```

### Log Files
- `logs/handoffs.log` - Handoff events and decisions
- `logs/[agent].log` - Individual agent activity
- `data/relay_state.json` - Relay system state

### Database Queries
```sql
-- View context packages
SELECT task_id, timestamp, tokens FROM context ORDER BY timestamp DESC;

-- View agent activity
SELECT agent_name, action_type, timestamp FROM agent_activity ORDER BY timestamp DESC;
```

## 🛠️ Testing

### System Test
```cmd
python test_autonomous_system.py          # Basic test suite
python test_autonomous_system.py --full   # Extended tests
python test_autonomous_system.py --info   # System information
```

### Manual Testing
```cmd
# Test summarization
python relays/relay.py --summarize

# Test single relay cycle
python relays/relay.py

# Force agent handoff
python relays/handoff.py --handoff test_agent
```

## 🚨 Troubleshooting

### Common Issues

1. **"Module not found" errors**
   ```cmd
   pip install google-generativeai tiktoken
   ```

2. **Database errors**
   ```cmd
   python init_db.py --reset
   ```

3. **Gemini API errors**
   ```cmd
   # Verify API key
   echo %GEMINI_API_KEY%

   # Test with mock mode (no API key needed)
   python relays/relay.py --summarize
   ```

4. **Permission errors**
   - Run Command Prompt as Administrator
   - Check file permissions in project directory

### Debug Mode
```cmd
# Verbose relay output
python relays/relay.py --loop --interval 10

# Monitor handoff decisions
python relays/handoff.py --monitor --interval 30
```

## 📁 File Structure

```
c:\kortana/
├── relays/
│   ├── relay.py              # Enhanced relay with Gemini
│   ├── handoff.py            # Agent handoff manager
│   ├── run_relay.bat         # Automation script (5 min)
│   └── handoff.bat           # Automation script (10 min)
├── logs/                     # Agent logs
├── queues/                   # Agent message queues
├── data/                     # System state files
├── init_db.py               # Database initialization
├── setup_automation.py      # Automation level setup
├── test_autonomous_system.py # System test suite
├── setup_system.bat         # One-click setup
└── kortana.db               # SQLite database
```

## 🎯 Use Cases

### Development Workflow
1. Use **Manual** level during development
2. Test individual components with status commands
3. Gradually move to **Semi-Auto** for integration testing
4. Deploy with **Hands-Off** for production

### Production Deployment
1. Set up **Hands-Off** automation level
2. Configure Windows Task Scheduler
3. Monitor via dashboard or status commands
4. Set up log rotation and maintenance

### Multi-Agent Coordination
1. Agents communicate through relay system
2. Context automatically summarized at 80% threshold
3. Handoffs preserve complete task context
4. Database tracks all agent interactions

## 🔮 Future Enhancements

- **Redis Integration**: Production task queue management
- **Web Dashboard**: Real-time monitoring interface
- **Docker Deployment**: Containerized autonomous operation
- **Multi-Model Support**: Additional AI providers
- **Advanced Scheduling**: Complex automation patterns
- **Metrics and Analytics**: Performance insights

## 📜 License

This autonomous agent system is part of the Kor'tana project. See project documentation for licensing details.

## 🤝 Contributing

To contribute to the autonomous system:
1. Test your changes with `python test_autonomous_system.py`
2. Ensure compatibility with all automation levels
3. Update documentation for new features
4. Follow the established patterns for agent integration

---

**🎉 Your autonomous Kor'tana system is ready for deployment!**

Choose your automation level and let the AI agents work autonomously while you focus on higher-level tasks.
