from ..data_abstraction_layer.data_abstraction_api import *
from ..executionware import proactive_runner, local_runner
from ..models.experiment import *
import pprint
import itertools
import random
import time
import importlib
from multiprocessing import Process, Queue

logger = logging.getLogger(__name__)


class Execution:

    def __init__(self, exp_id, exp, assembled_flat_wfs, runner_folder, config):
        self.exp_id = exp_id
        self.exp = exp
        self.assembled_flat_wfs = assembled_flat_wfs
        self.runner_folder = runner_folder
        self.config = config
        self.results = {}
        self.run_count = 1
        self.queues_for_nodes = {}
        self.queues_for_workflows = {}
        self.subprocesses = 0

    def evaluate_condition(self, condition_str):
        if condition_str == "True":
            return True
        if not self.config.PYTHON_CONDITIONS:
            logger.error("Cannot apply condition, missing PYTHON_CONDITIONS path in eexp_engine")
            logger.error("The default case in this case is to evaluate the condition as FALSE")
            return False
        else:
            condition_str_list = condition_str.split()
            python_conditions = importlib.import_module(self.config.PYTHON_CONDITIONS)
            condition = getattr(python_conditions, condition_str_list[0])
            args = condition_str_list[1:] + [self.results]
            return condition(*args)

    def execute_control_logic(self, node):
        if node.conditions_to_next_node_containers:
            for python_expression in node.conditions_to_next_node_containers:
                print(f"python_expression {python_expression}")
                if self.evaluate_condition(python_expression):
                    next_node = node.conditions_to_next_node_containers[python_expression]
                    self.execute_nodes_in_container(next_node)

    def start(self):
        start_node = next(node for node in self.exp.control_node_containers if not node.is_next)
        update_experiment(self.exp_id, {"status": "running", "start": get_current_time()})
        self.execute_nodes_in_container(start_node)
        update_experiment(self.exp_id, {"status": "completed", "end": get_current_time()})

    def execute_nodes_in_container_sequential_DEPRECATED(self, control_node_container):
        all_control_nodes = self.exp.spaces + self.exp.tasks + self.exp.interactions
        for node_name in control_node_container.parallel_node_names:
            node_to_execute = next(n for n in all_control_nodes if n.name==node_name)
            self.results[node_to_execute.name] = self.execute_node_sequential(node_to_execute)
            logger.info("Node executed")
            logger.info("Results so far")
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.results)
        self.execute_control_logic(control_node_container)

    def execute_node_sequential_DEPRECATED(self, node_to_execute):
        logger.info(f"executing node {node_to_execute.name}")
        if isinstance(node_to_execute, Space):
            logger.debug("executing a Space")
            return self.execute_space(node_to_execute)
        if isinstance(node_to_execute, ExpTask):
            logger.debug("executing an ExpTask")
            return self.execute_task(node_to_execute)

    def execute_nodes_in_container(self, control_node_container):
        all_control_nodes = self.exp.spaces + self.exp.tasks + self.exp.interactions
        processes = []
        for node_name in control_node_container.parallel_node_names:
            node_to_execute = next(n for n in all_control_nodes if n.name==node_name)
            node_queue = Queue()
            self.queues_for_nodes[node_name] = node_queue
            p = Process(target=self.execute_node, args=(node_to_execute, node_queue))
            processes.append((node_name, p))
            p.start()
            time.sleep(1)
        processes_results = {}
        for (node_name, p) in processes:
            result = self.queues_for_nodes[node_name].get()
            processes_results[node_name] = result
        for (node_name, p) in processes:
            p.join()
            result = processes_results[node_name]
            self.results[node_name] = result
            logger.info("Node executed")
            logger.info("Results so far")
            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(self.results)

        self.execute_control_logic(control_node_container)

    def execute_node(self, node_to_execute, node_queue):
        try:
            logger.info(f"executing node {node_to_execute.name}")
            if isinstance(node_to_execute, Space):
                logger.debug("executing a Space")
                result = self.execute_space(node_to_execute)
            if isinstance(node_to_execute, ExpTask):
                logger.debug("executing an ExpTask")
                result = self.execute_task(node_to_execute)
            node_queue.put(result)
        except Exception as e:
            print(f"Exception at subprocess: {e}")
            node_queue.put({})

    def execute_space(self, node):
        method_type = node.strategy
        if method_type == "gridsearch":
            logger.debug("Running gridsearch")
            space_results, self.run_count = self.run_grid_search(node)
        if method_type == "randomsearch":
            space_results, self.run_count = self.run_random_search(node)
        return space_results

    def execute_task(self, node):
        logger.debug(f"task: {node.name}")
        node.wf.print()
        wf_id = self.create_executed_workflow_in_db(node.wf)
        self.run_count += 1

        queue_for_workflow = Queue()
        self.queues_for_workflows[wf_id] = queue_for_workflow
        p = Process(target=self.execute_wf, args=(node.wf, wf_id, queue_for_workflow, self.results))
        p.start()
        result = self.queues_for_workflows[wf_id].get()
        p.join()

        workflow_results = {}
        workflow_results["configuration"] = ()
        workflow_results["result"] = result
        node_results = {}
        node_results[1] = workflow_results
        return node_results

    def run_grid_search(self, node):
        combinations = self.generate_combinations(node)
        print(f"\nGrid search generated {len(combinations)} configurations to run.\n")
        for combination in combinations:
            print(combination)
        return self.run_combinations(node, combinations)

    def run_random_search(self, node):
        combinations = self.generate_combinations(node)
        random_indexes = [random.randrange(len(combinations)) for i in range(node.runs)]
        random_combinations = [combinations[ri] for ri in random_indexes]
        print(f"\nRandom search generated {len(random_combinations)} configurations to run.\n")
        for c in random_combinations:
            print(c)
        return self.run_combinations(node, random_combinations)

    def generate_combinations(self, node):
        vp_combinations = []
        for vp_name, vp in node.variability_points.items():
            vp_values = []
            for value_generator in vp.value_generators:
                generator_type = value_generator[0]
                vp_data = value_generator[1]
                if generator_type == "enum":
                    vp_values += vp_data["values"]
                elif generator_type == "range":
                    min_value = vp_data["min"]
                    max_value = vp_data["max"]
                    step_value = vp_data.get("step", 1) if vp_data["step"] != 0 else 1
                    vp_values += list(range(min_value, max_value, step_value))
            vp_combinations.append([(vp_name, value) for value in vp_values])

        combinations = list(itertools.product(*vp_combinations))
        combinations = [dict(c) for c in combinations]

        if node.filter_function:
            if not self.config.PYTHON_CONFIGURATIONS:
                logger.error("Cannot filter configurations, missing PYTHON_CONFIGURATIONS path in eexp_engine")
            else:
                configuration_filter_str = node.filter_function
                python_configurations = importlib.import_module(self.config.PYTHON_CONFIGURATIONS)
                configurations_filter = getattr(python_configurations, configuration_filter_str)
                logger.info(f"Filtering configurations of space {node.name} using function {configuration_filter_str}()")
                combinations = configurations_filter(combinations)

        if node.generator_function:
            if not self.config.PYTHON_CONFIGURATIONS:
                logger.error("Cannot generate configurations, missing PYTHON_CONFIGURATIONS path in eexp_engine")
            else:
                configuration_generator_str = node.generator_function
                python_configurations = importlib.import_module(self.config.PYTHON_CONFIGURATIONS)
                configurations_generator = getattr(python_configurations, configuration_generator_str)
                logger.info(f"Generating configurations for space {node.name} using function {configuration_generator_str}()")
                combinations += configurations_generator()

        return combinations

    def run_combinations(self, node, combinations):
        configured_workflows_of_space = {}
        configurations_of_space = {}

        for c in combinations:
            print(f"Run {self.run_count}")
            print(f"Combination {c}")
            configured_workflow = self.get_workflow_to_run(node, c)
            wf_id = self.create_executed_workflow_in_db(configured_workflow)
            configured_workflows_of_space[wf_id] = configured_workflow
            configurations_of_space[wf_id] = c
            self.run_count += 1
        return self.run_scheduled_workflows(configured_workflows_of_space, configurations_of_space), self.run_count

    def create_executed_workflow_in_db(self, workflow_to_run):
        set_data_abstraction_config(self.config)
        task_specifications = []
        wf_metrics = {}
        for t in sorted(workflow_to_run.tasks, key=lambda t: t.order):
            t_spec = {}
            task_specifications.append(t_spec)
            t_spec["id"] = t.name
            t_spec["name"] = t.name
            metadata = {}
            metadata["prototypical_name"] = t.prototypical_name
            metadata["type"] = t.taskType
            t_spec["metadata"] = metadata
            t_spec["source_code"] = t.impl_file
            if len(t.params) > 0:
                params = []
                t_spec["parameters"] = params
                for name in t.params:
                    param = {}
                    params.append(param)
                    value = t.params[name]
                    param["name"] = name
                    param["value"] = str(value)
                    if type(value) is int:
                        param["type"] = "integer"
                    else:
                        param["type"] = "string"
            if len(t.input_files) > 0:
                input_datasets = []
                t_spec["input_datasets"] = input_datasets
                for f in t.input_files:
                    input_file = {}
                    input_datasets.append(input_file)
                    input_file["name"] = f.name
                    input_file["uri"] = f.path
                    metadata = {}
                    metadata["type"] = f.dataset_type
                    input_file["metadata"] = metadata
            if len(t.output_files) > 0:
                output_datasets = []
                t_spec["output_datasets"] = output_datasets
                for f in t.output_files:
                    output_file = {}
                    output_datasets.append(output_file)
                    output_file["name"] = f.name
                    output_file["uri"] = f.path
                    metadata = {}
                    metadata["type"] = f.dataset_type
                    output_file["metadata"] = metadata
            for m in t.metrics:
                if t.name in wf_metrics:
                    wf_metrics[t.name].append(m)
                else:
                    wf_metrics[t.name] = [m]
        body = {
            "name": f"{self.exp_id}--w{self.run_count}",
            "tasks": task_specifications
        }
        wf_id = create_workflow(self.exp_id, body)

        for task in wf_metrics:
            for m in wf_metrics[task]:
                create_metric(wf_id, task, m.name, m.semantic_type, m.kind, m.data_type)

        return wf_id

    def run_scheduled_workflows(self, configured_workflows_of_space, configurations_of_space):
        space_results = {}
        wf_ids = get_experiment(self.exp_id)["workflow_ids"]
        wf_ids_of_this_space = [w for w in wf_ids if w in configured_workflows_of_space.keys()]
        run_count_in_space = 1
        while True:
            scheduled_wf_ids = [wf_id for wf_id in wf_ids_of_this_space if get_workflow(wf_id)["status"] == "scheduled"]
            if len(scheduled_wf_ids) == 0:
                # all workflows have been executed
                break
            processes = []
            for wf_id in scheduled_wf_ids:
                if self.subprocesses == self.config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE:
                    # parallelization limit reached
                    break
                update_workflow(wf_id, {"status": "running", "start": get_current_time()})
                workflow_to_run = configured_workflows_of_space[wf_id]
                queue_for_workflow = Queue()
                self.queues_for_workflows[wf_id] = queue_for_workflow
                p = Process(target=self.execute_wf, args=(workflow_to_run, wf_id, queue_for_workflow))
                processes.append((wf_id, p))
                p.start()
                self.subprocesses += 1
                time.sleep(1)
            results = {}
            for (wf_id, p) in processes:
                result = self.queues_for_workflows[wf_id].get()
                results[wf_id] = result
            for (wf_id, p) in processes:
                p.join()
                self.subprocesses -= 1
                result = results[wf_id]
                update_workflow(wf_id, {"status": "completed", "end": get_current_time()})
                update_metrics_of_workflow(wf_id, result)
                workflow_results = {}
                workflow_results["configuration"] = configurations_of_space[wf_id]
                workflow_results["result"] = result
                space_results[run_count_in_space] = workflow_results
                # TODO fix this count in case of reordering
                run_count_in_space += 1
        return space_results

    def get_workflow_to_run(self, node, c_dict):
        assembled_workflow = next(w for w in self.assembled_flat_wfs if w.name == node.assembled_workflow)
        # TODO subclass the Workflow to capture different types (assembled, configured, etc.)
        configured_workflow = assembled_workflow.clone()
        for t in configured_workflow.tasks:
            t.params = {}
            variable_tasks = [vt for vt in node.variable_tasks if t.name==vt.name]
            if len(variable_tasks) == 1:
                variable_task = variable_tasks[0]
                for param_name, param_vp in variable_task.param_names_to_vp_names.items():
                    print(f"Setting param '{param_name}' of task '{t.name}' to '{c_dict[param_vp]}'")
                    t.set_param(param_name, c_dict[param_vp])
        return configured_workflow

    def execute_wf(self, w, wf_id, queue_for_workflow, results_so_far=None):
        try:
            if self.config.EXECUTIONWARE == "PROACTIVE":
                result = proactive_runner.execute_wf(w, self.exp_id, wf_id, self.runner_folder, self.config, results_so_far)
            elif self.config.EXECUTIONWARE == "LOCAL":
                result = local_runner.execute_wf(w, self.exp_id, wf_id, self.runner_folder, self.config)
            else:
                print("You need to setup an executionware")
                exit(0)
            queue_for_workflow.put(result)
        except Exception as e:
            print(f"Exception at subprocess: {e}")
            queue_for_workflow.put({})


