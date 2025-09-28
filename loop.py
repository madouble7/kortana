"""Loop module to poll nudges and send push notifications."""
from __future__ import annotations

import logging
import time
from typing import Any, Callable, Optional

import push  # type: ignore
import watcher  # type: ignore
import xp  # type: ignore


logger = logging.getLogger(__name__)


def _resolve_get_next_nudge() -> Callable[[], Any]:
    """Locate a ``get_next_nudge`` implementation from imported modules."""
    for module in (watcher, xp):
        candidate = getattr(module, "get_next_nudge", None)
        if callable(candidate):
            return candidate  # type: ignore[return-value]
    raise AttributeError("get_next_nudge() not found in watcher or xp modules")


def _send_notification(nudge: Any) -> None:
    push.push_notification(title="kor'tana nudge", message=nudge)


def run_loop(poll_interval: float = 60.0) -> None:
    """Continuously poll for nudges and push updates when they change."""
    get_next_nudge = _resolve_get_next_nudge()
    previous_nudge: Optional[Any] = None

    while True:
        try:
            nudge = get_next_nudge()
        except Exception as exc:  # pragma: no cover - defensive logging only
            logger.exception("Failed to fetch nudge: %s", exc)
            time.sleep(poll_interval)
            continue

        if nudge != previous_nudge:
            _send_notification(nudge)
            previous_nudge = nudge

        time.sleep(poll_interval)


if __name__ == "__main__":
    run_loop()
