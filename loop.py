"""Main loop for processing incoming files based on the JSON configuration."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict

from watcher import Watcher, load_config


def _resolve_interval(config: Dict[str, Any]) -> float:
    try:
        interval = float(config["nudge_interval_seconds"])
    except KeyError as exc:
        raise KeyError("Missing 'nudge_interval_seconds' in configuration") from exc
    except (TypeError, ValueError) as exc:
        raise ValueError("Configuration value 'nudge_interval_seconds' must be numeric") from exc

    if interval <= 0:
        raise ValueError("Configuration value 'nudge_interval_seconds' must be greater than zero")

    return interval


def main(config_path: Path | None = None) -> None:
    """Run the processing loop using the configuration file."""
    config = load_config(config_path)
    interval = _resolve_interval(config)

    watcher = Watcher.from_config(config)

    while True:
        new_files = watcher.scan()
        if new_files:
            for file_path in new_files:
                print(f"Processing {file_path}")
        time.sleep(interval)


if __name__ == "__main__":
    main()
