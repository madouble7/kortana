# Discord Bot Setup Guide

## Overview

Kor'tana's Discord bot integrates advanced conversational capabilities with interactive features. It supports:

- **Kor'tana ChatEngine**: Primary conversational AI using your existing Kor'tana infrastructure
- **Hugging Face Integration**: Fallback conversational models for reliability
- **Real-time Commands**: Slash commands and prefix commands
- **Interactive Features**: Trivia, Rock-Paper-Scissors, Polls
- **Auto Features**: Auto-react and auto-reply capabilities
- **Production Ready**: Flask health check endpoint for deployment stability

## Prerequisites

1. **Python 3.11+** installed
2. **Discord Bot Token** from Discord Developer Portal
3. **Hugging Face API Key** (optional, but recommended)
4. Required Python packages installed

## Installation

### 1. Install Dependencies

```bash
pip install discord.py>=2.3.0
pip install Flask>=3.0.0
pip install huggingface_hub>=0.20.0
```

Or use the requirements.txt:

```bash
pip install -r requirements.txt
```

### 2. Create a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" tab and click "Add Bot"
4. Under "Privileged Gateway Intents", enable:
   - MESSAGE CONTENT INTENT
   - SERVER MEMBERS INTENT (optional)
5. Copy the bot token

### 3. Invite Bot to Your Server

1. Go to the "OAuth2" > "URL Generator" tab
2. Select scopes: `bot` and `applications.commands`
3. Select bot permissions:
   - Send Messages
   - Read Messages/View Channels
   - Add Reactions
   - Use Slash Commands
   - Embed Links
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

### 4. Get Hugging Face API Key (Optional)

1. Go to [Hugging Face](https://huggingface.co/)
2. Sign up or log in
3. Go to Settings > Access Tokens
4. Create a new token with "Read" permission
5. Copy the token

### 5. Configure Environment Variables

Create or update your `.env` file:

```env
# Required
DISCORD_BOT_TOKEN=your-discord-bot-token-here

# Optional but recommended
HUGGINGFACE_API_KEY=your-huggingface-api-key-here

# Optional: Auto-react configuration
AUTO_REACT_CHANNELS=123456789012345678,987654321098765432
AUTO_REACT_EMOJIS=👍,🤖,🔥
AUTO_REACT_KEYWORDS=awesome,cool,great
AUTO_REACT_COOLDOWN=10

# Optional: Auto-reply configuration
AUTO_REPLY_CHANNELS=123456789012345678
AUTO_REPLY_KEYWORDS=bot,ai
AUTO_REPLY_CHANCE=20
AUTO_REPLY_COOLDOWN=30

# Optional: Flask server port (for deployment)
PORT=5000
```

## Running the Bot

### Basic Usage

```bash
python src/discord_bot_enhanced.py
```

### With Kor'tana Integration

If you have Kor'tana configured, the bot will automatically use it. Otherwise, it falls back to Hugging Face or simple echo responses.

### Production Deployment

For production deployment on platforms like Railway, Render, or Heroku:

1. Set the `PORT` environment variable (usually provided by the platform)
2. Ensure all required environment variables are set
3. The bot includes a Flask health check endpoint at `/health`

## Features

### Chat Commands

#### `/kortana [message]`
Primary chat command that uses Kor'tana's brain with Hugging Face fallback.

**Example:**
```
/kortana Hello! How are you today?
```

#### `/ask [question]`
Alternative command that directly uses Hugging Face models.

**Example:**
```
/ask What is the meaning of life?
```

#### `@Kor'tana [message]`
You can also mention the bot in any message to chat.

**Example:**
```
@Kor'tana Tell me a fun fact!
```

### Status Commands

#### `/ping`
Check if the bot is online and responsive.

**Response:**
```
🟢 Kor'tana is online! Latency: 45ms
```

#### `/help`
Display all available commands and features.

### Interactive Game Commands

#### `/trivia`
Start a trivia question. Answer by typing in the chat.

**Example:**
```
/trivia
```
Bot will post a question, and you answer by typing the answer in the channel.

#### `/rps [choice]`
Play rock-paper-scissors with the bot.

**Example:**
```
/rps rock
```

#### `/poll [question] [options] [duration]`
Create a poll with up to 5 options.

**Example:**
```
/poll "What's for dinner?" "Pizza,Burgers,Tacos,Sushi" 60
```

### Auto Features

#### Auto-React
The bot can automatically add reactions to messages in configured channels.

**Configuration:**
- `AUTO_REACT_CHANNELS`: Comma-separated list of channel IDs
- `AUTO_REACT_EMOJIS`: Emojis to use (default: 👍,🤖,🔥)
- `AUTO_REACT_KEYWORDS`: Optional keywords to trigger reactions
- `AUTO_REACT_COOLDOWN`: Seconds between reactions per user (default: 10)

#### Auto-Reply
The bot can automatically reply to messages with fun responses.

**Configuration:**
- `AUTO_REPLY_CHANNELS`: Comma-separated list of channel IDs
- `AUTO_REPLY_KEYWORDS`: Optional keywords to trigger replies
- `AUTO_REPLY_CHANCE`: Percentage chance to reply (default: 20)
- `AUTO_REPLY_COOLDOWN`: Seconds between replies per user (default: 30)

## Architecture

### Conversational Flow

```
User Message
    ↓
Try Kor'tana Brain
    ↓ (if fails)
Try Hugging Face
    ↓ (if fails)
Simple Echo Response
```

### Components

1. **Discord Bot**: Handles Discord events and commands
2. **Kor'tana Brain**: Primary conversational engine (if available)
3. **Hugging Face Client**: Fallback conversational AI
4. **Flask Server**: Health check endpoint for deployment monitoring
5. **Auto Features**: Background message processing for auto-react/reply

### Security Features

- API keys loaded from environment variables (never hardcoded)
- Graceful degradation when services are unavailable
- Timeout handling for AI API calls (25 seconds default)
- Exception handling with logging
- Rate limiting via cooldowns

## Troubleshooting

### Bot doesn't respond to commands

1. **Check if bot is online**: Run `/ping` or check bot status in server
2. **Verify permissions**: Ensure bot has "Send Messages" and "Use Slash Commands" permissions
3. **Check logs**: Look for error messages in console output
4. **Verify token**: Ensure `DISCORD_BOT_TOKEN` is correct in `.env`

### Commands not appearing

1. **Sync commands**: Commands sync automatically on bot startup
2. **Wait**: Discord can take up to 1 hour to propagate slash commands globally
3. **Check server permissions**: Ensure bot has "Use Application Commands" permission

### Hugging Face not working

1. **Check API key**: Verify `HUGGINGFACE_API_KEY` in `.env`
2. **Install package**: Ensure `huggingface_hub` is installed
3. **Check logs**: Look for HF-related errors in console
4. **Fallback**: Bot will still work without HF, using Kor'tana brain or echo mode

### Auto features not working

1. **Check channel IDs**: Verify channel IDs in environment variables
2. **Right-click channel**: In Discord, right-click channel > Copy ID (enable Developer Mode first)
3. **Format correctly**: Channel IDs should be comma-separated numbers
4. **Check cooldowns**: Features have cooldown periods between activations

### Bot crashes on startup

1. **Check dependencies**: Ensure all required packages are installed
2. **Verify token**: Invalid token will cause immediate crash
3. **Check imports**: Ensure Kor'tana brain imports work or gracefully fail
4. **Review logs**: Check error messages for specific issues

## Deployment

### Local Development

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Run bot
python src/discord_bot_enhanced.py
```

### Production (Railway, Render, etc.)

1. **Set environment variables** in platform dashboard
2. **Procfile** (if needed):
   ```
   worker: python src/discord_bot_enhanced.py
   ```
3. **Health check**: Use `/health` endpoint for monitoring
4. **Logs**: Monitor platform logs for errors

### Docker (Optional)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "src/discord_bot_enhanced.py"]
```

## Advanced Configuration

### Custom Hugging Face Model

Edit `src/discord_bot_enhanced.py`:

```python
HF_MODEL = "your-model-name-here"  # Default: "meta-llama/Llama-3.2-3B-Instruct"
```

### Custom Response Length

```python
MAX_RESPONSE_LENGTH = 1900  # Discord limit is 2000
```

### Custom Timeout

```python
HF_TIMEOUT_SECONDS = 25  # Seconds to wait for HF response
```

## API Endpoints

The bot runs a Flask server for health monitoring:

### GET /
Returns bot status and features.

**Response:**
```json
{
  "status": "online",
  "bot": "Kor'tana Discord Bot",
  "message": "Bot is running! 🤖✨",
  "features": {
    "kortana_brain": true,
    "huggingface": true
  }
}
```

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "uptime": "running",
  "discord_connected": true
}
```

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use environment variables** for all sensitive data
3. **Rotate tokens regularly** if they may have been exposed
4. **Limit bot permissions** to only what's needed
5. **Monitor logs** for suspicious activity
6. **Use rate limiting** (built-in via cooldowns)
7. **Validate user input** (handled by Discord.py)

## Support

For issues or questions:

1. Check this documentation
2. Review bot logs for error messages
3. Verify all environment variables are set correctly
4. Ensure all dependencies are installed
5. Check Discord bot permissions in server settings

## License

This Discord bot is part of the Kor'tana project and follows the same license.
