from dev_agent import execute_dev_task


class CodingAgent:
    def __init__(self, planner):
        self.planner = planner

    def execute_today(self):
        plan = self.planner.plan_day()
        results = {}
        for task in plan["today"]:
            results[task] = execute_dev_task(task)
        return results
