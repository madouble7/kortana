import uuid

class RepairEngine:
    def __init__(self, task_manager):
        self.task_manager = task_manager

    def trigger_repair(self, repair_type, context):
        correlation_id = str(uuid.uuid4())
        task_data = {
            "type": repair_type,
            "context": context,
            "correlation_id": correlation_id
        }
        self.task_manager.dispatch(task_data)
        return correlation_id