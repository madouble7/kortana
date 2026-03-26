class SelfAwarenessService:
    async def log_incident(self, code: str, detail: str):
        # Centralized logging for autonomy failures
        print(f"[SELF-AWARENESS ALERT] {code}: {detail}")

self_awareness_service = SelfAwarenessService()