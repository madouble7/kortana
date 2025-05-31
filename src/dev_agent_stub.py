class DevAgentStub:
    def execute_dev_task(self, task_description: str) -> dict:
        """
        Simulate code generation for a given task description.
        Returns a dictionary with status, code_generated (if success), and log.
        """
        if not task_description or not isinstance(task_description, str):
            return {
                "status": "failure",
                "error": "Invalid or empty task description.",
                "log": "Dev task failed.",
            }
        # Simulate success for any non-empty string
        return {
            "status": "success",
            "code_generated": f'# Placeholder code for: {task_description}\nprint("Task: {task_description}")',
            "log": "Dev task completed successfully.",
        }
