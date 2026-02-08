"""Voice processing error definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class VoiceProcessingError(Exception):
    """Structured voice processing exception."""

    code: str
    message: str
    details: dict[str, Any] | None = None
    status_code: int = 400

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "details": self.details or {},
        }
