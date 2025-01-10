import logging
logger = logging.getLogger(__name__)


class Task:

    def __init__(self, name):
        self.name = name
        self.taskType = None
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
        self.prototypical_inputs = []
        self.prototypical_outputs = []
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

    def set_type(self, taskType):
        self.taskType = taskType

    def add_sub_workflow_name(self, workflow_name):
        self.sub_workflow_name = workflow_name

    def add_sub_workflow(self, workflow):
        self.sub_workflow = workflow

    def add_dependent_module(self, folder, name):
        import os
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

    def add_prototypical_inputs(self, prototypical_inputs):
        self.prototypical_inputs = prototypical_inputs

    def add_prototypical_outputs(self, prototypical_outputs):
        self.prototypical_outputs = prototypical_outputs

    def clone(self, parsed_workflows=None):
        new_t = Task(self.name)
        new_t.set_type(self.taskType)
        new_t.prototypical_name = self.prototypical_name
        new_t.prototypical_inputs = self.prototypical_inputs
        new_t.prototypical_outputs = self.prototypical_outputs
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
        logger.debug(f"{tab}with name : {self.name}")
        logger.debug(f"{tab}\twith type: {self.taskType}")
        logger.debug(f"{tab}\twith prototypical name : {self.prototypical_name}")
        logger.debug(f"{tab}\twith prototypical inputs : {self.prototypical_inputs}")
        logger.debug(f"{tab}\twith prototypical outputs : {self.prototypical_outputs}")
        logger.debug(f"{tab}\twith implementation: {self.impl_file}")
        logger.debug(f"{tab}\twith requirements_file: {self.requirements_file}")
        logger.debug(f"{tab}\twith python version: {self.python_version}")
        logger.debug(f"{tab}\twith sub_workflow_name: {self.sub_workflow_name}")
        logger.debug(f"{tab}\twith sub_workflow: {self.sub_workflow}")
        logger.debug(f"{tab}\twith dependencies: {self.dependencies}")
        logger.debug(f"{tab}\twith inputs:")
        for ds in self.input_files:
            ds.print(tab+"\t")
        logger.debug(f"{tab}\twith outputs:")
        for ds in self.output_files:
            ds.print(tab+"\t")
        logger.debug(f"{tab}\twith dependent modules: {self.dependent_modules}")
        logger.debug(f"{tab}\twith order: {self.order}")
        logger.debug(f"{tab}\twith params: {self.params}")
        logger.debug(f"{tab}\twith metrics:")
        for m in self.metrics:
            m.print(tab+"\t")
        # logger.debug(f"{tab}\twith condition: {self.condition}")
        # logger.debug(f"{tab}\twith if_task_name: {self.if_task_name}")
        # logger.debug(f"{tab}\twith else_task_name: {self.else_task_name}")
        # logger.debug(f"{tab}\twith continuation_task_name: {self.continuation_task_name}")
