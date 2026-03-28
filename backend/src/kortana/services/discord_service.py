"""
KOR'TANA Discord Bot Service

Gives KOR'TANA a real-time presence on Discord. The bot:
  - Responds to messages with multi-provider AI consensus
  - Relays autonomy daemon events to a designated channel
  - Accepts slash commands for status, query, and task management
  - Runs alongside FastAPI in the same event loop (no separate process)

Requires: DISCORD_BOT_TOKEN in .env
Optional: DISCORD_CHANNEL_ID for autonomous event relay
"""

from __future__ import annotations

import asyncio
import os
from typing import Any

import discord
from discord import app_commands

from src.kortana.logger import get_logger

logger = get_logger(__name__)

# Intents required for message content access
INTENTS = discord.Intents.default()
INTENTS.message_content = True


class KortanaBot(discord.Client):
    """Discord bot that bridges KOR'TANA's AI and autonomy systems."""

    def __init__(self) -> None:
        super().__init__(intents=INTENTS)
        self.tree = app_commands.CommandTree(self)
        self._relay_channel_id: int | None = None
        self._ready_event = asyncio.Event()

        ch_id = os.getenv("DISCORD_CHANNEL_ID")
        if ch_id and ch_id.isdigit():
            self._relay_channel_id = int(ch_id)

        self._register_commands()

    # ---- lifecycle ----

    async def setup_hook(self) -> None:
        await self.tree.sync()

    async def on_ready(self) -> None:
        self._ready_event.set()
        logger.info(f"Discord bot online as {self.user} ({self.user.id if self.user else '?'})")
        if self._relay_channel_id:
            ch = self.get_channel(self._relay_channel_id)
            if ch and isinstance(ch, discord.TextChannel):
                await ch.send("**KOR'TANA** is online. Autonomy daemon engaged.")

    async def on_message(self, message: discord.Message) -> None:
        # Ignore own messages
        if message.author == self.user:
            return

        # Respond when mentioned or in DMs
        is_mentioned = self.user is not None and self.user.mentioned_in(message)
        is_dm = isinstance(message.channel, discord.DMChannel)

        if not (is_mentioned or is_dm):
            return

        # Strip mention from content
        content = message.content
        if self.user:
            content = content.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "").strip()

        if not content:
            await message.reply("I'm here. Ask me anything.")
            return

        async with message.channel.typing():
            try:
                from src.kortana.services.ai_consensus import (
                    ConsensusMode,
                    get_consensus_engine,
                )

                engine = get_consensus_engine()
                result = await engine.query(
                    content,
                    mode=ConsensusMode.FASTEST,
                    system="we are kor'tana, an autonomous ai agent. be concise and helpful.",
                    max_tokens=800,
                )

                answer = result.answer[:1900]  # Discord message limit
                provider_tag = (
                    result.provider_used
                    if isinstance(result.provider_used, str)
                    else ", ".join(result.provider_used)
                )
                await message.reply(f"{answer}\n-# *via {provider_tag} ({result.latency:.1f}s)*")
            except Exception as e:
                logger.error(f"Discord AI query failed: {e}")
                await message.reply(f"Error processing request: {e}")

    # ---- slash commands ----

    def _register_commands(self) -> None:
        @self.tree.command(name="status", description="KOR'TANA system status")
        async def status_cmd(interaction: discord.Interaction) -> None:
            await interaction.response.defer()
            try:
                from src.kortana.services.autonomy_daemon import get_autonomy_daemon

                daemon = get_autonomy_daemon()
                s = daemon.get_status()

                from src.kortana.services.ai_consensus import get_consensus_engine

                engine = get_consensus_engine()
                ai = engine.get_status()

                embed = discord.Embed(
                    title="KOR'TANA System Status",
                    color=0x00FF88 if s["running"] else 0xFF4444,
                )
                embed.add_field(
                    name="Autonomy Daemon",
                    value=f"{'Running' if s['running'] else 'Stopped'}\n"
                    f"Cycles: {s['cycles_completed']}\n"
                    f"Tasks: {s['tasks_succeeded']}/{s['tasks_processed']}",
                    inline=True,
                )
                embed.add_field(
                    name="AI Providers",
                    value=f"{ai['total_providers']} online\n"
                    f"Ranking: {', '.join(ai['ranking'][:3])}",
                    inline=True,
                )
                if s.get("last_cycle"):
                    embed.add_field(
                        name="Last Cycle",
                        value=f"{s['last_cycle']['duration_seconds']}s\n"
                        f"+{s['last_cycle']['new_issues']} issues\n"
                        f"{s['last_cycle']['succeeded']}/{s['last_cycle']['processed']} ok",
                        inline=True,
                    )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

        @self.tree.command(name="ask", description="Ask KOR'TANA a question")
        @app_commands.describe(
            question="Your question",
            mode="AI mode: fastest, best, or consensus",
        )
        @app_commands.choices(
            mode=[
                app_commands.Choice(name="Fastest", value="fastest"),
                app_commands.Choice(name="Best", value="best"),
                app_commands.Choice(name="Consensus", value="consensus"),
            ]
        )
        async def ask_cmd(
            interaction: discord.Interaction,
            question: str,
            mode: str = "fastest",
        ) -> None:
            await interaction.response.defer()
            try:
                from src.kortana.services.ai_consensus import (
                    ConsensusMode,
                    get_consensus_engine,
                )

                engine = get_consensus_engine()
                result = await engine.query(
                    question,
                    mode=ConsensusMode(mode),
                    system="we are kor'tana, an autonomous ai agent. be thorough but concise.",
                    max_tokens=1500,
                )

                answer = result.answer[:1900]
                provider_info = (
                    result.provider_used
                    if isinstance(result.provider_used, str)
                    else ", ".join(result.provider_used)
                )

                embed = discord.Embed(
                    title=f"KOR'TANA [{mode.upper()}]",
                    description=answer,
                    color=0x7B68EE,
                )
                embed.set_footer(
                    text=f"Provider: {provider_info} | "
                    f"{result.providers_succeeded}/{result.providers_queried} providers | "
                    f"{result.latency:.1f}s"
                )
                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

        @self.tree.command(name="tasks", description="View autonomous task queue")
        async def tasks_cmd(interaction: discord.Interaction) -> None:
            await interaction.response.defer()
            try:
                from sqlalchemy import func, select

                from src.kortana.database import get_db_manager
                from src.kortana.models import GitHubTask

                db = get_db_manager()
                async for session in db.get_session():
                    stmt = (
                        select(
                            GitHubTask.status, func.count()
                        )
                        .group_by(GitHubTask.status)
                    )
                    result = await session.execute(stmt)
                    counts = {str(status): count for status, count in result.all()}

                    # recent tasks
                    recent_stmt = (
                        select(GitHubTask)
                        .order_by(GitHubTask.created_at.desc())
                        .limit(5)
                    )
                    recent_result = await session.execute(recent_stmt)
                    recent = recent_result.scalars().all()

                embed = discord.Embed(title="Task Queue", color=0x00BFFF)
                status_text = "\n".join(
                    f"**{k}**: {v}" for k, v in counts.items()
                ) or "No tasks"
                embed.add_field(name="Status", value=status_text, inline=False)

                if recent:
                    task_lines = []
                    for t in recent:
                        emoji = {"pending": "", "executed": "", "failed": ""}.get(
                            str(t.status), ""
                        )
                        task_lines.append(
                            f"{emoji} #{t.github_issue_number} — {str(t.title)[:50]}"
                        )
                    embed.add_field(
                        name="Recent Tasks",
                        value="\n".join(task_lines),
                        inline=False,
                    )

                await interaction.followup.send(embed=embed)
            except Exception as e:
                await interaction.followup.send(f"Error: {e}")

    # ---- event relay (called by autonomy daemon) ----

    async def relay_event(self, event_type: str, data: dict[str, Any]) -> None:
        """Relay an autonomy daemon event to the configured Discord channel."""
        if not self._relay_channel_id:
            return
        await self._ready_event.wait()  # Wait until bot is ready

        ch = self.get_channel(self._relay_channel_id)
        if not ch or not isinstance(ch, discord.TextChannel):
            return

        emoji_map = {
            "cycle_start": "",
            "cycle_end": "",
            "task_progress": "",
            "task_complete": "",
            "error": "",
        }
        emoji = emoji_map.get(event_type, "")

        if event_type == "cycle_end":
            d = data
            msg = (
                f"{emoji} **Cycle Complete** — "
                f"{d.get('succeeded', 0)}/{d.get('processed', 0)} tasks, "
                f"+{d.get('new_issues', 0)} issues, "
                f"{d.get('duration_seconds', '?')}s"
            )
        elif event_type == "task_complete":
            msg = f"{emoji} **Task Done**: {data.get('title', '?')} — {data.get('status', '?')}"
        elif event_type == "error":
            msg = f"{emoji} **Error**: {str(data.get('error', '?'))[:200]}"
        else:
            msg = f"{emoji} `{event_type}`: {str(data)[:300]}"

        try:
            await ch.send(msg)
        except Exception as e:
            logger.warning(f"Discord relay failed: {e}")


# ---------------------------------------------------------------------------
# Singleton & launcher
# ---------------------------------------------------------------------------

_bot: KortanaBot | None = None


def get_discord_bot() -> KortanaBot | None:
    """Return the singleton bot instance, or None if token not configured."""
    global _bot
    if _bot is None:
        token = os.getenv("DISCORD_BOT_TOKEN")
        if not token:
            return None
        _bot = KortanaBot()
    return _bot


async def start_discord_bot() -> None:
    """Start the Discord bot in the current event loop (non-blocking)."""
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        logger.info("Discord bot disabled — no DISCORD_BOT_TOKEN")
        return

    bot = get_discord_bot()
    if bot is None:
        return

    async def _run() -> None:
        try:
            await bot.start(token)
        except Exception as e:
            logger.error(f"Discord bot crashed: {e}")

    asyncio.create_task(_run())
    logger.info("Discord bot task spawned")
