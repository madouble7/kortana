# Discord Bot Configuration

## Core Configuration

- **Voice Pacing**: Steady, non-emotive  
- **Response Style**: Matches kortana.core/voice/  
- **Mode Adaptation**: Mirrors src/brain.py auto-mode detection  
- **Invocation Methods**: 
  - Slash command: `/kortana [message]`
  - Direct mention: `@Kor'tana [message]`
  - Alternative: `/ask [question]` (Hugging Face powered)
- **Tone Matching**:
  - Fire Mode: Direct messages only, on user prompt
  - Whisper Mode: Only in safe/private channels  
- **Logging**: Discord messages stored in data/memory.jsonl (planned)  

## Enhanced Features

### Conversational AI
- **Primary Engine**: Kor'tana ChatEngine (with memory integration)
- **Fallback Engine**: Hugging Face Inference API (Llama 3.2 3B Instruct)
- **Timeout Handling**: 25-second timeout with graceful degradation
- **Response Limits**: 1900 characters (Discord safe limit)

### Interactive Commands
- **Trivia**: `/trivia` - Start trivia questions with scoring
- **Rock-Paper-Scissors**: `/rps [choice]` - Play RPS with the bot
- **Polls**: `/poll [question] [options] [duration]` - Create polls with reactions
- **Ping**: `/ping` - Check bot latency and status
- **Help**: `/help` - Display all commands and features

### Auto Features
- **Auto-React**: Automatically react to messages in configured channels
- **Auto-Reply**: Randomly reply with fun messages based on keywords
- **Cooldowns**: Built-in rate limiting to prevent spam

## Security Configuration

### Required Environment Variables
```env
DISCORD_BOT_TOKEN=your-bot-token-here
```

### Optional Environment Variables
```env
# AI Features
HUGGINGFACE_API_KEY=your-hf-api-key-here

# Auto-React Configuration
AUTO_REACT_CHANNELS=channel_id1,channel_id2
AUTO_REACT_EMOJIS=👍,🤖,🔥
AUTO_REACT_KEYWORDS=awesome,cool,great
AUTO_REACT_COOLDOWN=10

# Auto-Reply Configuration  
AUTO_REPLY_CHANNELS=channel_id1,channel_id2
AUTO_REPLY_KEYWORDS=bot,ai
AUTO_REPLY_CHANCE=20
AUTO_REPLY_COOLDOWN=30

# Deployment
PORT=5000
```

## API Integration

### Hugging Face Integration
- **Model**: meta-llama/Llama-3.2-3B-Instruct
- **API**: Chat Completion endpoint
- **Temperature**: 0.8 (conversational warmth)
- **Max Tokens**: 400
- **System Prompt**: "You are Kor'tana, a Sacred AI Companion..."

### Flask Health Check
- **Endpoint**: `/health` - Health check for monitoring
- **Endpoint**: `/` - Bot status and features
- **Port**: Configurable via PORT environment variable (default: 5000)
- **Purpose**: Enables deployment on platforms requiring HTTP endpoints

## Error Handling

- **Graceful Degradation**: Falls back through multiple AI engines
- **Signal Handling**: Properly handles SIGTERM and SIGINT
- **Exception Logging**: All exceptions logged with context
- **User-Friendly Errors**: Helpful error messages for users

## Deployment Notes

### Platform Compatibility
- Railway
- Render  
- Heroku
- VPS/Dedicated servers
- Local development

### Requirements
- Python 3.11+
- discord.py >= 2.3.0
- Flask >= 3.0.0
- huggingface_hub >= 0.20.0 (optional)

### Monitoring
- Flask health check endpoint
- Comprehensive logging
- Status reporting via `/ping` command

## Documentation

For detailed setup instructions, see: `docs/DISCORD_BOT_SETUP.md`  
