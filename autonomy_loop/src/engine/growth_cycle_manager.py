from src.protocols.quantum_link_interface import QuantumLinkImplementation

class GrowthCycleManager:
    def __init__(self):
        self.link = QuantumLinkImplementation()

    async def run_cycle(self, data):
        if await self.link.handshake():
            return await self.link.sync_state(data)
        return False