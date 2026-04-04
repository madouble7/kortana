"""
Standalone autonomy daemon entrypoint.

Run as a separate process so the web API and the autonomy loop have
independent lifetimes — a web deploy/restart no longer interrupts the
daemon, and a daemon crash cannot take down the HTTP server.

Usage (Procfile / Railway daemon service):
    python -m src.kortana.daemon_worker

Environment variables:
    AUTONOMY_DAEMON_ENABLED   — master kill-switch; "false" suppresses the loop
                                 entirely (default "true" when this process runs).
    AUTONOMY_CYCLE_INTERVAL   — seconds between cycles (default 60).
    LOG_LEVEL                 — e.g. "INFO" (default).
    LOG_FORMAT                — "json" | "plain" (default "json").

The web process no longer starts the daemon automatically. It only does so
when KORTANA_DAEMON_IN_PROCESS=true is set explicitly.
"""

from __future__ import annotations

import asyncio
import signal
import sys


async def run() -> None:
    from src.kortana.config import get_settings
    from src.kortana.logger import get_logger, setup_logging

    settings = get_settings()
    setup_logging(
        getattr(settings, "LOG_LEVEL", "INFO"),
        getattr(settings, "LOG_FORMAT", "json"),
    )
    logger = get_logger(__name__)

    # ------------------------------------------------------------------
    # Graceful shutdown: honour SIGTERM (Railway/Docker) and SIGINT (Ctrl-C)
    # ------------------------------------------------------------------
    shutdown_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, shutdown_event.set)
        except (NotImplementedError, OSError):
            # Windows does not support add_signal_handler for all signals;
            # KeyboardInterrupt still works via the except below.
            pass

    # ------------------------------------------------------------------
    # Database initialisation
    # ------------------------------------------------------------------
    try:
        from src.kortana.database import get_db_manager

        db_manager = get_db_manager()
        await db_manager.initialize()
        logger.info("Database initialised")
    except Exception as exc:
        logger.exception(f"Database init failed, cannot start daemon: {exc}")
        sys.exit(1)

    # ------------------------------------------------------------------
    # Start the autonomy daemon loop
    # ------------------------------------------------------------------
    from src.kortana.services.autonomy_daemon import get_autonomy_daemon

    daemon = get_autonomy_daemon()
    await daemon.start()

    if not daemon._running:
        # Daemon is disabled (AUTONOMY_DAEMON_ENABLED=false master kill-switch).
        # Exit cleanly rather than waiting forever on the shutdown event.
        logger.info("Autonomy daemon is disabled — daemon worker exiting")
        return

    logger.info("Autonomy daemon worker online — waiting for shutdown signal")

    try:
        await shutdown_event.wait()
    except asyncio.CancelledError:
        pass
    except KeyboardInterrupt:
        pass

    logger.info("Shutdown signal received — stopping daemon gracefully")
    await daemon.stop()
    logger.info("Autonomy daemon worker stopped cleanly")


if __name__ == "__main__":
    asyncio.run(run())
