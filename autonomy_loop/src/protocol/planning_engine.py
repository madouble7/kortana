import datetime
class PlanningEngine:
    def create_task(self, task_id, intent, objective, alignment_data):
        task = {
            "id": task_id,
            "intent": intent,
            "objective_link": objective,
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "directive_alignment": alignment_data
        }
        return task