from abc import ABC, abstractmethod
from typing import Any, Dict


class Skill(ABC):
    """Abstract base class for skills.

    A Skill should be able to say whether it can handle a given intent and produce
    a response for that intent.
    """

    @property
    def name(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def can_handle(self, intent: str, data: Dict[str, Any] | None = None) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def handle(self, intent: str, data: Dict[str, Any] | None = None) -> str:
        raise NotImplementedError()
