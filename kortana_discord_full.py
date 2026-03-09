#!/usr/bin/env python
"""
Kor'tana Discord Bot - Full Integration
Connects ChatEngine brain + Voice capabilities
"""

import os
import sys
from pathlib import Path

# Setup paths
sys.path.insert(0, str(Path(__file__).parent / "src"))

import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment
load_dotenv(override=True)

print("\n" + "=" * 80)
print("🎤 KOR'TANA DISCORD BOT - Full AI + Voice Integration")
print("=" * 80 + "\n")

# Import Kor'tana's brain and voice system
try:
    print("Loading Kor'tana's brain...")
    from kortana.brain import ChatEngine
    from kortana.config import load_config
    from kortana.voice import STTService, TTSService, VoiceChatOrchestrator

    print("✅ Brain and voice systems loaded\n")
except ImportError as e:
    print(f"❌ Failed to load Kor'tana modules: {e}")
    print("\nMake sure you're running from the kortana directory.")
    input("Press Enter to exit...")
    sys.exit(1)

# Check token
token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    print("❌ ERROR: DISCORD_BOT_TOKEN not found in .env")
    input("Press Enter to exit...")
    sys.exit(1)

# Load Kor'tana config
print("Loading Kor'tana configuration...")
try:
    config_path = Path(__file__).parent / "kortana.yaml"
    settings = load_config(str(config_path))
    print("✅ Configuration loaded\n")
except Exception as e:
    print(f"⚠️  Warning: Could not load full config: {e}")
    print("Using default configuration...\n")
    from kortana.config.schema import KortanaConfig

    settings = KortanaConfig()

# Initialize Kor'tana's brain
print("Awakening Kor'tana's consciousness...")
try:
    chat_engine = ChatEngine(settings)
    print("✅ Kor'tana is conscious\n")
except Exception as e:
    print(f"⚠️  Warning: ChatEngine initialization issue: {e}")
    print("Bot will continue with limited functionality.\n")
    chat_engine = None

# Initialize voice orchestrator
print("Initializing voice capabilities...")
try:
    voice_orchestrator = (
        VoiceChatOrchestrator(
            chat_engine=chat_engine, stt_service=STTService(), tts_service=TTSService()
        )
        if chat_engine
        else None
    )
    print("✅ Voice system ready\n")
except Exception as e:
    print(f"⚠️  Warning: Voice system unavailable: {e}\n")
    voice_orchestrator = None

# Configure Discord bot
print("Configuring Discord bot...")
intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Store active voice connections
voice_sessions = {}


@bot.event
async def on_ready():
    """Bot ready event"""
    print(f"\n🚀 Kor'tana is online as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Connected to {len(bot.guilds)} server(s)")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)")
        print("\n✅ Kor'tana is ready for text and voice interactions!")
        print("=" * 80 + "\n")
    except Exception as e:
        print(f"Failed to sync commands: {e}\n")


@bot.event
async def on_guild_join(guild):
    """Welcome message when bot joins a server"""
    if guild.system_channel:
        embed = discord.Embed(
            title="🤖 Kor'tana Has Arrived",
            description=(
                "Hello! I'm Kor'tana, your AI companion.\n\n"
                "**Text Commands:**\n"
                "• `/kortana [message]` - Talk to me\n"
                "• `/ping` - Check if I'm responsive\n"
                "• `/help` - See all commands\n\n"
                "**Voice:**\n"
                "• Join a voice channel and use `/join` to bring me in\n"
                "• I can listen and respond with voice!"
            ),
            color=discord.Color.blue(),
        )
        await guild.system_channel.send(embed=embed)


@bot.tree.command(name="ping", description="Check if Kor'tana is responsive")
async def ping_command(interaction: discord.Interaction):
    """Simple ping command"""
    await interaction.response.send_message(
        f"🤖 **Kor'tana is online!**\nLatency: {round(bot.latency * 1000)}ms",
        ephemeral=True,
    )


async def speak_response(guild, text):
    """Helper to speak text in voice channel if connected"""
    voice_client = guild.voice_client
    if not voice_client or not voice_client.is_connected():
        return False

    try:
        if voice_orchestrator:
            # Generate audio using TTS
            import io

            tts_result = voice_orchestrator.tts.synthesize(text)
            audio_bytes = tts_result["audio_bytes"]

            # Play audio in voice channel
            audio_source = discord.FFmpegPCMAudio(io.BytesIO(audio_bytes), pipe=True)

            if voice_client.is_playing():
                voice_client.stop()

            voice_client.play(audio_source)
            return True
    except Exception as e:
        print(f"Voice output error: {e}")
        return False


@bot.tree.command(name="kortana", description="Talk to Kor'tana")
async def kortana_chat(interaction: discord.Interaction, message: str):
    """Main chat command with AI brain"""
    await interaction.response.defer()

    try:
        if chat_engine:
            # Use full AI brain
            response = await chat_engine.process_message(
                message,
                user_id=str(interaction.user.id),
                user_name=interaction.user.display_name,
                channel="discord",
            )
        else:
            # Fallback response
            response = f"I hear you, {interaction.user.display_name}! (AI brain currently unavailable)"

        # Create embed response
        embed = discord.Embed(
            title="🤖 Kor'tana", description=response, color=discord.Color.blue()
        )
        embed.set_footer(text="Sacred AI Companion")

        # Send text response
        await interaction.followup.send(embed=embed)

        # If in voice channel, also speak the response
        if interaction.guild.voice_client:
            spoke = await speak_response(interaction.guild, response)
            if spoke:
                await interaction.followup.send(
                    "🔊 Speaking in voice channel...", ephemeral=True
                )

    except Exception as e:
        await interaction.followup.send(
            f"⚠️ I'm having trouble processing that. Error: {str(e)}", ephemeral=True
        )


@bot.tree.command(name="join", description="Kor'tana joins your voice channel")
async def join_voice(interaction: discord.Interaction):
    """Join user's voice channel"""
    if not interaction.user.voice:
        await interaction.response.send_message(
            "❌ You need to be in a voice channel first!", ephemeral=True
        )
        return

    if not voice_orchestrator:
        await interaction.response.send_message(
            "⚠️ Voice features are currently unavailable.", ephemeral=True
        )
        return

    channel = interaction.user.voice.channel

    try:
        # Check if already connected
        if interaction.guild.voice_client:
            await interaction.guild.voice_client.move_to(channel)
        else:
            await channel.connect()

        voice_sessions[interaction.guild.id] = {"channel": channel, "users": set()}

        await interaction.response.send_message(
            f"🎤 Joined {channel.name}! Use `/kortana` to chat - I'll speak my responses aloud.",
            ephemeral=False,
        )

    except Exception as e:
        await interaction.response.send_message(
            f"❌ Failed to join voice: {str(e)}", ephemeral=True
        )


@bot.tree.command(name="speak", description="Make Kor'tana speak text in voice channel")
async def speak_text(interaction: discord.Interaction, text: str):
    """Speak specific text in voice channel"""
    if not interaction.guild.voice_client:
        await interaction.response.send_message(
            "❌ I'm not in a voice channel! Use `/join` first.", ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        spoke = await speak_response(interaction.guild, text)
        if spoke:
            await interaction.followup.send(
                f"🔊 Speaking: '{text[:50]}...'", ephemeral=True
            )
        else:
            await interaction.followup.send(
                "⚠️ Voice output unavailable.", ephemeral=True
            )
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)


@bot.tree.command(name="leave", description="Kor'tana leaves the voice channel")
async def leave_voice(interaction: discord.Interaction):
    """Leave voice channel"""
    if interaction.guild.voice_client:
        await interaction.guild.voice_client.disconnect()
        if interaction.guild.id in voice_sessions:
            del voice_sessions[interaction.guild.id]
        await interaction.response.send_message("👋 Left the voice channel.")
    else:
        await interaction.response.send_message(
            "❌ I'm not in a voice channel!", ephemeral=True
        )


@bot.tree.command(name="help", description="Learn about Kor'tana's capabilities")
async def help_command(interaction: discord.Interaction):
    """Help command"""
    embed = discord.Embed(
        title="🤖 Kor'tana - AI Companion",
        description="I'm here to help and chat with you!",
        color=discord.Color.blue(),
    )

    embed.add_field(
        name="💬 Text Commands",
        value=(
            "`/kortana [message]` - Have a conversation\n"
            "`/ping` - Check my status\n"
            "`/help` - Show this help"
        ),
        inline=False,
    )

    if voice_orchestrator:
        embed.add_field(
            name="🎤 Voice Commands",
            value=(
                "`/join` - I'll join your voice channel\n"
                "`/speak [text]` - I'll speak specific text\n"
                "`/leave` - I'll leave the voice channel\n"
                "*When in voice: Use `/kortana` and I'll speak my responses!*"
            ),
            inline=False,
        )

    embed.add_field(
        name="ℹ️ About",
        value="I'm Kor'tana, an AI companion with memory and personality. I can remember our conversations and provide thoughtful responses.",
        inline=False,
    )

    embed.set_footer(text="Sacred AI Companion | Project Kor'tana")

    await interaction.response.send_message(embed=embed)


@bot.event
async def on_message(message):
    """Handle mentions"""
    if message.author.bot:
        return

    # Respond to mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        content = message.content.replace(f"<@{bot.user.id}>", "").strip()

        if not content:
            await message.reply("Yes? How can I help you?")
            return

        try:
            if chat_engine:
                async with message.channel.typing():
                    response = await chat_engine.process_message(
                        content,
                        user_id=str(message.author.id),
                        user_name=message.author.display_name,
                        channel="discord",
                    )
            else:
                response = (
                    f"Hello {message.author.display_name}! I heard you mention me."
                )

            await message.reply(response)

        except Exception as e:
            await message.reply(f"⚠️ Sorry, I'm having trouble right now: {str(e)}")

    await bot.process_commands(message)


# Run the bot
if __name__ == "__main__":
    print("=" * 80)
    print("🚀 STARTING KOR'TANA")
    print("=" * 80 + "\n")

    try:
        bot.run(token)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 80)
        print("👋 Kor'tana is shutting down gracefully...")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        input("Press Enter to exit...")
