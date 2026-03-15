#!/usr/bin/env python
"""
Direct Kor'tana Discord Bot Launcher
Bypasses import issues and runs the bot directly
"""

import os
import sys

# Make sure we can import from src
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

print("\n" + "=" * 80)
print("🤖 KOR'TANA DISCORD BOT - DIRECT LAUNCHER")
print("=" * 80 + "\n")

# Load environment first
print("Loading environment...")
from dotenv import load_dotenv

load_dotenv(override=True)

# Check token
token = os.getenv("DISCORD_BOT_TOKEN")
if not token:
    print("❌ ERROR: DISCORD_BOT_TOKEN not found in .env")
    print("Please run: python setup_discord_bot_quick.py")
    input("Press Enter to exit...")
    sys.exit(1)

print("✅ Token loaded\n")

# Import discord DIRECTLY (not from src)
print("Loading discord.py...")
try:
    import discord
    from discord.ext import commands

    print("✅ discord.py loaded successfully\n")
except ImportError as e:
    print(f"❌ Failed to load discord.py: {e}")
    print("\nInstalling discord.py...")
    result = os.system(f'"{sys.executable}" -m pip install --quiet discord.py')
    if result != 0:
        print("❌ Failed to install discord.py")
        input("Press Enter to exit...")
        sys.exit(1)

    # Try importing again
    try:
        import discord
        from discord.ext import commands

        print("✅ discord.py installed and loaded successfully\n")
    except ImportError as e2:
        print(f"❌ Still can't import discord.py: {e2}")
        print("\nThis might be a Python path issue.")
        print("Please check if you have a file named 'discord.py' in this directory.")
        input("Press Enter to exit...")
        sys.exit(1)

# Configure bot
print("Configuring bot...")
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)


# Define events and commands
@bot.event
async def on_ready():
    """Bot ready event"""
    print(f"\n🚀 Kor'tana is online as {bot.user}")
    print(f"Bot ID: {bot.user.id}")
    print(f"Connected to {len(bot.guilds)} server(s)")

    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} slash command(s)\n")
    except Exception as e:
        print(f"Failed to sync commands: {e}\n")


@bot.tree.command(name="ping", description="Check if Kor'tana is responsive")
async def ping_command(interaction: discord.Interaction):
    """Ping command"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(
        f"🟢 Kor'tana is online! Latency: {latency}ms"
    )


@bot.tree.command(
    name="kortana", description="Chat with Kor'tana - Your Sacred AI Companion"
)
async def kortana_chat(interaction: discord.Interaction, message: str):
    """Kortana chat command"""
    await interaction.response.defer()

    try:
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        guild_name = interaction.guild.name if interaction.guild else "DM"

        print(f"[{guild_name}] {user_name}: {message}")

        # Simple echo for now
        response = f"Hello {user_name}! You said: {message}"

        if len(response) > 2000:
            response = response[:1997] + "..."

        embed = discord.Embed(title="🤖 Kor'tana", description=response, color=0x7B2CBF)
        embed.set_footer(text="Sacred AI Companion")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error in kortana_chat: {e}")
        await interaction.followup.send(
            "I'm experiencing some difficulties. Please try again."
        )


@bot.tree.command(name="help", description="Show Kor'tana commands")
async def help_command(interaction: discord.Interaction):
    """Help command"""
    embed = discord.Embed(
        title="🤖 Kor'tana - Sacred AI Companion",
        description="I'm here to assist you with thoughtful conversation.",
        color=0x7B2CBF,
    )

    embed.add_field(
        name="Commands",
        value=(
            "`/kortana [message]` - Chat with me\n"
            "`/ping` - Check my status\n"
            "`/help` - Show this help message"
        ),
        inline=False,
    )

    embed.set_footer(text="Built with love for the Sacred Covenant")
    await interaction.response.send_message(embed=embed)


@bot.event
async def on_guild_join(guild):
    """When bot joins a server"""
    print(f"Joined new server: {guild.name} (ID: {guild.id})")

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            embed = discord.Embed(
                title="🤖 Kor'tana has arrived!",
                description=(
                    "Hello! I'm Kor'tana, your Sacred AI Companion.\n\n"
                    "Use `/kortana [message]` to chat with me!\n"
                    "Type `/help` to see all commands."
                ),
                color=0x7B2CBF,
            )
            await channel.send(embed=embed)
            break


# Start the bot
print("✅ Bot configured\n")
print("=" * 80)
print("🚀 STARTING BOT")
print("=" * 80 + "\n")

try:
    bot.run(token)
except KeyboardInterrupt:
    print("\n\n🛑 Bot stopped by user")
except discord.LoginFailure:
    print("\n❌ ERROR: Invalid Discord bot token")
    print("Please check your DISCORD_BOT_TOKEN in .env")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback

    traceback.print_exc()
