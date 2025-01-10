from ..data_abstraction_layer.data_abstraction_api import *
from ..executionware import proactive_runner, local_runner
import pprint
import itertools
import random

logger = logging.getLogger(__name__)


class Execution:

    def __init__(self, exp_id, nodes, automated_dict, spaces,
                 automated_events, parsed_automated_events,
                 manual_events, parsed_manual_events,
                 space_configs, assembled_flat_wfs,
                 runner_folder, config):
        self.exp_id = exp_id
        self.nodes = nodes
        self.automated_dict = automated_dict
        self.spaces = spaces
        self.automated_events = automated_events
        self.parsed_automated_events = parsed_automated_events
        self.manual_events = manual_events
        self.parsed_manual_events = parsed_manual_events
        self.space_configs = space_configs
        self.assembled_flat_wfs = assembled_flat_wfs
        self.results = {}
        global RUNNER_FOLDER, CONFIG, LOGGER
        RUNNER_FOLDER = runner_folder
        CONFIG = config

    def start(self):
        start_node = find_start_node(self.nodes, self.automated_dict)
        logger.info(f"Nodes: {self.nodes}")
        logger.info(f"Start Node: {start_node}")
        update_experiment(self.exp_id, {"status": "running", "start": get_current_time()})
        node = start_node
        result = self.execute_node(node)
        while node in self.automated_dict:
            next_action = self.automated_dict[node]
            node = next_action[result]
            result = self.execute_node(node)
        update_experiment(self.exp_id, {"status": "completed", "end": get_current_time()})

    def execute_node(self, node):
        logger.info(node)
        if node in self.spaces:
            return self.execute_space(node)
        elif node in self.automated_events:
            return self.execute_automated_event(node)
        elif node in self.manual_events:
            return self.execute_manual_event(node)

    def execute_space(self, node):
        logger.info("executing space")
        space_config = next((s for s in self.space_configs if s['name'] == node), None)
        logger.info('-------------------------------------------------------------------')
        logger.info(f"Running experiment of espace '{space_config['name']}' of type '{space_config['strategy']}'")
        method_type = space_config["strategy"]
        if method_type == "gridsearch":
            space_results = run_grid_search(space_config, self.exp_id, self.assembled_flat_wfs)
        if method_type == "randomsearch":
            space_results = run_random_search(space_config, self.exp_id, self.assembled_flat_wfs)
        if method_type =="singlerun":
            space_results = run_singlerun(space_config, self.exp_id)
        self.results[space_config['name']] = space_results
        logger.info("node executed")
        logger.info("Results so far")
        pp = pprint.PrettyPrinter(indent=4)
        pp.pprint(self.results)
        return 'True'

    def execute_automated_event(self, node):
        logger.info("executing automated event")
        e = next((e for e in self.parsed_automated_events if e.name == node), None)
        logger.info(e.task)
        module = __import__('IDEKO_events')
        func = getattr(module, e.task)
        ret = func(self.results)
        logger.info("--------------------------------------------------------------------")
        return ret

    def execute_manual_event(self, node):
        logger.info("executing manual event")
        e = next((e for e in self.parsed_manual_events if e.name == node), None)
        module = __import__('IDEKO_events')
        func = getattr(module, e.task)
        ret = func(self.automated_dict, self.space_configs, e.name)
        logger.info("--------------------------------------------------------------------")
        return ret


def run_grid_search(space_config, exp_id, assembled_flat_wfs):
    VPs = space_config["VPs"]
    vp_combinations = []

    for vp_data in VPs:
        if vp_data["type"] == "enum":
            vp_name = vp_data["name"]
            vp_values = vp_data["values"]
            vp_combinations.append([(vp_name, value) for value in vp_values])

        elif vp_data["type"] == "range":
            vp_name = vp_data["name"]
            min_value = vp_data["min"]
            max_value = vp_data["max"]
            step_value = vp_data.get("step", 1) if vp_data["step"] != 0 else 1
            vp_values = list(range(min_value, max_value, step_value))
            vp_combinations.append([(vp_name, value) for value in vp_values])

    # Generate combinations
    combinations = list(itertools.product(*vp_combinations))

    print(f"\nGrid search generated {len(combinations)} configurations to run.\n")
    for combination in combinations:
        print(combination)

    configured_workflows_of_space = {}
    configurations_of_space = {}

    run_count = 1
    for c in combinations:
        print(f"Run {run_count}")
        print(f"Combination {c}")
        configured_workflow = get_workflow_to_run(space_config, c, assembled_flat_wfs)
        wf_id = create_executed_workflow_in_db(exp_id, run_count, configured_workflow)
        configured_workflows_of_space[wf_id] = configured_workflow
        configurations_of_space[wf_id] = c
        run_count += 1
    return run_scheduled_workflows(exp_id, configured_workflows_of_space, configurations_of_space)


def create_executed_workflow_in_db(exp_id, run_count, workflow_to_run):
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
        if len(t.output_files) > 0:
            output_datasets = []
            t_spec["output_datasets"] = output_datasets
            for f in t.output_files:
                output_file = {}
                output_datasets.append(output_file)
                output_file["name"] = f.name
                output_file["uri"] = f.path
        for m in t.metrics:
            if t.name in wf_metrics:
                wf_metrics[t.name].append(m)
            else:
                wf_metrics[t.name] = [m]
    body = {
        "name": f"{exp_id}--w{run_count}",
        "tasks": task_specifications
    }
    wf_id = create_workflow(exp_id, body)

    for task in wf_metrics:
        for m in wf_metrics[task]:
            create_metric(wf_id, task, m.name, m.semantic_type, m.kind, m.data_type)

    return wf_id


def run_scheduled_workflows(exp_id, configured_workflows_of_space, configurations_of_space):
    exp = get_experiment(exp_id)
    workflows_count = len(exp["workflow_ids"])
    space_results = {}
    for attempts in range(workflows_count):
        wf_ids = get_experiment(exp_id)["workflow_ids"]
        wf_ids_of_this_space = [w for w in wf_ids if w in configured_workflows_of_space.keys()]
        run_count = 1
        for wf_id in wf_ids_of_this_space:
            workflow_to_run = configured_workflows_of_space[wf_id]
            if get_workflow(wf_id)["status"] == "scheduled":
                update_workflow(wf_id, {"status": "running", "start": get_current_time()})
                result = execute_wf(workflow_to_run, wf_id)
                update_workflow(wf_id, {"status": "completed", "end": get_current_time()})
                update_metrics_of_workflow(wf_id, result)
                workflow_results = {}
                workflow_results["configuration"] = configurations_of_space[wf_id]
                workflow_results["result"] = result
                space_results[run_count] = workflow_results
            # TODO fix this count in case of reordering
            run_count += 1
    return space_results


def run_random_search(space_config, exp_id, assembled_flat_wfs):
    # TODO not working, revisit this
    random_combinations = []

    vps = space_config['VPs']
    runs = space_config['runs']

    for i in range(runs):
        combination = []
        for vp in vps:
            vp_name = vp['name']
            min_val = vp['min']
            max_val = vp['max']

            value = random.randint(min_val, max_val)

            combination.append((vp_name, value))

        random_combinations.append(tuple(combination))

    print(f"\nRandom search generated {len(random_combinations)} configurations to run.\n")
    for c in random_combinations:
        print(c)

    run_count = 1
    space_results = {}
    for c in random_combinations:
        print(f"Run {run_count}")
        workflow_to_run = get_workflow_to_run(space_config, c, assembled_flat_wfs)
        result = execute_wf()
        workflow_results = {}
        workflow_results["configuration"] = c
        workflow_results["result"] = result
        space_results[run_count] = workflow_results
        print("..........")
        run_count += 1
    return space_results


def run_singlerun(space_config, exp_id):
    # TODO not working, revisit this
    print(f"Single Run")
    # w = next(w for w in assembled_flat_wfs if w.name == space_config["assembled_workflow"])
    print(space_config)
    result = execute_wf()
    workflow_results = []
    workflow_results = result
    print(workflow_results)


def get_workflow_to_run(space_config, c, assembled_flat_wfs):
    c_dict = dict(c)
    assembled_workflow = next(w for w in assembled_flat_wfs if w.name == space_config["assembled_workflow"])
    # TODO subclass the Workflow to capture different types (assembled, configured, etc.)
    configured_workflow = assembled_workflow.clone()
    for t in configured_workflow.tasks:
        t.params = {}
        if t.name in space_config["tasks"].keys():
            task_config = space_config["tasks"][t.name]
            for param_name, param_vp in task_config.items():
                print(f"Setting param '{param_name}' of task '{t.name}' to '{c_dict[param_vp]}'")
                t.set_param(param_name, c_dict[param_vp])
    return configured_workflow


def execute_wf(w, wf_id):
    if CONFIG.EXECUTIONWARE == "PROACTIVE":
        return proactive_runner.execute_wf(w, wf_id, RUNNER_FOLDER, CONFIG)
    if CONFIG.EXECUTIONWARE == "LOCAL":
        return local_runner.execute_wf(w, wf_id, RUNNER_FOLDER, CONFIG)

def find_start_node(nodes, automated_dict):
    values = automated_dict.values()
    if len(values) == 0:
        # if the control is trivial, just pick the first node
        return list(nodes)[0]
    for n in automated_dict:
        if n not in values:
            return n
