from backend.src.kortana.services.self_awareness import self_awareness_service

class AutonomyPermissionError(Exception): pass

async def create_autonomy_branch(self, branch_name: str):
    try:
        return await self.client.create_branch(branch_name)
    except Exception as e:
        if getattr(e, 'status_code', None) == 403:
            await self_awareness_service.log_incident("AUTH_INSUFFICIENT_SCOPE", str(e))
            raise AutonomyPermissionError("GitHub token lacks write permissions.")
        raise