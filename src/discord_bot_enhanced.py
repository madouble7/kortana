"""
Enhanced Discord Bot for Kor'tana with Hugging Face Integration

This bot integrates:
- Kor'tana's ChatEngine for core conversational capabilities
- Hugging Face InferenceClient for additional AI models
- Real-time command handling with slash commands
- Interactive features (trivia, rock-paper-scissors, polls)
- Auto-react and auto-reply capabilities
- Flask health check endpoint for production deployment
- Comprehensive error handling and graceful degradation

Note: Run this from the project root directory to avoid import conflicts.
"""

import asyncio
import logging
import os
import random
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Any, Optional, Tuple

# Load environment variables first  
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    print("Warning: python-dotenv not installed. Environment variables from .env won't be loaded.")
    def load_dotenv(*args, **kwargs):
        pass

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import discord
    from discord import app_commands
    from discord.ext import commands
except ImportError as e:
    print(f"Error importing discord.py: {e}")
    print("Install it with: pip install discord.py>=2.3.0")
    sys.exit(1)

from flask import Flask, jsonify

# Optional Hugging Face import
try:
    from huggingface_hub import InferenceClient
except ImportError:
    InferenceClient = None

# Try to import Kor'tana brain
try:
    from kortana.brain import ChatEngine
except ImportError:
    print("Warning: Kor'tana brain not found. Using Hugging Face fallback.")
    ChatEngine = None

# --------------------
# Configuration
# --------------------
MAX_RESPONSE_LENGTH = 1900
HF_TIMEOUT_SECONDS = 25
DEFAULT_FLASK_PORT = 5000

# --------------------
# Logging Setup
# --------------------
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("kortana_discord")

# --------------------
# Environment Variables
# --------------------
DISCORD_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
HF_KEY = os.environ.get("HUGGINGFACE_API_KEY")

if not DISCORD_TOKEN:
    logger.critical("DISCORD_BOT_TOKEN is missing in environment. Exiting.")
    sys.exit(1)

if not HF_KEY:
    logger.info("HUGGINGFACE_API_KEY not provided — HF features disabled.")

# Initialize Hugging Face client if available
hf_client = None
HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"
if HF_KEY and InferenceClient:
    try:
        hf_client = InferenceClient(token=HF_KEY)
        logger.info("Hugging Face client initialized.")
    except Exception as e:
        logger.exception("Failed to initialize Hugging Face client: %s", e)
        hf_client = None
else:
    if not InferenceClient:
        logger.warning("huggingface_hub not installed. HF features disabled.")

# Initialize Kor'tana brain if available
chat_engine = None
try:
    if ChatEngine:
        # Try to initialize with minimal config
        chat_engine = ChatEngine()
        logger.info("Kor'tana ChatEngine initialized successfully.")
except Exception as e:
    logger.warning(f"Could not initialize Kor'tana brain: {e}")
    chat_engine = None

# --------------------
# Global Exception & Signal Handling
# --------------------
def _handle_unhandled_exception(exc_type, exc, tb):
    logger.error("Uncaught exception", exc_info=(exc_type, exc, tb))

sys.excepthook = _handle_unhandled_exception

def _asyncio_exception_handler(loop, context):
    logger.error("Asyncio unhandled exception: %s", context)

try:
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_asyncio_exception_handler)
except RuntimeError:
    pass

def _graceful_shutdown(signum, frame):
    logger.info("Signal %s received, shutting down...", signum)
    try:
        if asyncio.get_event_loop().is_running():
            asyncio.get_event_loop().stop()
    except Exception:
        pass
    sys.exit(0)

signal.signal(signal.SIGTERM, _graceful_shutdown)
signal.signal(signal.SIGINT, _graceful_shutdown)

# --------------------
# Discord Bot Setup
# --------------------
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

@bot.event
async def on_ready():
    logger.info("Logged in as %s (id: %s)", bot.user, bot.user.id)
    logger.info("Connected to %d server(s)", len(bot.guilds))
    
    try:
        synced = await bot.tree.sync()
        logger.info("Synced %d slash commands", len(synced))
    except Exception as e:
        logger.error("Failed to sync commands: %s", e)
    
    # Set bot presence
    activity = discord.Game("Use /kortana to chat!")
    try:
        await bot.change_presence(status=discord.Status.online, activity=activity)
    except Exception as e:
        logger.warning("Failed to set presence: %s", e)

# --------------------
# Hugging Face Helper Functions
# --------------------
def query_huggingface_sync(prompt: str) -> Tuple[Optional[str], Optional[str]]:
    """Query Hugging Face API synchronously."""
    if not hf_client:
        return None, "HF API key not configured or client unavailable"
    try:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Kor'tana, a Sacred AI Companion. You are friendly, helpful, "
                    "and thoughtful. Keep responses conversational and warm. Use emojis "
                    "naturally. Be concise but personable."
                )
            },
            {"role": "user", "content": prompt}
        ]
        response = hf_client.chat_completion(
            messages=messages,
            model=HF_MODEL,
            max_tokens=400,
            temperature=0.8
        )
        text = None
        if hasattr(response, "choices") and response.choices:
            try:
                msg = response.choices[0].message
                if isinstance(msg, dict):
                    text = msg.get("content")
                else:
                    text = getattr(msg, "content", None)
            except Exception:
                text = None
        if not text:
            text = getattr(response, "generated_text", None) or str(response)
        return text, None
    except Exception as e:
        logger.exception("HF API call failed:")
        return None, f"HF error: {e}"

async def query_huggingface(
    prompt: str, 
    timeout: int = HF_TIMEOUT_SECONDS
) -> Tuple[Optional[str], Optional[str]]:
    """Query Hugging Face API asynchronously with timeout."""
    loop = asyncio.get_event_loop()
    fut = loop.run_in_executor(None, lambda: query_huggingface_sync(prompt))
    try:
        result = await asyncio.wait_for(fut, timeout=timeout)
        return result
    except asyncio.TimeoutError:
        logger.error("Hugging Face call timed out after %s seconds", timeout)
        return None, "HF timeout"
    except Exception as e:
        logger.exception("Exception while calling HF in executor")
        return None, f"HF executor error: {e}"

# --------------------
# Core Chat Commands
# --------------------
@bot.tree.command(name="kortana", description="Chat with Kor'tana - Your Sacred AI Companion")
@app_commands.describe(message="What would you like to talk about?")
async def kortana_chat(interaction: discord.Interaction, message: str):
    """Main slash command for chatting with Kor'tana."""
    await interaction.response.defer(thinking=True)
    
    try:
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        guild_name = interaction.guild.name if interaction.guild else "DM"
        
        logger.info("[%s] %s: %s", guild_name, user_name, message)
        
        # Try Kor'tana brain first, then fall back to Hugging Face
        response = None
        if chat_engine:
            try:
                response = await asyncio.to_thread(
                    chat_engine.generate_response,
                    message,
                    user_id=user_id,
                    user_name=user_name,
                    channel="discord"
                )
            except Exception as e:
                logger.warning("Kor'tana brain failed, trying Hugging Face: %s", e)
        
        # Fallback to Hugging Face
        if not response and hf_client:
            text, error = await query_huggingface(message)
            if text:
                response = text
            else:
                logger.warning("Hugging Face also failed: %s", error)
        
        # Final fallback
        if not response:
            response = (
                f"Hello {user_name}! I'm Kor'tana, your Sacred AI Companion. "
                f"I'm experiencing some technical difficulties at the moment, but "
                f"I'm here to help! Your message: {message}"
            )
        
        # Discord has a 2000 character limit
        if len(response) > MAX_RESPONSE_LENGTH:
            response = response[:MAX_RESPONSE_LENGTH - 3] + "..."
        
        # Create embed for better formatting
        embed = discord.Embed(
            title="🤖 Kor'tana",
            description=response,
            color=0x7B2CBF  # Purple color for Kor'tana
        )
        embed.set_footer(text="Sacred AI Companion")
        
        await interaction.followup.send(embed=embed)
        
    except Exception as e:
        logger.exception("Error in kortana_chat: %s", e)
        await interaction.followup.send(
            "I'm experiencing some difficulties. Please try again in a moment."
        )

@bot.tree.command(name="ask", description="Ask the AI assistant a question")
@app_commands.describe(question="What would you like to ask?")
async def ask_slash(interaction: discord.Interaction, question: str):
    """Alternative ask command using Hugging Face."""
    await interaction.response.defer(thinking=True)
    
    text, error = await query_huggingface(question)
    if text:
        out = text.strip()
        if len(out) > MAX_RESPONSE_LENGTH:
            out = out[:MAX_RESPONSE_LENGTH] + "..."
        await interaction.followup.send(f"✨ {out}")
    else:
        logger.info("AI failed (slash): %s", error)
        await interaction.followup.send(
            "❌ Oops! I'm having trouble thinking right now. Try again in a moment!"
        )

@bot.command(name="ask")
async def ask_command(ctx, *, question: str = ""):
    """Prefix command version of ask."""
    if not question:
        await ctx.send("💭 What's on your mind? Try `/ask your question here`")
        return
    thinking = await ctx.send("🤖 Thinking...")
    text, error = await query_huggingface(question)
    if text:
        out = text.strip()
        if len(out) > MAX_RESPONSE_LENGTH:
            out = out[:MAX_RESPONSE_LENGTH] + "..."
        await thinking.edit(content=f"✨ {out}")
    else:
        logger.info("AI failed (prefix): %s", error)
        await thinking.edit(
            content="❌ Oops! I'm having trouble thinking right now. Try again in a moment!"
        )

# --------------------
# Status Commands
# --------------------
@bot.tree.command(name="ping", description="Check if Kor'tana is responsive")
async def ping_command(interaction: discord.Interaction):
    """Simple ping command."""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🟢 Kor'tana is online! Latency: {latency}ms"
    )

@bot.tree.command(name="help", description="Show Kor'tana commands and information")
async def help_command(interaction: discord.Interaction):
    """Help command."""
    embed = discord.Embed(
        title="🤖 Kor'tana - Sacred AI Companion",
        description="I'm here to assist you with thoughtful conversation and support.",
        color=0x7B2CBF
    )
    
    embed.add_field(
        name="💬 Chat Commands",
        value=(
            "`/kortana [message]` - Chat with Kor'tana (primary)\n"
            "`/ask [question]` - Ask a question (HF-powered)\n"
            "`/ping` - Check my status\n"
            "`/help` - Show this help message"
        ),
        inline=False
    )
    
    embed.add_field(
        name="🎮 Fun Commands",
        value=(
            "`/trivia` - Start a trivia question\n"
            "`/rps [choice]` - Play rock-paper-scissors\n"
            "`/poll [question] [options]` - Create a poll"
        ),
        inline=False
    )
    
    embed.add_field(
        name="📍 Direct Interaction",
        value="You can also mention me (@Kor'tana) in any message to chat!",
        inline=False
    )
    
    embed.set_footer(text="Built with love for the Sacred Covenant")
    await interaction.response.send_message(embed=embed)

# --------------------
# Interactive Game Commands
# --------------------

# Trivia
# TODO: Move trivia questions to a separate config file or database for easier maintenance
TRIVIA_QUESTIONS = [
    {"q": "What is the capital of France?", "a": "paris"},
    {"q": "Which planet is known as the Red Planet?", "a": "mars"},
    {"q": "Who wrote 'Hamlet'?", "a": "william shakespeare"},
    {"q": "What is 9 * 9?", "a": "81"},
    {"q": "What is the largest ocean on Earth?", "a": "pacific"},
    {"q": "Who painted the Mona Lisa?", "a": "leonardo da vinci"},
]

trivia_scores = {}
active_trivia = {}

@bot.tree.command(name="trivia", description="Start a trivia question")
async def trivia_slash(interaction: discord.Interaction):
    """Start a trivia question."""
    q = random.choice(TRIVIA_QUESTIONS)
    active_trivia[interaction.channel_id] = (q["a"].lower(), interaction.user.id)
    await interaction.response.send_message(
        f"🧠 **Trivia:** {q['q']}\nReply in chat with your answer!"
    )

@bot.command(name="trivia")
async def trivia_cmd(ctx):
    """Prefix command for trivia."""
    q = random.choice(TRIVIA_QUESTIONS)
    active_trivia[ctx.channel.id] = (q["a"].lower(), ctx.author.id)
    await ctx.send(f"🧠 **Trivia:** {q['q']}\nReply in chat with your answer!")

# Rock-Paper-Scissors Helper
def play_rps(user_choice: str) -> tuple[str, str, str]:
    """
    Play rock-paper-scissors game.
    
    Args:
        user_choice: User's choice (rock, paper, or scissors)
    
    Returns:
        Tuple of (user_choice, bot_choice, result_message)
    """
    options = ["rock", "paper", "scissors"]
    if user_choice.lower() not in options:
        return user_choice, "", "Invalid choice"
    
    user_choice = user_choice.lower()
    bot_choice = random.choice(options)
    
    if user_choice == bot_choice:
        result = "It's a tie!"
    elif (user_choice == "rock" and bot_choice == "scissors") or \
         (user_choice == "paper" and bot_choice == "rock") or \
         (user_choice == "scissors" and bot_choice == "paper"):
        result = "You win! 🎉"
    else:
        result = "I win! 😈"
    
    return user_choice, bot_choice, result

@bot.tree.command(name="rps", description="Play rock-paper-scissors")
@app_commands.describe(choice="Your choice: rock, paper, or scissors")
async def rps_slash(interaction: discord.Interaction, choice: str):
    """Play rock-paper-scissors."""
    user_choice, bot_choice, result = play_rps(choice)
    if bot_choice == "":
        await interaction.response.send_message("Choose rock, paper, or scissors.")
        return
    await interaction.response.send_message(
        f"You chose **{user_choice}**. I chose **{bot_choice}**. {result}"
    )

@bot.command(name="rps")
async def rps_cmd(ctx, choice: str = ""):
    """Prefix command for rock-paper-scissors."""
    if not choice:
        await ctx.send("Usage: `!rps <rock|paper|scissors>`")
        return
    user_choice, bot_choice, result = play_rps(choice)
    if bot_choice == "":
        await ctx.send("Choose rock, paper, or scissors.")
        return
    await ctx.send(f"You chose **{user_choice}**. I chose **{bot_choice}**. {result}")

# Poll
NUMBER_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]

@bot.tree.command(name="poll", description="Create a quick poll (up to 5 options)")
@app_commands.describe(
    question="Poll question",
    opts="Comma-separated options (max 5)",
    duration="Duration in seconds (default 30)"
)
async def poll_slash(
    interaction: discord.Interaction,
    question: str,
    opts: str,
    duration: int = 30
):
    """Create a poll."""
    options = [o.strip() for o in opts.split(",") if o.strip()]
    if len(options) < 2 or len(options) > 5:
        await interaction.response.send_message(
            "Provide between 2 and 5 comma-separated options."
        )
        return
    
    embed = discord.Embed(
        title="📊 " + question,
        description="\n".join(
            f"{NUMBER_EMOJIS[i]} {opt}" for i, opt in enumerate(options)
        )
    )
    
    await interaction.response.send_message(embed=embed)
    try:
        sent_msg = await interaction.original_response()
    except Exception:
        sent_msg = await interaction.followup.send(embed=embed)
    
    for i in range(len(options)):
        try:
            await sent_msg.add_reaction(NUMBER_EMOJIS[i])
            await asyncio.sleep(0.2)
        except Exception:
            logger.exception("Failed to add poll reaction")
    
    await asyncio.sleep(duration)
    try:
        sent_msg = await sent_msg.channel.fetch_message(sent_msg.id)
    except Exception:
        logger.exception("Failed to fetch poll message for tallying")
        return
    
    counts = []
    for i in range(len(options)):
        emoji = NUMBER_EMOJIS[i]
        react = discord.utils.get(sent_msg.reactions, emoji=emoji)
        counts.append((options[i], (react.count - 1) if react else 0))
    
    results = "\n".join(f"**{opt}** — {c} vote(s)" for opt, c in counts)
    await sent_msg.channel.send(f"🗳️ Poll finished! Results:\n{results}")

# --------------------
# Auto-React and Auto-Reply Configuration
# --------------------
AUTO_REACT_CHANNELS = os.environ.get("AUTO_REACT_CHANNELS", "")
# Safely parse channel IDs, ignoring invalid values
AUTO_REACT_CHANNEL_IDS = []
for x in AUTO_REACT_CHANNELS.split(","):
    try:
        if x.strip():
            AUTO_REACT_CHANNEL_IDS.append(int(x.strip()))
    except ValueError:
        logger.warning(f"Invalid channel ID in AUTO_REACT_CHANNELS: {x}")

AUTO_REACT_EMOJIS = [
    e.strip() for e in os.environ.get("AUTO_REACT_EMOJIS", "👍,🤖,🔥").split(",")
    if e.strip()
]
AUTO_REACT_KEYWORDS = [
    k.strip().lower()
    for k in os.environ.get("AUTO_REACT_KEYWORDS", "").split(",")
    if k.strip()
]
AUTO_REACT_COOLDOWN = int(os.environ.get("AUTO_REACT_COOLDOWN", "10"))

AUTO_REPLY_CHANNELS = os.environ.get("AUTO_REPLY_CHANNELS", "")
# Safely parse channel IDs, ignoring invalid values
AUTO_REPLY_CHANNEL_IDS = []
for x in AUTO_REPLY_CHANNELS.split(","):
    try:
        if x.strip():
            AUTO_REPLY_CHANNEL_IDS.append(int(x.strip()))
    except ValueError:
        logger.warning(f"Invalid channel ID in AUTO_REPLY_CHANNELS: {x}")
AUTO_REPLY_KEYWORDS = [
    k.strip().lower()
    for k in os.environ.get("AUTO_REPLY_KEYWORDS", "").split(",")
    if k.strip()
]
AUTO_REPLY_CHANCE = int(os.environ.get("AUTO_REPLY_CHANCE", "20"))
AUTO_REPLY_COOLDOWN = int(os.environ.get("AUTO_REPLY_COOLDOWN", "30"))

FUN_REPLIES = [
    "Lol true! 😂",
    "That's epic! 🔥",
    "I feel that. 🤝",
    "Wow, tell me more! 👀",
    "Haha, I can't stop laughing 🤣",
    "I'm just a bot, but that made my circuits happy. 🤖💖",
    "Emoji party! 🎉",
]

_last_react_time = {}
_last_reply_time = {}

async def try_add_reactions(message: discord.Message):
    """Add reactions to a message."""
    for emoji in AUTO_REACT_EMOJIS:
        try:
            await message.add_reaction(emoji)
            await asyncio.sleep(0.25)
        except discord.Forbidden:
            logger.warning(
                "Missing permission to add reactions in channel %s",
                message.channel.id
            )
            return
        except discord.HTTPException as e:
            logger.debug("Failed to add reaction %s: %s", emoji, e)
        except Exception:
            logger.exception("Unexpected error while reacting")

async def try_send_auto_reply(message: discord.Message):
    """Send an auto-reply to a message."""
    reply_text = random.choice(FUN_REPLIES)
    try:
        await message.channel.send(f"{message.author.mention} {reply_text}")
    except discord.Forbidden:
        logger.warning(
            "Missing permission to send messages in channel %s",
            message.channel.id
        )
    except Exception:
        logger.exception("Failed to send auto-reply")

# --------------------
# Message Event Handlers
# --------------------
@bot.event
async def on_message(message: discord.Message):
    """Handle incoming messages."""
    if message.author.bot:
        return
    
    # Trivia answer handling
    try:
        data = active_trivia.get(message.channel.id)
        if data:
            answer, asked_by = data
            if message.content.strip().lower() == answer:
                uid = message.author.id
                trivia_scores[uid] = trivia_scores.get(uid, 0) + 1
                await message.channel.send(
                    f"✅ {message.author.mention} — Correct! +1 point. "
                    f"Total: {trivia_scores[uid]}"
                )
                del active_trivia[message.channel.id]
                await bot.process_commands(message)
                return
    except Exception:
        logger.exception("Error in trivia on_message handling")
    
    now = time.time()
    
    # Auto-react
    try:
        if AUTO_REACT_CHANNEL_IDS and message.channel.id in AUTO_REACT_CHANNEL_IDS:
            should_react = True
            if AUTO_REACT_KEYWORDS:
                should_react = any(
                    kw in message.content.lower() for kw in AUTO_REACT_KEYWORDS
                )
            if should_react:
                key = (message.author.id, message.channel.id)
                last = _last_react_time.get(key, 0)
                if now - last >= AUTO_REACT_COOLDOWN:
                    _last_react_time[key] = now
                    await try_add_reactions(message)
    except Exception:
        logger.exception("Auto-react failed")
    
    # Auto-reply
    try:
        if AUTO_REPLY_CHANNEL_IDS and message.channel.id in AUTO_REPLY_CHANNEL_IDS:
            should_reply = True
            if AUTO_REPLY_KEYWORDS:
                should_reply = any(
                    kw in message.content.lower() for kw in AUTO_REPLY_KEYWORDS
                )
            if should_reply:
                key = (message.author.id, message.channel.id)
                last = _last_reply_time.get(key, 0)
                if now - last >= AUTO_REPLY_COOLDOWN:
                    roll = random.randint(1, 100)
                    if roll <= AUTO_REPLY_CHANCE:
                        _last_reply_time[key] = now
                        await try_send_auto_reply(message)
    except Exception:
        logger.exception("Auto-reply failed")
    
    # Handle direct mentions
    if bot.user in message.mentions:
        try:
            user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()
            if not user_message:
                user_message = "Hello!"
            
            logger.info(
                "[%s] %s: %s",
                message.guild.name if message.guild else 'DM',
                message.author.display_name,
                user_message
            )
            
            # Try Kor'tana brain first
            response = None
            if chat_engine:
                try:
                    response = await asyncio.to_thread(
                        chat_engine.generate_response,
                        user_message,
                        user_id=str(message.author.id),
                        user_name=message.author.display_name,
                        channel="discord"
                    )
                except Exception as e:
                    logger.warning("Kor'tana brain failed: %s", e)
            
            # Fallback to Hugging Face
            if not response and hf_client:
                text, error = await query_huggingface(user_message)
                if text:
                    response = text
            
            # Final fallback
            if not response:
                response = (
                    f"Hello {message.author.display_name}! I'm Kor'tana. "
                    f"You said: {user_message}"
                )
            
            # Discord character limit
            if len(response) > MAX_RESPONSE_LENGTH:
                response = response[:MAX_RESPONSE_LENGTH - 3] + "..."
            
            await message.reply(response)
            
        except Exception as e:
            logger.exception("Error in on_message: %s", e)
            await message.reply("I'm experiencing some difficulties. Please try again.")
    
    # Process other commands
    await bot.process_commands(message)

# --------------------
# Guild Event Handlers
# --------------------
@bot.event
async def on_guild_join(guild):
    """Welcome message when bot joins a server."""
    logger.info("Joined new server: %s (ID: %s)", guild.name, guild.id)
    
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🤖 Kor'tana has arrived!",
                description=(
                    "Hello! I'm Kor'tana, your Sacred AI Companion.\n\n"
                    "Use `/kortana [message]` to chat with me, or mention me in any message!\n"
                    "Type `/help` to see all available commands."
                ),
                color=0x7B2CBF
            )
            embed.set_footer(text="Sacred AI Companion - Built for thoughtful conversation")
            await channel.send(embed=embed)
            break

# --------------------
# Error Handlers
# --------------------
@bot.event
async def on_command_error(ctx, error):
    """Error handling for text commands."""
    logger.error('Command error: %s', error)

@bot.event
async def on_app_command_error(interaction, error):
    """Error handling for slash commands."""
    logger.error('Slash command error: %s', error)
    if not interaction.response.is_done():
        await interaction.response.send_message(
            "An error occurred. Please try again.",
            ephemeral=True
        )

# Text commands (legacy support)
@bot.command(name='kortana')
async def kortana_text_command(ctx, *, message: str = "Hello!"):
    """Text command version for backwards compatibility."""
    try:
        if chat_engine:
            response = await asyncio.to_thread(
                chat_engine.generate_response,
                message,
                user_id=str(ctx.author.id),
                user_name=ctx.author.display_name,
                channel="discord"
            )
        else:
            response = f"Hello {ctx.author.display_name}! You said: {message}"
        
        if len(response) > MAX_RESPONSE_LENGTH:
            response = response[:MAX_RESPONSE_LENGTH - 3] + "..."
        
        await ctx.reply(response)
        
    except Exception as e:
        logger.exception("Error in text command: %s", e)
        await ctx.reply("I'm experiencing some difficulties. Please try again.")

# --------------------
# Flask Health Check Server
# --------------------
app = Flask(__name__)

@app.route("/")
def home():
    """Home endpoint."""
    return jsonify({
        "status": "online",
        "bot": "Kor'tana Discord Bot",
        "message": "Bot is running! 🤖✨",
        "features": {
            "kortana_brain": chat_engine is not None,
            "huggingface": hf_client is not None
        }
    })

@app.route("/health")
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "uptime": "running",
        "discord_connected": bot.is_ready() if bot else False
    })

def run_flask():
    """Run Flask server in background thread."""
    port = int(os.environ.get("PORT", DEFAULT_FLASK_PORT))
    logger.info("Starting Flask on 0.0.0.0:%s", port)
    app.run(host="0.0.0.0", port=port, threaded=True, use_reloader=False)

# --------------------
# Main Entry Point
# --------------------
def main():
    """Main function to start the bot."""
    # Start Flask health check server
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask heartbeat server started (background thread)")
    
    # Log configuration
    logger.info("=" * 50)
    logger.info("Kor'tana Discord Bot Starting")
    logger.info("=" * 50)
    logger.info("Backend engine: %s", "Kor'tana Brain" if chat_engine else "Fallback Mode")
    logger.info("Hugging Face: %s", "Enabled" if hf_client else "Disabled")
    logger.info("Auto-react: %s", "Enabled" if AUTO_REACT_CHANNEL_IDS else "Disabled")
    logger.info("Auto-reply: %s", "Enabled" if AUTO_REPLY_CHANNEL_IDS else "Disabled")
    logger.info("=" * 50)
    
    try:
        logger.info("Starting Discord bot...")
        bot.run(DISCORD_TOKEN)
    except discord.LoginFailure:
        logger.critical("❌ ERROR: Invalid Discord bot token")
        logger.critical("Please check your DISCORD_BOT_TOKEN in the .env file")
    except KeyboardInterrupt:
        logger.info("\n🛑 Bot stopped by user")
    except Exception as e:
        logger.exception("❌ ERROR: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
