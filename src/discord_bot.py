import asyncio
import os
import sys

from dotenv import load_dotenv

import discord
from discord.ext import commands

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from kortana.brain import ChatEngine
except ImportError:
    print("Warning: Kor'tana brain not found. Using simple echo responses.")
    ChatEngine = None

# Load environment variables
load_dotenv(override=True)

# Bot configuration
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Initialize Kor'tana brain if available
chat_engine = ChatEngine() if ChatEngine else None

@bot.event
async def on_ready():
    print(f'🚀 Kor\'tana is online as {bot.user}')
    print(f'Bot ID: {bot.user.id}')
    print(f'Connected to {len(bot.guilds)} server(s)')

    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash command(s)')
    except Exception as e:
        print(f'Failed to sync commands: {e}')

@bot.tree.command(name="kortana", description="Chat with Kor'tana - Your Sacred AI Companion")
async def kortana_chat(interaction: discord.Interaction, message: str):
    """Main slash command for chatting with Kor'tana"""
    await interaction.response.defer()

    try:
        # Get user context
        user_id = str(interaction.user.id)
        user_name = interaction.user.display_name
        guild_name = interaction.guild.name if interaction.guild else "DM"

        print(f"[{guild_name}] {user_name}: {message}")

        # Generate response using Kor'tana brain
        if chat_engine:
            response = await asyncio.to_thread(
                chat_engine.generate_response,
                message,
                user_id=user_id,
                user_name=user_name,
                channel="discord"
            )
        else:
            response = f"Hello {user_name}! I'm Kor'tana, your Sacred AI Companion. (Echo mode: {message})"

        # Discord has a 2000 character limit
        if len(response) > 2000:
            response = response[:1997] + "..."

        # Create embed for better formatting
        embed = discord.Embed(
            title="🤖 Kor'tana",
            description=response,
            color=0x7B2CBF  # Purple color for Kor'tana
        )
        embed.set_footer(text="Sacred AI Companion")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        print(f"Error in kortana_chat: {e}")
        await interaction.followup.send("I'm experiencing some difficulties. Please try again in a moment.")

@bot.tree.command(name="ping", description="Check if Kor'tana is responsive")
async def ping_command(interaction: discord.Interaction):
    """Simple ping command"""
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🟢 Kor'tana is online! Latency: {latency}ms")

@bot.tree.command(name="help", description="Show Kor'tana commands and information")
async def help_command(interaction: discord.Interaction):
    """Help command"""
    embed = discord.Embed(
        title="🤖 Kor'tana - Sacred AI Companion",
        description="I'm here to assist you with thoughtful conversation and support.",
        color=0x7B2CBF
    )

    embed.add_field(
        name="Commands",
        value=(
            "`/kortana [message]` - Chat with me\n"
            "`/ping` - Check my status\n"
            "`/help` - Show this help message"
        ),
        inline=False
    )

    embed.add_field(
        name="Direct Interaction",
        value="You can also mention me (@Kor'tana) in any message to chat!",
        inline=False
    )

    embed.set_footer(text="Built with love for the Sacred Covenant")
    await interaction.response.send_message(embed=embed)

@bot.event
async def on_message(message):
    """Handle direct mentions and regular messages"""
    # Ignore bot messages
    if message.author == bot.user:
        return

    # Respond to direct mentions
    if bot.user in message.mentions:
        try:
            # Remove the mention from the message
            user_message = message.content.replace(f'<@{bot.user.id}>', '').strip()

            if not user_message:
                user_message = "Hello!"

            print(f"[{message.guild.name if message.guild else 'DM'}] {message.author.display_name}: {user_message}")

            # Generate response
            if chat_engine:
                response = await asyncio.to_thread(
                    chat_engine.generate_response,
                    user_message,
                    user_id=str(message.author.id),
                    user_name=message.author.display_name,
                    channel="discord"
                )
            else:
                response = f"Hello {message.author.display_name}! I'm Kor'tana. You said: {user_message}"

            # Discord character limit
            if len(response) > 2000:
                response = response[:1997] + "..."

            await message.reply(response)

        except Exception as e:
            print(f"Error in on_message: {e}")
            await message.reply("I'm experiencing some difficulties. Please try again.")

    # Process other commands
    await bot.process_commands(message)

@bot.event
async def on_guild_join(guild):
    """Welcome message when bot joins a server"""
    print(f"Joined new server: {guild.name} (ID: {guild.id})")

    # Find a channel to send welcome message
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

@bot.event
async def on_command_error(ctx, error):
    """Error handling for text commands"""
    print(f'Command error: {error}')

@bot.event
async def on_app_command_error(interaction, error):
    """Error handling for slash commands"""
    print(f'Slash command error: {error}')
    if not interaction.response.is_done():
        await interaction.response.send_message("An error occurred. Please try again.", ephemeral=True)

# Text commands (legacy support)
@bot.command(name='kortana')
async def kortana_text_command(ctx, *, message: str = "Hello!"):
    """Text command version for backwards compatibility"""
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

        if len(response) > 2000:
            response = response[:1997] + "..."

        await ctx.reply(response)

    except Exception as e:
        print(f"Error in text command: {e}")
        await ctx.reply("I'm experiencing some difficulties. Please try again.")

def main():
    """Main function to start the bot"""
    # Get Discord token from environment
    discord_token = os.getenv('DISCORD_BOT_TOKEN')

    if not discord_token:
        print("❌ ERROR: DISCORD_BOT_TOKEN not found in environment variables")
        print("Please add your Discord bot token to the .env file:")
        print("DISCORD_BOT_TOKEN=your_token_here")
        input("Press Enter to exit...")
        return

    print("🚀 Starting Kor'tana Discord Bot...")
    print("🔧 Backend engine:", "Kor'tana Brain" if chat_engine else "Echo Mode")
    print("📡 Connecting to Discord...")

    try:
        bot.run(discord_token)
    except discord.LoginFailure:
        print("❌ ERROR: Invalid Discord bot token")
        print("Please check your DISCORD_BOT_TOKEN in the .env file")
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
