# 🤖 Kor'tana Discord Bot Deployment Guide

## Quick Start

### Option 1: Windows Batch File (Easiest)
```bash
deploy_discord_bot.bat
```
This will:
- Check dependencies
- Set up Python environment
- Create .env file
- Start deployment checklist
- Launch bot

### Option 2: Python Deployment Script
```bash
python deploy_discord_bot.py
```
Full automated deployment with comprehensive checks.

### Option 3: Direct Start
```bash
python start_discord_bot.py
```
Simple bot startup (requires manual setup).

---

## ✅ Prerequisites

### 1. Discord Developer Setup
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and name it "Kor'tana"
3. Go to the "Bot" section
4. Click "Add Bot"
5. Under "TOKEN", click "Copy" to get your bot token
6. Enable "Message Content Intent" under Privileged Gateway Intents

### 2. Bot Permissions
The bot needs these permissions:
- View Channels
- Send Messages
- Read Message History
- Use Slash Commands
- Embed Links

**To set up permissions:**
1. In Developer Portal, go to "OAuth2" → "URL Generator"
2. Select scopes: `bot`
3. Select permissions:
   - Send Messages
   - Read Messages/View Channels
   - Read Message History
   - Embed Links
4. Copy the generated URL
5. Open it in browser to invite bot to your server

### 3. Environment Setup
Create a `.env` file in the project root:

```env
DISCORD_BOT_TOKEN=your_token_here
OPENAI_API_KEY=your_key_here  # Optional
KORTANA_MODE=default
LOG_LEVEL=INFO
```

You can copy from `.env.example`:
```bash
cp .env.example .env
```

---

## 📦 Required Packages

### Automatic Installation
Run the deployment script - it installs everything:
```bash
python deploy_discord_bot.py
```

### Manual Installation
```bash
pip install discord.py python-dotenv openai pydantic pyyaml apscheduler
```

### Verify Installation
```bash
python -c "import discord; print(f'discord.py {discord.__version__}')"
```

---

## 🚀 Starting the Bot

### Method 1: Deployment Script (Recommended)
```bash
python deploy_discord_bot.py
```
Includes full checks and validation.

### Method 2: Startup Script
```bash
python start_discord_bot.py
```
Simple startup with basic checks.

### Method 3: Direct Python
```bash
python src/discord_bot.py
```
Direct execution (requires manual error handling).

### Method 4: With Virtual Environment
```bash
# Activate virtual environment
.kortana_config_test_env\Scripts\activate.bat  # Windows
source .kortana_config_test_env/bin/activate  # Linux/Mac

# Start bot
python start_discord_bot.py
```

---

## 🔧 Configuration

### .env File Template
```env
# Required
DISCORD_BOT_TOKEN=your_token_here

# Optional - for enhanced AI
OPENAI_API_KEY=your_key_here

# Mode Selection
KORTANA_MODE=default  # or: autonomous, fire, whisper

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR

# LLM Settings
DEFAULT_LLM_PROVIDER=openai
LLM_MODEL=gpt-4
LLM_TEMPERATURE=0.7
```

### Mode Descriptions
- **default**: Standard conversational mode
- **autonomous**: Bot takes initiative with suggestions
- **fire**: Direct, concise responses
- **whisper**: Gentle, empathetic responses

---

## 📝 Bot Commands

Once the bot is running and invited to your server, use these commands:

### Slash Commands
```
/kortana [message]    - Chat with Kor'tana
/ping                 - Check bot status
/help                 - Show help and available commands
```

### Mention-Based
```
@Kor'tana hello       - Reply to mentions
```

### Text Commands (Legacy)
```
!kortana [message]    - Text command version
```

---

## 🐛 Troubleshooting

### Error: "discord.py not installed"
```bash
pip install discord.py
```

### Error: "DISCORD_BOT_TOKEN not found"
1. Create `.env` file in project root
2. Add: `DISCORD_BOT_TOKEN=your_token_here`
3. Restart bot

### Error: "Invalid Discord bot token"
1. Go to Discord Developer Portal
2. Regenerate the token
3. Update .env file
4. Restart bot

### Error: "Bot doesn't respond"
1. Verify bot is online in Discord
2. Check that bot has message permissions
3. Ensure "Message Content Intent" is enabled
4. Check logs for errors

### Bot disconnects frequently
1. Check internet connection
2. Verify Discord API status: https://discordstatus.com
3. Increase timeout settings if needed
4. Check for API rate limiting

### Missing messages or commands
1. Ensure "Message Content Intent" is enabled in Developer Portal
2. Check that bot has proper permissions in channel
3. Verify bot role is positioned above other roles (for moderation)

---

## 📊 Features

### Core Functionality
- ✅ Real-time chat responses
- ✅ Slash commands and mentions
- ✅ Multiple conversation modes
- ✅ Memory integration
- ✅ Error handling and recovery

### Advanced Features
- ✅ Conversation history
- ✅ User context tracking
- ✅ Server-specific settings
- ✅ Autonomous suggestions
- ✅ Covenant-based safety

---

## 🔒 Security Notes

1. **Never commit .env file** - Add to .gitignore:
   ```
   .env
   *.env
   .env.*
   ```

2. **Rotate tokens regularly**:
   - Go to Developer Portal
   - Click "Regenerate" under bot token
   - Update .env file

3. **Use specific permissions** - Give bot only needed permissions

4. **Monitor bot usage** - Check Discord audit logs regularly

---

## 📈 Monitoring

### Check Bot Status
```bash
# From Discord
/ping            # Shows latency
```

### View Logs
Logs are displayed in console when bot is running.

### Monitor Memory Usage
Bot will log memory stats periodically.

---

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| Bot won't start | Check .env file, verify token, check Python version |
| No responses | Enable Message Content Intent, check permissions |
| Slow responses | Check API quotas, verify internet connection |
| Bot offline | Check token validity, verify server connection |
| Permission errors | Adjust bot role position, grant permissions |

---

## 📚 File Structure

```
kortana/
├── src/
│   ├── discord_bot.py           # Main bot implementation
│   ├── dev_chat_simple.py       # Chat interface
│   └── kortana/
│       ├── brain.py             # Core chat engine
│       └── ...
├── discord/
│   ├── bot.py                   # Discord bot module
│   └── config.md                # Discord configuration
├── deploy_discord_bot.py        # Deployment script
├── deploy_discord_bot.bat       # Windows deployment
├── start_discord_bot.py         # Startup script
├── .env.example                 # Configuration template
└── .env                         # Your configuration (create this)
```

---

## 🧪 Testing

### Test Bot Connection
```python
python -c "import discord; print('✅ discord.py working')"
```

### Test Configuration
```bash
python deploy_discord_bot.py
```
Runs full validation suite.

### Manual Test
1. Start bot: `python start_discord_bot.py`
2. Go to Discord server with bot
3. Type `/kortana hello`
4. Bot should respond

---

## ⚙️ Advanced Options

### Environment Variables
Set via .env or system:
```bash
# Windows
set PYTHON_UNBUFFERED=1
python start_discord_bot.py

# Linux
export PYTHONUNBUFFERED=1
python start_discord_bot.py
```

### Debug Mode
```bash
# In .env
LOG_LEVEL=DEBUG
```

### Custom Intents
Edit src/discord_bot.py line 24-26:
```python
intents = discord.Intents.default()
intents.message_content = True  # Required for message reading
```

---

## 🎯 Next Steps

1. **Deploy Bot**:
   ```bash
   python deploy_discord_bot.py
   ```

2. **Verify in Discord**:
   - Check bot is online
   - Run `/ping` command
   - Run `/kortana hello`

3. **Monitor Performance**:
   - Check response times
   - Monitor error logs
   - Keep API quotas in check

4. **Customize (Optional)**:
   - Adjust conversation mode
   - Configure LLM settings
   - Add custom commands

---

## 📞 Support

If you encounter issues:
1. Check logs for error messages
2. Verify all prerequisites are met
3. Check [Discord.py Documentation](https://discordpy.readthedocs.io)
4. Review this guide's troubleshooting section

---

**Last Updated:** February 8, 2026  
**Bot Status:** ✅ Ready for Deployment  
**Version:** Kor'tana Discord Integration v1.0
