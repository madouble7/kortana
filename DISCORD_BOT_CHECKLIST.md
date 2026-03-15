# 🤖 Kor'tana Discord Bot - Pre-Deployment Checklist

Use this checklist to ensure everything is ready before deploying the bot to production.

---

## 📋 Pre-Deployment Checklist

### Phase 1: Discord Setup ✓
- [ ] Discord account created
- [ ] Developer Portal access enabled
- [ ] New Application "Kor'tana" created
- [ ] Bot added to the application
- [ ] Bot token copied securely
- [ ] Message Content Intent enabled
- [ ] Bot invited to test/production server

### Phase 2: Environment Setup ✓
- [ ] `.env` file created in project root
- [ ] `DISCORD_BOT_TOKEN` added to `.env`
- [ ] Token format validated (should contain dots)
- [ ] OPENAI_API_KEY added (optional)
- [ ] .env file is in .gitignore
- [ ] .env file permissions restricted (readable by bot only)

### Phase 3: Python Environment ✓
- [ ] Python 3.10+ installed
- [ ] Virtual environment created (`.kortana_config_test_env`)
- [ ] Virtual environment activated
- [ ] pip upgraded to latest version
- [ ] discord.py installed (v2.0+)
- [ ] Other dependencies installed:
  - [ ] python-dotenv
  - [ ] openai
  - [ ] pydantic
  - [ ] pyyaml
  - [ ] apscheduler

### Phase 4: Code Validation ✓
- [ ] `src/discord_bot.py` exists and is valid
- [ ] `src/kortana/brain.py` exists (for enhanced responses)
- [ ] All imports resolve correctly
- [ ] No syntax errors in bot code
- [ ] Configuration schema loads properly

### Phase 5: Configuration ✓
- [ ] Deployment script created: `deploy_discord_bot.py`
- [ ] Startup script created: `start_discord_bot.py`
- [ ] Windows batch file created: `deploy_discord_bot.bat`
- [ ] Configuration template exists: `.env.example`
- [ ] Documentation complete: `DISCORD_BOT_DEPLOYMENT.md`
- [ ] Validator script exists: `validate_discord_bot.py`

### Phase 6: Testing ✓
- [ ] Run validation: `python validate_discord_bot.py`
- [ ] Test imports: `python -c "import discord; print('OK')"`
- [ ] Test config loading: `python deploy_discord_bot.py`
- [ ] All validation checks pass
- [ ] No error messages in validation output

### Phase 7: Permissions & Security ✓
- [ ] Bot has necessary permissions in Discord server
- [ ] Bot role is positioned above moderation roles (if needed)
- [ ] Token is NOT committed to git
- [ ] .env is NOT visible in repository
- [ ] .gitignore includes `.env` patterns
- [ ] No sensitive data in code files
- [ ] Bot uses only required Discord intents

### Phase 8: Deployment ✓
- [ ] Run deployment script: `python deploy_discord_bot.py`
- [ ] All checks pass without errors
- [ ] Bot successfully connects to Discord
- [ ] Bot status shows as online in Discord
- [ ] Bot can receive messages
- [ ] Slash commands register successfully

### Phase 9: Functional Testing ✓
- [ ] `/ping` command works and shows latency
- [ ] `/help` command displays help message
- [ ] `/kortana [message]` command works
- [ ] Mentioning bot (@Kor'tana) generates responses
- [ ] Bot responds within reasonable time (< 5 seconds)
- [ ] Long messages truncate properly (> 2000 chars)
- [ ] Error messages display correctly

### Phase 10: Monitoring & Logging ✓
- [ ] Console logging displays normally
- [ ] Message logs show user interactions
- [ ] Error logs capture issues properly
- [ ] Bot recovers from temporary disconnections
- [ ] Memory usage is stable over time
- [ ] No persistent error loops

---

## 🚀 Deployment Commands

### Quick Start
```bash
# Windows
deploy_discord_bot.bat

# Linux/Mac
python deploy_discord_bot.py
```

### Validation Only
```bash
python validate_discord_bot.py
```

### Direct Start
```bash
python start_discord_bot.py
```

---

## 📋 Step-by-Step Deployment Process

### 1. Discord Developer Portal Setup (5 min)
```
1. Visit https://discord.com/developers/applications
2. Create new application → name: "Kor'tana"
3. Go to "Bot" section → Add Bot
4. Under "TOKEN" → Copy the token
5. Enable "Message Content Intent"
6. Go to OAuth2 → URL Generator
7. Select: bot → send messages, read messages, embed links
8. Copy generated URL and open in browser to invite to server
```

### 2. Environment Setup (3 min)
```bash
# Copy configuration template
cp .env.example .env

# Edit .env and add your token:
# DISCORD_BOT_TOKEN=your_token_here

# Verify format (should have dots)
echo $DISCORD_BOT_TOKEN
```

### 3. Install Dependencies (2 min)
```bash
# Create virtual environment (if needed)
python -m venv .kortana_config_test_env

# Activate
.kortana_config_test_env\Scripts\activate  # Windows
source .kortana_config_test_env/bin/activate  # Linux

# Install packages
pip install discord.py python-dotenv openai pydantic pyyaml
```

### 4. Validation (2 min)
```bash
# Run validator
python validate_discord_bot.py

# Expected output: ✅ All checks passed
```

### 5. Deployment (1 min)
```bash
# Method 1: Full deployment
python deploy_discord_bot.py

# Method 2: Simple start
python start_discord_bot.py
```

### 6. Verification (2 min)
```
1. Check Discord - bot should appear online
2. Test command in Discord: /ping
3. Test chat: /kortana hello
4. Verify response appears
```

**Total Time: ~15 minutes**

---

## 🐛 Troubleshooting During Deployment

### Issue: "ModuleNotFoundError: No module named 'discord'"
**Solution:**
```bash
pip install discord.py
```

### Issue: "DISCORD_BOT_TOKEN not found"
**Solution:**
1. Create `.env` file
2. Add: `DISCORD_BOT_TOKEN=your_token`
3. Save and restart

### Issue: "discord.errors.LoginFailure"
**Solution:**
1. Verify token in Discord Developer Portal
2. Copy fresh token if expired
3. Check no extra spaces in .env
4. Regenerate token if needed

### Issue: "Bot doesn't respond to messages"
**Solution:**
1. Check Message Content Intent is enabled
2. Verify bot has message permissions
3. Restart bot: `python start_discord_bot.py`
4. Check logs for errors

### Issue: "ModuleNotFoundError: No module named 'kortana'"
**Solution:**
```bash
set PYTHONPATH=c:\kortana\src
# or export PYTHONPATH=/path/to/kortana/src
python start_discord_bot.py
```

---

## 📊 Verification Checklist

After deployment, verify:

- [ ] Bot is online in Discord
- [ ] `/ping` command works
- [ ] `/help` command works
- [ ] `/kortana hello` returns a response
- [ ] Mentioning bot works
- [ ] Bot recovers from temporary disconnects
- [ ] No persistent errors in logs
- [ ] Response time is acceptable
- [ ] Memory usage is stable
- [ ] Bot handles long messages gracefully

---

## 🔒 Production Deployment Notes

Before deploying to production:

1. **Use a dedicated bot account** - Don't use personal account
2. **Secure token storage** - Keep .env file secure on server
3. **Regular token rotation** - Regenerate token periodically
4. **Monitor bot activity** - Watch for unusual behavior
5. **Rate limiting awareness** - Discord has API rate limits
6. **Error logging** - Set up persistent logging
7. **Backup configuration** - Keep copies of working .env
8. **Update handling** - Plan for dependency updates
9. **Testing in staging** - Always test before production
10. **Documentation** - Keep deployment docs up to date

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `python validate_discord_bot.py` | Validate setup |
| `python deploy_discord_bot.py` | Full deployment |
| `python start_discord_bot.py` | Start bot |
| `deploy_discord_bot.bat` | Windows deployment |
| `/ping` | Check bot status |
| `/kortana [msg]` | Chat with bot |
| `/help` | Show commands |

---

## ✅ Completion Criteria

Deployment is complete when:
1. ✅ All validation checks pass
2. ✅ Bot is online in Discord
3. ✅ Commands work correctly
4. ✅ Responses are received
5. ✅ No errors in logs
6. ✅ Performance is acceptable

---

**Status:** 🟢 Ready for Deployment  
**Last Updated:** February 8, 2026  
**Version:** Kor'tana Discord Bot v1.0
