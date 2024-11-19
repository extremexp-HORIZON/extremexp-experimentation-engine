class AutomatedEvent:
    def __init__(self, name, task, condition):
        self.name = name
        self.task = task
        self.condition = condition


class ManualEvent:
    def __init__(self, name, task, restart=False):
        self.name = name
        self.task = task
        self.restart = restart
