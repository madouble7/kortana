from abc import ABC, abstractmethod

class QuantumLink(ABC):
    @abstractmethod
    async def sync_state(self, data: dict) -> bool:
        pass

    @abstractmethod
    async def handshake(self) -> bool:
        pass

class QuantumLinkImplementation(QuantumLink):
    def __init__(self):
        self.state = "initialized"

    async def sync_state(self, data: dict) -> bool:
        return True

    async def handshake(self) -> bool:
        self.state = "linked"
        return True