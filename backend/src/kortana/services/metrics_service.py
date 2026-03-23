from src.kortana.database import get_db_manager
from src.kortana.models import Metric
from datetime import datetime

class MetricsService:
    def __init__(self):
        self.db_manager = get_db_manager()

    async def save_metric(self, name: str, value: float, labels: dict | None = None):
        async for session in self.db_manager.get_session():
            metric = Metric(name=name, value=value, labels=labels, created_at=datetime.utcnow())
            session.add(metric)
            await session.commit()
            break
