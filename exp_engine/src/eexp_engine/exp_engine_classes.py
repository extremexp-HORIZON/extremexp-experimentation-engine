import os

class WorkflowDataset:

    def __init__(self, name):
        self.name = name
        self.path = None

    def add_path(self, path):
        self.path = path

    def print(self, tab=""):
        print(f"{tab}\twith dataset name : {self.name}")
        print(f"{tab}\twith dataset path : {self.path}")


class WorkflowTask:

    def __init__(self, name):
        self.name = name
        self.params = {}
        self.order = None
        self.sub_workflow_name = None
        self.sub_workflow = None
        self.impl_file = None
        self.requirements_file = None
        self.python_version = None
        self.input_files = []
        self.output_files = []
        self.metrics = []
        self.dependent_modules = []
        self.dependencies = []
        self.conditional_dependencies = []
        self.prototypical_name = None
        self.if_task_name = None
        self.else_task_name = None
        self.continuation_task_name = None
        self.condition = None

    def add_conditional_dependency(self, task, condition):
        self.conditional_dependencies.append((task, condition))

    def set_conditional_tasks(self, task_if, task_else, task_continuation, condition):
        self.if_task_name = task_if
        self.else_task_name = task_else
        self.continuation_task_name = task_continuation
        self.condition = condition

    def is_condition_task(self):
        return self.condition is not None

    def add_implementation_file(self, impl_file):
        self.impl_file = impl_file

    def add_requirements_file(self, requirements_file):
        self.requirements_file = requirements_file

    def add_python_version(self, python_version):
        self.python_version = python_version

    def add_sub_workflow_name(self, workflow_name):
        self.sub_workflow_name = workflow_name

    def add_sub_workflow(self, workflow):
        self.sub_workflow = workflow

    def add_dependent_module(self, folder, name):
        dependent_module_path = os.path.join(folder, name)
        self.dependent_modules.append(dependent_module_path)

    def add_dependencies(self, dependencies):
        self.dependencies += dependencies

    def remove_dependency(self, dependency):
        self.dependencies.remove(dependency)

    def set_order(self, order):
        self.order = order

    def set_param(self, key, value):
        self.params[key] = value

    def add_metric(self, metric):
        self.metrics.append(metric)

    def clone(self, parsed_workflows=None):
        new_t = WorkflowTask(self.name)
        new_t.prototypical_name = self.prototypical_name
        new_t.add_implementation_file(self.impl_file)
        new_t.add_requirements_file(self.requirements_file)
        new_t.add_python_version(self.python_version)
        new_t.add_sub_workflow_name(self.sub_workflow_name)
        if self.sub_workflow_name:
            new_t.add_sub_workflow(next(w for w in parsed_workflows if w.name == self.sub_workflow_name).clone(parsed_workflows))
        new_t.add_dependencies(self.dependencies)
        new_t.input_files = self.input_files
        new_t.output_files = self.output_files
        for m in self.metrics:
            new_m = m.clone()
            new_t.add_metric(new_m)
        new_t.dependent_modules = self.dependent_modules
        new_t.set_order(self.order)
        new_t.params = self.params
        new_t.condition = self.condition
        new_t.if_task_name = self.if_task_name
        new_t.else_task_name = self.else_task_name
        new_t.continuation_task_name = self.continuation_task_name
        return new_t

    def print(self, tab=""):
        print(f"{tab}with task name : {self.name}")
        print(f"{tab}with task prototypical_name : {self.prototypical_name}")
        print(f"{tab}\twith task implementation: {self.impl_file}")
        print(f"{tab}\twith requirements_file: {self.requirements_file}")
        print(f"{tab}\twith python version: {self.python_version}")
        print(f"{tab}\twith sub_workflow_name: {self.sub_workflow_name}")
        print(f"{tab}\twith sub_workflow: {self.sub_workflow}")
        print(f"{tab}\twith dependencies: {self.dependencies}")
        print(f"{tab}\twith inputs:")
        for ds in self.input_files:
            ds.print(tab+"\t")
        print(f"{tab}\twith outputs:")
        for ds in self.output_files:
            ds.print(tab+"\t")
        print(f"{tab}\twith dependent modules: {self.dependent_modules}")
        print(f"{tab}\twith order: {self.order}")
        print(f"{tab}\twith params: {self.params}")
        print(f"{tab}\twith metrics:")
        for m in self.metrics:
            m.print(tab+"\t")
        # print(f"{tab}\twith condition: {self.condition}")
        # print(f"{tab}\twith if_task_name: {self.if_task_name}")
        # print(f"{tab}\twith else_task_name: {self.else_task_name}")
        # print(f"{tab}\twith continuation_task_name: {self.continuation_task_name}")


class Metric:

    def __init__(self, name, semantic_type, kind, data_type):
        self.name = name
        self.semantic_type = semantic_type
        self.kind = kind
        self.data_type = data_type

    def print(self, tab=""):
        print(f"{tab}\twith metric name : {self.name}")
        print(f"{tab}\twith metric semantic type : {self.semantic_type}")
        print(f"{tab}\twith metric kind : {self.kind}")
        print(f"{tab}\twith metric data_type : {self.data_type}")

    def clone(self):
        new_m = Metric(self.name, self.semantic_type, self.kind, self.data_type)
        return new_m


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
        print(f"{tab}Workflow with name: {self.name}")
        print(f"{tab}Workflow is main?: {self.is_main}")
        print(f"{tab}Workflow is flat?: {self.is_flat()}")
        for t in sorted(self.tasks, key=lambda t: t.order):
            t.print(tab+"\t")
            if t.sub_workflow:
                t.sub_workflow.print(tab+"\t\t")


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
