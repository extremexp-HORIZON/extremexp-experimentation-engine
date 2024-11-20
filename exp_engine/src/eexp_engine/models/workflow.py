import logging
logger = logging.getLogger(__name__)


class Workflow:

    def __init__(self, name):
        self.is_main = None
        self.name = name
        self.tasks = []
        self.datasets = []

    def add_task(self, task):
        self.tasks.append(task)

    def add_dataset(self, dataset):
        self.datasets.append(dataset)

    def get_task(self, name):
        return next(t for t in self.tasks if t.name == name)

    def get_dataset(self, name):
        return next(ds for ds in self.datasets if ds.name == name)

    def is_flat(self):
        for t in self.tasks:
            if t.sub_workflow:
                return False
        return True

    def set_is_main(self, is_main):
        self.is_main = is_main

    def clone(self, parsed_workflows=None):
        new_w = Workflow(self.name)
        new_w.is_main = self.is_main
        for t in self.tasks:
            new_t = t.clone(parsed_workflows)
            new_w.tasks.append(new_t)
        return new_w

    def print(self, tab=""):
        logger.debug(f"{tab}Workflow with name: {self.name}")
        logger.debug(f"{tab}Workflow is main?: {self.is_main}")
        logger.debug(f"{tab}Workflow is flat?: {self.is_flat()}")
        for t in sorted(self.tasks, key=lambda t: t.order):
            t.print(tab+"\t")
            if t.sub_workflow:
                t.sub_workflow.print(tab+"\t\t")
