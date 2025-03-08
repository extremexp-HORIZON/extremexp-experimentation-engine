import logging
logger = logging.getLogger(__name__)


class Experiment:

    def __init__(self, name):
        self.name = name
        self.intent = None
        self.spaces = []
        self.tasks = []
        self.interactions = []
        self.control_node_containers = []

    def set_intent(self, intent):
        self.intent = intent

    def add_space(self, space):
        self.spaces.append(space)

    def add_task(self, name, wf):
        task = ExpTask(name, wf)
        self.tasks.append(task)

    def add_control_node_container(self, control_node):
        self.control_node_containers.append(control_node)

    def get_control_node_container(self, names):
        return next(cn for cn in self.control_node_containers if cn.equals(names))

    def has_control_node_container(self, names):
        for control_node in self.control_node_containers:
            if control_node.equals(names):
                return True
        return False

    def print_control_node_container(self, node, tab):
        node.print(tab)
        for python_expression in node.conditions_to_next_node_containers:
            next_node = node.conditions_to_next_node_containers[python_expression]
            logger.debug(f"{tab}\t--> {next_node.to_string()} ({python_expression})")

    def traverse_and_print_control_node_container(self, node, tab):
        if node.conditions_to_next_node_containers:
            tab += '\t'
            for python_expression in node.conditions_to_next_node_containers:
                next_node = node.conditions_to_next_node_containers[python_expression]
                self.print_control_node_container(next_node, tab)
                self.traverse_and_print_control_node_container(next_node, tab)

    def traverse_and_print_control_node_containers(self, tab):
            logger.debug(f"{tab}control_node_containers:")
            node = next(node for node in self.control_node_containers if not node.is_next)
            self.print_control_node_container(node, tab)
            self.traverse_and_print_control_node_container(node, tab)

    def print(self, tab=""):
        logger.debug(f"{tab}name : {self.name}")
        logger.debug(f"{tab}intent: {self.intent}")
        logger.debug(f"{tab}spaces:")
        for space in self.spaces:
            space.print(tab+"\t")
        logger.debug(f"{tab}tasks:")
        for task in self.tasks:
            task.print(tab+"\t")
        logger.debug(f"{tab}interactions:")
        for interaction in self.interactions:
            interaction.print(tab+"\t")
        self.traverse_and_print_control_node_containers(tab)


class ControlNodeContainer:

    def __init__(self, parallel_node_names):
        self.parallel_node_names = parallel_node_names
        self.is_next = False
        self.conditions_to_next_node_containers = {}

    def add_parallel_node_name(self, node_name):
        self.parallel_node_names.append(node_name)

    def add_next(self, next_node_container, next_node_container_condition):
        self.conditions_to_next_node_containers[next_node_container_condition] = next_node_container
        next_node_container.set_is_next()

    def set_is_next(self):
        self.is_next = True

    def print(self, tab=""):
        logger.debug(f"{tab}\t{', '.join(self.parallel_node_names)}")

    def to_string(self):
        return ', '.join(self.parallel_node_names)

    def equals(self, other_control_node_names):
        return set(self.parallel_node_names) == set(other_control_node_names)


class ControlNode:

    def __init__(self, name):
        self.name = name


class Space(ControlNode):

    class VariableTask:

        def __init__(self, name):
            self.name = name
            self.param_names_to_vp_names = {}

        def add_param(self, param_name, vp_name):
            self.param_names_to_vp_names[param_name] = vp_name

        def print(self, tab=""):
            logger.debug(f"{tab}name : {self.name}")
            logger.debug(f"{tab}param_names_to_vp_names:")
            for param_name in self.param_names_to_vp_names.keys():
                logger.debug(f"{tab}\t{param_name} --> {self.param_names_to_vp_names[param_name]}")

    class VariabilityPoint:

        def __init__(self, name):
            self.name = name
            self.value_generators = []

        def add_value_generator(self, generator_type, vp_data):
            self.value_generators.append((generator_type, vp_data))

        def print(self, tab=""):
            logger.debug(f"{tab}name : {self.name}")
            for value_generator in self.value_generators:
                logger.debug(f"{tab}\tgenerator_type : {value_generator[0]}")
                logger.debug(f"{tab}\tvp_data:")
                for vp_datum in value_generator[1].keys():
                    logger.debug(f"{tab}\t\t{vp_datum} --> {value_generator[1][vp_datum]}")

    def __init__(self, name):
        super().__init__(name)
        self.name = name
        self.assembled_workflow = None
        self.strategy = None
        self.runs = None
        self.filter_function = None
        self.generator_function = None
        self.variable_tasks = []
        self.variability_points = {}

    def set_assembled_workflow(self, assembled_workflow):
        self.assembled_workflow = assembled_workflow

    def set_strategy(self, strategy):
        self.strategy = strategy

    def set_runs(self, runs):
        self.runs = runs

    def set_filter_function(self, filter_function):
        self.filter_function = filter_function

    def set_generator_function(self, generator_function):
        self.generator_function = generator_function

    def add_task_param_to_vp_mapping(self, name, param_name, vp_name):
        if name in [t.name for t in self.variable_tasks]:
            t = next(t for t in self.variable_tasks if t.name==name)
        else:
            t = self.VariableTask(name)
            self.variable_tasks.append(t)
        t.add_param(param_name, vp_name)

    def add_variability_point(self, vp_name, vp_type, vp_data):
        if vp_name in self.variability_points.keys():
            vp = self.variability_points[vp_name]
        else:
            vp = self.VariabilityPoint(vp_name)
            self.variability_points[vp_name] = vp
        vp.add_value_generator(vp_type, vp_data)

    def print(self, tab=""):
        logger.debug(f"{tab}name : {self.name}")
        logger.debug(f"{tab}strategy : {self.strategy}")
        logger.debug(f"{tab}runs : {self.runs}")
        logger.debug(f"{tab}filter_function : {self.filter_function}")
        logger.debug(f"{tab}generator_function : {self.generator_function}")
        logger.debug(f"{tab}variable_tasks:")
        for t in self.variable_tasks:
            t.print(tab+"\t")
        logger.debug(f"{tab}variability_points:")
        for vp in self.variability_points.keys():
            self.variability_points[vp].print(tab+"\t")
        logger.debug(f"{tab}---------------------------------")


class ExpTask(ControlNode):
    """ Abstraction for both automated and interactive tasks at the experiment level """

    def __init__(self, name, wf):
        super().__init__(name)
        self.name = name
        self.wf = wf

    def print(self, tab=""):
        logger.debug(f"{tab}name : {self.name}")

