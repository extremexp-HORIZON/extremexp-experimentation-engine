from ..data_abstraction_layer.data_abstraction_api import DataAbstractionClient
from ..executionware import proactive_runner, local_runner, kubeflow_runner
from ..models.experiment import *
import pprint
import itertools
import random
import time
import importlib
import logging
from multiprocessing import Process, Queue
import os
import sys

logger = logging.getLogger(__name__)

# Uniformly sample exactly k items from a (filtered) stream without knowing its length
def _reservoir_sample(iterable, k):
    res = []
    for i, item in enumerate(iterable, 1):  # 1-based index
        if i <= k:
            res.append(item)
        else:
            j = random.randint(1, i)
            if j <= k:
                res[j - 1] = item
    return res

class Execution:

    def __init__(self, exp_id, exp, assembled_flat_wfs, runner_folder, config, data_client: DataAbstractionClient, cancel_flag=None):
        self.exp_id = exp_id
        self.exp = exp
        self.assembled_flat_wfs = assembled_flat_wfs
        self.runner_folder = runner_folder
        self.config = config
        self.data = data_client
        self.results = {}
        self.run_count = 1
        self.queues_for_nodes = {}
        self.queues_for_workflows = {}
        self.subprocesses = 0
        self.cancel_flag = cancel_flag
        self.consecutive_connection_failures = 0
        self.max_consecutive_connection_failures = getattr(config, 'MAX_CONSECUTIVE_CONNECTION_FAILURES', 3)

    def _check_cancellation(self, context=""):
        """Check if experiment has been cancelled and raise exception if so."""
        if self.cancel_flag and self.cancel_flag.is_set():
            msg = f"Experiment {self.exp_id} cancelled"
            if context:
                msg += f" {context}"
            logger.info(msg)
            raise RuntimeError("Experiment cancelled by user")

    def _check_connection_failure(self, workflow_failed_with_connection_error):
        """Check if we should abort experiment due to consecutive connection failures.

        Args:
            workflow_failed_with_connection_error: Boolean indicating if the workflow failed due to connection error

        Raises:
            RuntimeError: If max consecutive connection failures exceeded
        """
        if workflow_failed_with_connection_error:
            self.consecutive_connection_failures += 1
            logger.warning(f"Connection failure {self.consecutive_connection_failures}/{self.max_consecutive_connection_failures}")

            if self.consecutive_connection_failures >= self.max_consecutive_connection_failures:
                msg = f"Aborting experiment {self.exp_id}: {self.consecutive_connection_failures} consecutive connection failures"
                logger.error(msg)
                raise RuntimeError(msg)
        else:
            # Reset counter on successful workflow execution
            self.consecutive_connection_failures = 0

    def evaluate_condition(self, condition_str):
        if condition_str == "True":
            return True
        if not self.config.PYTHON_CONDITIONS:
            logger.error("Cannot apply condition, missing PYTHON_CONDITIONS path in eexp_engine")
            logger.error("The default case in this case is to evaluate the condition as FALSE")
            return False
        else:
            condition_str_list = condition_str.split()
            cwd = os.getcwd()
            if cwd not in sys.path:
                sys.path.insert(0, cwd)
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
        """Entry point to execute the experiment control flow."""
        start_node = next(node for node in self.exp.control_node_containers if not node.is_next)
        self.data.update_experiment(self.exp_id, {"status": "running", "start": self.data.get_current_time()})
        try:
            self.execute_nodes_in_container(start_node)
            self.data.update_experiment(self.exp_id, {"status": "completed", "end": self.data.get_current_time()})
        except RuntimeError as e:
            # Handle both cancellation and circuit breaker exceptions
            logger.error(f"Experiment {self.exp_id} failed: {e}")
            self.data.update_experiment(self.exp_id, {"status": "failed", "end": self.data.get_current_time()})
            raise

    def execute_nodes_in_container_sequential_DEPRECATED(self, control_node_container):
        all_control_nodes = self.exp.spaces + self.exp.tasks + self.exp.interactions
        for node_name in control_node_container.parallel_node_names:
            node_to_execute = next(n for n in all_control_nodes if n.name==node_name)
            self.results[node_to_execute.name] = self.execute_node_sequential_DEPRECATED(node_to_execute)
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
        # Check for cancellation before executing nodes
        self._check_cancellation("before executing node container")

        all_control_nodes = self.exp.spaces + self.exp.tasks
        processes = []
        for node_name in control_node_container.parallel_node_names:
            # Check cancellation before each node
            self._check_cancellation(f"before executing node {node_name}")

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
            logger.error(f"Exception at subprocess: {e}")
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
        workflow_origin = "exp_interaction" if node.wf.tasks[0].taskType == "interactive" else "exp_task"
        wf_id = self.create_executed_workflow_in_db(node.wf, workflow_origin)
        self.run_count += 1

        queue_for_workflow = Queue()
        self.queues_for_workflows[wf_id] = queue_for_workflow
        p = Process(target=self.execute_wf, args=(node.wf, wf_id, queue_for_workflow, self.results))
        p.start()
        result_tuple = self.queues_for_workflows[wf_id].get()
        p.join()

        result, connection_error = result_tuple

        # Check circuit breaker for connection failures
        self._check_connection_failure(connection_error)

        self.data.update_workflow(wf_id, {"end": self.data.get_current_time()})
        self.data.update_metrics_of_workflow(wf_id, result)
        workflow_results = {}
        workflow_results["configuration"] = ()
        workflow_results["result"] = result
        node_results = {}
        node_results[1] = workflow_results
        return node_results

    def run_grid_search(self, node):
        # Streaming (lazy) path
        combo_iter = self._iter_base_combinations(node)
        # Preregister workflows lazily, one by one
        space_workflow_ids = self._preregister_workflows_streaming(node, combo_iter)
        # Execute scheduled workflows reconstructing from DB
        return self.run_scheduled_workflows_from_db(node, space_workflow_ids), self.run_count

    def run_random_search(self, node):
        """Randomly sample exactly K configurations from the filtered space (uniformly),
        without materializing the full cartesian product.

        Uses reservoir sampling over the filtered combination stream produced by
        _iter_base_combinations(node), so user-defined filters/generators are honored.
        """
        logger.debug("Using reservoir-sampled random search over filtered stream")
        vp_value_lists = self._build_vp_value_lists(node)
        # No variability points -> single empty configuration
        if not vp_value_lists:
            space_workflow_ids = self._preregister_workflows_streaming(node, iter([{}]))
            return self.run_scheduled_workflows_from_db(node, space_workflow_ids), self.run_count

        # Compute cartesian size upper bound (may be reduced by filters)
        total = 1
        for _, vals in vp_value_lists:
            total *= len(vals)
        sample_size = min(getattr(node, "runs", 1), total)

        # Stream filtered combinations and reservoir-sample K of them
        combo_iter = self._iter_base_combinations(node)
        sampled_combos = _reservoir_sample(combo_iter, sample_size)
        logger.info(
            f"Random search will run {len(sampled_combos)} sampled configuration(s) "
            f"(requested={sample_size}, max-space={total})."
        )

        # Preregister lazily from the sampled list and execute from DB
        space_workflow_ids = self._preregister_workflows_streaming(node, iter(sampled_combos))
        return self.run_scheduled_workflows_from_db(node, space_workflow_ids), self.run_count

    # --------- Lazy combination helpers ---------
    def _build_vp_value_lists(self, node):
        """Return list of tuples (vp_name, [values]) without cartesian expansion."""
        vp_value_lists = []
        for vp_name, vp in node.variability_points.items():
            values = []
            for value_generator in vp.value_generators:
                generator_type = value_generator[0]
                vp_data = value_generator[1]
                if generator_type == "enum":
                    values += vp_data["values"]
                elif generator_type == "range":
                    min_value = vp_data["min"]
                    max_value = vp_data["max"]
                    step_value = vp_data.get("step", 1) if vp_data["step"] != 0 else 1
                    values += list(range(min_value, max_value, step_value))
            vp_value_lists.append((vp_name, values))
        return vp_value_lists

    def _iter_base_combinations(self, node):
        """Yield combinations as dicts.
        """
        vp_value_lists = self._build_vp_value_lists(node)
        # No variability points: single empty combination. If filters exist we still must run them.
        if not vp_value_lists:
            base_iter = [{}]
        else:
            names = [n for (n, _) in vp_value_lists]
            lists = [vals for (_, vals) in vp_value_lists]
            if node.filter_function or node.generator_function:
                # Eager materialization required to satisfy user function signature.
                base_iter = [{n: v for n, v in zip(names, prod)} for prod in itertools.product(*lists)]
            else:
                # Pure lazy streaming path.
                for prod in itertools.product(*lists):
                    yield {n: v for n, v in zip(names, prod)}
                return

        # If we reach here we either had no variability points or we need to apply filters/generators.
        combos = list(base_iter)
        # Apply filter function if present
        if node.filter_function:
            if not self.config.PYTHON_CONFIGURATIONS:
                logger.error("Cannot filter configurations, missing PYTHON_CONFIGURATIONS path in eexp_engine")
            else:
                try:
                    python_configurations = importlib.import_module(self.config.PYTHON_CONFIGURATIONS)
                    filter_fn = getattr(python_configurations, node.filter_function)
                    logger.info(f"Filtering configurations of space {node.name} using function {node.filter_function}()")
                    combos = filter_fn(combos)
                except Exception as e:
                    logger.error(f"Error applying filter function {node.filter_function}: {e}")
        # Apply generator function if present (append generated configs)
        if node.generator_function:
            if not self.config.PYTHON_CONFIGURATIONS:
                logger.error("Cannot generate configurations, missing PYTHON_CONFIGURATIONS path in eexp_engine")
            else:
                try:
                    python_configurations = importlib.import_module(self.config.PYTHON_CONFIGURATIONS)
                    gen_fn = getattr(python_configurations, node.generator_function)
                    logger.info(f"Generating configurations for space {node.name} using function {node.generator_function}()")
                    generated = gen_fn()
                    if generated:
                        combos.extend(generated)
                except Exception as e:
                    logger.error(f"Error applying generator function {node.generator_function}: {e}")
        # Yield final list (still possibly small after filtering)
        # Deduplicate while preserving order
        seen = set()
        deduped = []
        for c in combos:
            key = frozenset(c.items())
            if key in seen:
                continue
            seen.add(key)
            deduped.append(c)
        if len(deduped) != len(combos):
            logger.info(f"Removed {len(combos) - len(deduped)} duplicate configuration(s) for space {node.name}")
        for c in deduped:
            yield c

    def _preregister_workflows_streaming(self, node, combo_iter):
        """Create workflows lazily, one by one, without retaining combinations/workflows in memory."""
        workflow_ids = []
        for c in combo_iter:
            logger.info(f"Run {self.run_count}")
            logger.info(f"Combination {c}")
            configured_workflow = self.get_workflow_to_run(node, c)
            workflow_id = self.create_executed_workflow_in_db(configured_workflow, node.name)
            workflow_ids.append(workflow_id)
            self.run_count += 1
        return workflow_ids

    def run_scheduled_workflows_from_db(self, node, space_workflow_ids):
        """Execute scheduled workflows for this space by reconstructing each workflow from DB task parameters."""
        import json
        space_results = {}
        run_count_in_space = 1
        # Cache configurations per wf_id to avoid recomputation
        config_by_wf_id = {}
        while True:
            # Check for cancellation in the workflow execution loop
            self._check_cancellation("during workflow execution")

            if len(space_workflow_ids) == 0:
                break
            processes = []
            launched_ids = []
            for wf_id in space_workflow_ids:
                if self.subprocesses == self.config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE:
                    break
                configured_workflow = self.get_workflow_configuration(wf_id, node, config_by_wf_id)
                self.data.update_workflow(wf_id, {"status": "running", "start": self.data.get_current_time()})
                queue_for_workflow = Queue()
                self.queues_for_workflows[wf_id] = queue_for_workflow
                p = Process(target=self.execute_wf, args=(configured_workflow, wf_id, queue_for_workflow, self.results))
                processes.append((wf_id, p))
                launched_ids.append(wf_id)
                p.start()
                self.subprocesses += 1
                time.sleep(1)
            results = {}
            for (wf_id, p) in processes:
                result_tuple = self.queues_for_workflows[wf_id].get()
                results[wf_id] = result_tuple
            for (wf_id, p) in processes:
                p.join()
                self.subprocesses -= 1
                result, connection_error = results[wf_id]
               
                # Check circuit breaker for connection failures
                self._check_connection_failure(connection_error)

                self.data.update_workflow(wf_id, {"end": self.data.get_current_time()})
                self.data.update_metrics_of_workflow(wf_id, result)
                if self.config.DATASET_MANAGEMENT == "DDM":
                    self.data.update_files_of_workflow(wf_id, result)
                workflow_results = {}
                workflow_results["configuration"] = config_by_wf_id.pop(wf_id, {})
                workflow_results["result"] = result
                space_results[run_count_in_space] = workflow_results
                # Free the per-workflow queue to avoid memory growth across many runs
                try:
                    del self.queues_for_workflows[wf_id]
                except KeyError:
                    pass
                run_count_in_space += 1
            # Remove launched ids so we don't reprocess them
            space_workflow_ids = [wid for wid in space_workflow_ids if wid not in launched_ids]
        return space_results

    def get_workflow_configuration(self, wf_id, node, config_by_wf_id):
        """Reconstruct configured workflow for wf_id using persisted task parameters.

        Caches configuration in config_by_wf_id to avoid recomputation.
        """
        # Fetch workflow document once
        wf_doc = self.data.get_workflow(wf_id)
        # Compute configuration dict from this document and cache it
        task_params = {}
        for t in wf_doc.get("tasks", []) or []:
            params_map = {}
            for p in t.get("parameters", []) or []:
                v = p.get("value")
                if p.get("type") == "integer":
                    try:
                        v = int(v)
                    except Exception:
                        pass
                params_map[p.get("name")] = v
            task_params[t.get("name")] = params_map
        config = {}
        for vt in node.variable_tasks:
            tname = vt.name
            mapping = vt.param_names_to_vp_names
            for param_name, vp_name in mapping.items():
                if tname in task_params and param_name in task_params[tname]:
                    config[vp_name] = task_params[tname][param_name]
        config_by_wf_id[wf_id] = config
        # Reconstruct configured workflow from the same document (no extra DB read)
        assembled_workflow = next(w for w in self.assembled_flat_wfs if w.name == node.assembled_workflow)
        configured_workflow = assembled_workflow.clone()
        for t in configured_workflow.tasks:
            t.params = {}
            if t.name in task_params:
                for k, v in task_params[t.name].items():
                    t.set_param(k, v)
        return configured_workflow

    def create_executed_workflow_in_db(self, workflow_to_run, workflow_origin):
        # data client already configured
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
                    input_file["name"] = f.name_in_task_signature
                    input_file["uri"] = f.path
                    metadata = {}
                    metadata["name_in_experiment"] = f.name
                    input_file["metadata"] = metadata
            if len(t.output_files) > 0:
                output_datasets = []
                t_spec["output_datasets"] = output_datasets
                for f in t.output_files:
                    output_file = {}
                    output_datasets.append(output_file)
                    output_file["name"] = f.name_in_task_signature
                    output_file["uri"] = f.path
                    metadata = {}
                    metadata["name_in_experiment"] = f.name
                    output_file["metadata"] = metadata
            for m in t.metrics:
                if t.name in wf_metrics:
                    wf_metrics[t.name].append(m)
                else:
                    wf_metrics[t.name] = [m]

        wf_metadata = {
            "wf_origin": workflow_origin
        }
        body = {
            "name": f"{self.exp_id}--w{self.run_count}",
            "tasks": task_specifications,
            "metadata": wf_metadata
        }
        wf_id = self.data.create_workflow(self.exp_id, body)

        for task in wf_metrics:
            for m in wf_metrics[task]:
                self.data.create_metric(wf_id, task, m.name, m.semantic_type, m.kind, m.data_type)

        return wf_id

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
                    logger.info(f"Setting param '{param_name}' of task '{t.name}' to '{c_dict[param_vp]}'")
                    t.set_param(param_name, c_dict[param_vp])
        return configured_workflow

    def execute_wf(self, w, wf_id, queue_for_workflow, results_so_far=None):
        connection_error_occurred = False
        try:
            if self.config.EXECUTIONWARE == "PROACTIVE":
                result = proactive_runner.execute_wf(w, self.exp_id, self.exp.name, wf_id, self.runner_folder, self.config, results_so_far)
            elif self.config.EXECUTIONWARE == "LOCAL":
                result = local_runner.execute_wf(w, self.exp_id, self.exp.name, wf_id, self.runner_folder, self.config)
            elif self.config.EXECUTIONWARE == "KUBEFLOW":
                result = kubeflow_runner.execute_wf(w, self.exp_id, self.exp.name, wf_id, self.runner_folder, self.config, results_so_far)
            else:
                logger.error("You need to setup an executionware")
                exit(0)
            # Convert result to a picklable format by creating a clean copy
            try:
                import json
                # Serialize and deserialize to create a clean, picklable copy
                clean_result = json.loads(json.dumps(result, default=str))
                queue_for_workflow.put((clean_result, connection_error_occurred))
                print(f"Successfully put clean result in queue for {wf_id}")
            except Exception as json_e:
                print(f"JSON serialization failed for {wf_id}: {json_e}, trying direct put")
                try:
                    queue_for_workflow.put((result, connection_error_occurred))
                    print(f"Successfully put original result in queue for {wf_id}")
                except Exception as pickle_e:
                    print(f"Pickling failed for {wf_id}: {pickle_e}, putting empty dict")
                    queue_for_workflow.put(({}, connection_error_occurred))
        except ConnectionError as e:
            connection_error_occurred = True
            logger.error(f"Connection error at subprocess for {wf_id}: {e}")
            print(f"Connection error occurred, putting empty dict with error flag in queue for {wf_id}")
            queue_for_workflow.put(({}, connection_error_occurred))
        except Exception as e:
            logger.error(f"Exception at subprocess: {e}")
            print(f"Exception occurred, putting empty dict in queue for {wf_id}")
            queue_for_workflow.put(({}, connection_error_occurred))


