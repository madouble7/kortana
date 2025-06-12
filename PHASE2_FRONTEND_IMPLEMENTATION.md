# 🎨 PHASE 2: Frontend Implementation Guide

## 🎯 Overview

Kor'tana's core system is **100% deployment ready**! Now it's time to implement a beautiful, modern frontend interface for user interaction. You have two excellent options:

## 🚀 Option 1: LobeChat Integration (RECOMMENDED)

### ✅ Why LobeChat?

**You already have LobeChat set up!** This is a massive advantage:

- ✅ **Modern React/Next.js Framework**: Beautiful, responsive UI
- ✅ **Multi-AI Provider Support**: Already supports OpenAI, Gemini, Claude
- ✅ **Advanced Features**: Voice chat, file uploads, plugin system
- ✅ **PWA Support**: Works as desktop/mobile app
- ✅ **Self-hosting Ready**: Full control over deployment
- ✅ **Active Development**: Constantly updated with new features

### 🔧 Implementation Steps

#### 1. Configure LobeChat Backend Connection

Create a custom API adapter to connect LobeChat to your Kor'tana backend:

```bash
# Navigate to LobeChat frontend
cd c:\project-kortana\lobechat-frontend

# Install dependencies
npm install

# Copy environment configuration
cp .env.example .env.local
```

#### 2. Create Kor'tana API Integration

**File: `src/libs/agent-runtime/kortana/index.ts`**

```typescript
import { LobeRuntimeAI } from '../types';
import { ChatStreamPayload } from '../types';

export class LobeKortanaAI implements LobeRuntimeAI {
  private baseURL: string;
  private apiKey: string;

  constructor(options: { baseURL?: string; apiKey?: string } = {}) {
    this.baseURL = options.baseURL || 'http://localhost:7860';
    this.apiKey = options.apiKey || 'kortana-local';
  }

  async chat(payload: ChatStreamPayload, options?: any) {
    const response = await fetch(`${this.baseURL}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify({
        messages: payload.messages,
        stream: payload.stream || true,
        model: payload.model || 'kortana-brain',
      }),
    });

    return response;
  }
}
```

#### 3. Environment Configuration

**File: `lobechat-frontend/.env.local`**

```bash
# Kor'tana Backend Configuration
KORTANA_API_URL=http://localhost:7860
KORTANA_API_KEY=kortana-local

# Optional: OpenAI Fallback
OPENAI_API_KEY=your_openai_key_here

# App Configuration
NEXT_PUBLIC_BASE_PATH=
```

#### 4. Launch LobeChat

```bash
cd c:\project-kortana\lobechat-frontend
npm run dev
```

Visit: `http://localhost:3000`

### 🎨 Customization Options

1. **Branding**: Update logo, colors, and title to "Kor'tana"
2. **Custom Agents**: Pre-configure Kor'tana personalities
3. **Memory Integration**: Display conversation history from Kor'tana's memory
4. **Sacred Covenant**: Add covenant guidelines in the UI

---

## 🤖 Option 2: Discord Bot Integration

### ✅ Why Discord?

- ✅ **Community Integration**: Natural for team/server environments
- ✅ **Easy Access**: No additional app needed
- ✅ **Rich Features**: Slash commands, embeds, reactions
- ✅ **Mobile Ready**: Discord mobile app support
- ✅ **Simple Setup**: Quick deployment and management

### 🔧 Implementation Steps

#### 1. Create Discord Application

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" → Name it "Kor'tana"
3. Go to "Bot" section → Click "Add Bot"
4. Copy the bot token

#### 2. Create Discord Bot Code

**File: `src/discord_bot.py`**

```python
import discord
from discord.ext import commands
import asyncio
import sys
import os
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.kortana.brain import ChatEngine

# Load environment variables
load_dotenv(override=True)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Kor'tana brain
chat_engine = ChatEngine()

@bot.event
async def on_ready():
    print(f'🚀 Kor\'tana is online as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="kortana", description="Chat with Kor'tana")
async def kortana_chat(interaction: discord.Interaction, message: str):
    await interaction.response.defer()

    try:
        # Get user context
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name

        # Generate response using Kor'tana brain
        response = await chat_engine.generate_response(
            message,
            user_id=user_id,
            user_name=user_name,
            channel="discord"
        )

        # Send response
        await interaction.followup.send(response)

    except Exception as e:
        print(f"Error: {e}")
        await interaction.followup.send("I'm experiencing some difficulties. Please try again.")

@bot.event
async def on_message(message):
    # Ignore bot messages
    if message.author == bot.user:
        return

    # Respond to direct mentions
    if bot.user in message.mentions:
        try:
            user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()

            response = await chat_engine.generate_response(
                user_message,
                user_id=str(message.author.id),
                user_name=message.author.display_name,
                channel="discord"
            )

            await message.reply(response)

        except Exception as e:
            print(f"Error: {e}")
            await message.reply("I'm experiencing some difficulties. Please try again.")

    await bot.process_commands(message)

# Error handling
@bot.event
async def on_command_error(ctx, error):
    print(f'Command error: {error}')

if __name__ == "__main__":
    # Get Discord token from environment
    discord_token = os.getenv('DISCORD_BOT_TOKEN')

    if not discord_token:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables")
        sys.exit(1)

    print("Starting Kor'tana Discord Bot...")
    bot.run(discord_token)
```

#### 3. Update Environment Variables

**Add to `.env`:**

```bash
# Discord Bot Configuration
DISCORD_BOT_TOKEN=your_discord_bot_token_here
```

#### 4. Install Discord Dependencies

```bash
pip install discord.py python-dotenv
```

#### 5. Launch Discord Bot

```bash
python src/discord_bot.py
```

### 🎮 Discord Features

1. **Slash Commands**: `/kortana [message]`
2. **Mentions**: @Kor'tana responds automatically
3. **Rich Embeds**: Beautiful formatted responses
4. **Voice Integration**: Future voice chat support

---

## 🏆 Recommendation: Start with LobeChat

### Why LobeChat First?

1. **Already Set Up**: You have the complete LobeChat codebase
2. **Feature Rich**: Voice, vision, plugins, themes
3. **Professional UI**: Modern, polished interface
4. **Self-Contained**: Complete web application
5. **Scalable**: Easy to deploy and maintain

### Implementation Timeline

- **Week 1**: LobeChat + Kor'tana integration
- **Week 2**: UI customization and branding
- **Week 3**: Advanced features (memory display, covenant integration)
- **Week 4**: Discord bot as secondary interface

---

## 🚀 Quick Start Commands

### LobeChat Route:
```bash
cd c:\project-kortana\lobechat-frontend
npm install
cp .env.example .env.local
# Edit .env.local with your settings
npm run dev
```

### Discord Route:
```bash
# Add DISCORD_BOT_TOKEN to .env
pip install discord.py
python src/discord_bot.py
```

---

## 🎯 Next Steps

1. **Choose your frontend** (LobeChat recommended)
2. **Configure API integration**
3. **Test basic chat functionality**
4. **Customize branding and UI**
5. **Deploy for production use**

The core Kor'tana brain is ready - now let's give it a beautiful face! 🎨✨
