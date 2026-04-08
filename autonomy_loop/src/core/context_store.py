class ContextStore:
    def __init__(self):
        self.state = {}

    def get_latest_state(self):
        return self.state

    def update_state(self, task_context):
        self.state.update({'last_processed': task_context, 'updated': True})