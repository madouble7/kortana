"""File system watcher that relies on a shared JSON configuration."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_CONFIG_PATH = Path(__file__).resolve().with_name("config.json")


class Watcher:
    """Monitor a directory for new files.

    The watcher reads its target directory from the shared configuration so that
    both the watcher and any client loops work from the same settings.
    """

    def __init__(self, incoming_folder: Path) -> None:
        self.incoming_folder = incoming_folder
        self._seen_files: set[Path] = set()
        self.incoming_folder.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "Watcher":
        """Create a watcher instance using configuration values."""
        try:
            folder_value = config["incoming_folder"]
        except KeyError as exc:
            raise KeyError("Missing 'incoming_folder' in configuration") from exc

        incoming_folder = Path(str(folder_value)).expanduser()
        if not incoming_folder.is_absolute():
            incoming_folder = DEFAULT_CONFIG_PATH.parent / incoming_folder

        incoming_folder = incoming_folder.resolve()
        return cls(incoming_folder)

    def scan(self) -> List[Path]:
        """Return any new files discovered in the incoming directory."""
        discovered: List[Path] = []
        for file_path in self._iter_candidate_files():
            if file_path not in self._seen_files:
                self._seen_files.add(file_path)
                discovered.append(file_path)
        return discovered

    def _iter_candidate_files(self) -> Iterable[Path]:
        if not self.incoming_folder.exists():
            return ()

        for path in self.incoming_folder.iterdir():
            if path.is_file():
                yield path


def load_config(config_path: Path | None = None) -> Dict[str, Any]:
    """Load configuration from JSON file."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    with path.open("r", encoding="utf-8") as config_file:
        return json.load(config_file)
