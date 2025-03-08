from ..models.workflow import Workflow
from ..models.task import Task
from ..models.dataset import Dataset
from ..models.metric import Metric
from ..models.experiment import Experiment
from ..models.experiment import Space
from ..models.experiment import ControlNodeContainer
from .. import exceptions
import os
import textx
import logging

CONFIG = {}
logger = logging.getLogger(__name__)
packagedir = os.path.dirname(os.path.abspath(__file__))
GRAMMAR_PATH = os.path.join(packagedir, "../grammar/workflow_grammar.tx")
TASK_GRAMMAR_PATH = os.path.join(packagedir, "../grammar/task_grammar.tx")
KNOWN_TASK_INPUTS = ['dependent_modules_folders']


def process_dependencies(task_dependencies, nodes, parsing_node_type, verbose_logging=False):
    if verbose_logging:
        logger.info(parsing_node_type)
    for n1, n2 in zip(nodes[0::1], nodes[1::1]):
        if verbose_logging:
            logger.info(str(n2.name), ' depends on ', str(n1))
        if n2.name in task_dependencies:
            logger.info(f"{parsing_node_type}: Double dependency ({n2.name}), check your specification")
            # exit(0)
        else:
            # TODO what about tasks with multiple dependencies?
            task_dependencies[n2.name] = [n1.name]


def add_input_output_data(wf, firstNode, firstData, firstData2, firstData3, secondNode, secondData, secondData1, secondData2):
    if secondNode:
        if firstNode:
            '''  Grammar rule: firstNode=[Node] '.' firstData2=ID '-->' secondNode=[Node] '.' secondData2=ID ';' '''
            task1 = wf.get_task(firstNode.name)
            output_dataset = Dataset(firstData2)
            output_dataset.set_name_in_task_signature(firstData2)
            task1.output_files.append(output_dataset)

            task2 = wf.get_task(secondNode.name)
            input_dataset = Dataset(secondData2)
            input_dataset.set_name_in_task_signature(secondData2)
            input_dataset.set_name_in_generating_task(firstData2)
            task2.input_files.append(input_dataset)

            if task1.impl_file:
                check_whether_dataflow_respects_task_signatures(task1.name, task1.prototypical_inputs, task1.prototypical_outputs, task1.input_files, task1.output_files)
            if task2.impl_file:
                check_whether_dataflow_respects_task_signatures(task2.name, task2.prototypical_inputs, task2.prototypical_outputs, task2.input_files, task2.output_files)

        else:
            ''' Grammar rule: firstData=[Data] '-->' secondNode=[Node] '.' secondData1=ID ';' '''
            task = wf.get_task(secondNode.name)
            ds = wf.get_dataset(firstData.name)
            ds.set_name_in_task_signature(secondData1)
            task.input_files.append(ds)
            if task.impl_file:
                check_whether_dataflow_respects_task_signatures(task.name, task.prototypical_inputs, task.prototypical_outputs, task.input_files, task.output_files)
    else:
        ''' Grammar rule: firstNode=[Node] '.' firstData3=ID '-->' secondData=[Data] ';' '''
        task = wf.get_task(firstNode.name)
        ds = wf.get_dataset(secondData.name)
        ds.set_name_in_task_signature(firstData3)
        task.output_files.append(ds)
        if task.impl_file:
            check_whether_dataflow_respects_task_signatures(task.name, task.prototypical_inputs, task.prototypical_outputs, task.input_files, task.output_files)



def apply_task_dependencies_and_set_order(wf, task_dependencies):
    for t in wf.tasks:
        if t.name in task_dependencies.keys():
            t.add_dependencies(task_dependencies[t.name])
    re_order_tasks_in_workflow(wf)


def re_order_tasks_in_workflow(wf):
    first_task = [t for t in wf.tasks if not t.dependencies][0]
    order = 0
    first_task.set_order(order)
    dependent_tasks = [t for t in wf.tasks if first_task.name in t.dependencies]
    while dependent_tasks:
        order += 1
        new_dependent_tasks = []
        for dependent_task in dependent_tasks:
            dependent_task.set_order(order)
            new_dependent_tasks += [t for t in wf.tasks if dependent_task.name in t.dependencies]
        dependent_tasks = new_dependent_tasks


def find_dependent_tasks(wf, task, dependent_tasks):
    for t in wf.tasks:
        if task.name in t.dependencies:
            dependent_tasks.append(t)
        if t.sub_workflow:
            find_dependent_tasks(t.sub_workflow, task, dependent_tasks)
    return dependent_tasks


def exists_parent_workflow(wfs, wf_name):
    for wf in wfs:
        if wf_name in [task.sub_workflow.name for task in wf.tasks if task.sub_workflow]:
            return True
    return False


def set_is_main_attribute(wfs):
    for wf in wfs:
        wf.set_is_main(not exists_parent_workflow(wfs, wf.name))


def check_if_subworkflow_input_matches_use_in_parent_workflow(subworkflow, first_task):
    expected_inputs = [ds.name for ds in first_task.input_files]
    for ds in subworkflow.input_files:
        if ds.name not in expected_inputs:
            raise exceptions.InputDataInSubWorkflowDoesNotMatchOutputDataOfParentWorkflow(
                f"Expected one of '{expected_inputs}' but found '{ds.name}' as input of subworkflow '{subworkflow.name}'")


def check_if_subworkflow_output_matches_use_in_parent_workflow(subworkflow, last_task):
    expected_outputs = [ds.name for ds in last_task.output_files]
    for ds in subworkflow.output_files:
        if ds.name not in expected_outputs:
            raise exceptions.OutputDataInSubWorkflowDoesNotMatchInputDataOfParentWorkflow(
                f"Expected one of '{expected_outputs}' but found '{ds.name}' as output of subworkflow '{subworkflow.name}'")


def get_underlying_tasks(t, assembled_wf, tasks_to_add):
    i = 0
    for task in sorted(t.sub_workflow.tasks, key=lambda t: t.order):
        if not task.sub_workflow:
            if i==0:
                check_if_subworkflow_input_matches_use_in_parent_workflow(t, task)
                logger.info(f"{t.dependencies} --> {t.name} -->  becomes {t.dependencies} --> {task.name}")
                task.add_dependencies(t.dependencies)
                ''' This is for correctly resolving data dependencies in subworkflows '''
                for ds in task.input_files:
                    dataset_with_name_in_generating_task = next((d for d in t.input_files if d.name==ds.name), None)
                    if dataset_with_name_in_generating_task:
                        ds.set_name_in_generating_task(dataset_with_name_in_generating_task.name_in_generating_task)
                ''' ----------------------------------------------------------------- '''
            if i==len(t.sub_workflow.tasks)-1:
                dependent_tasks = find_dependent_tasks(assembled_wf, t, [])
                dep = [t.name for t in dependent_tasks]
                check_if_subworkflow_output_matches_use_in_parent_workflow(t, task)
                logger.info(f"{t.name} --> {dep} becomes {task.name} --> {dep}")
                for dependent_task in dependent_tasks:
                    ''' This is for correctly resolving data dependencies in subworkflows '''
                    for ds in dependent_task.input_files:
                        dataset_with_name_in_generating_task = next((d for d in task.output_files if d.name==ds.name_in_generating_task), None)
                        if dataset_with_name_in_generating_task:
                            ds.set_name_in_generating_task(dataset_with_name_in_generating_task.name_in_task_signature)
                    ''' ----------------------------------------------------------------- '''
                    dependent_task.remove_dependency(t.name)
                    dependent_task.add_dependencies([task.name])
            tasks_to_add.append(task)
        else:
            get_underlying_tasks(task, assembled_wf, tasks_to_add)
        i += 1
    return tasks_to_add


def flatten_workflows(assembled_wf):
    logger.info(f"Flattening assembled workflow with name {assembled_wf.name}")
    new_wf = Workflow(assembled_wf.name)
    for t in assembled_wf.tasks:
        if t.sub_workflow:
            logger.info(t.sub_workflow.name)
            tasks_to_add = get_underlying_tasks(t, assembled_wf, [])
            for t in tasks_to_add:
                new_wf.add_task(t)
        else:
            new_wf.add_task(t)
    re_order_tasks_in_workflow(new_wf)
    new_wf.set_is_main(True)
    return new_wf


def check_whether_dataflow_respects_task_signatures(name, prototypical_inputs, prototypical_outputs, input_files, output_files):
    for i in input_files:
        if i.name_in_task_signature not in prototypical_inputs:
            raise exceptions.InputDataInWorkflowDoesNotMatchSignature(
                f"Expected one of '{prototypical_inputs}' but found '{i.name_in_task_signature}' as input of task '{name}'")
    for o in output_files:
        if o.name_in_task_signature not in prototypical_outputs:
            raise exceptions.OutputDataInWorkflowDoesNotMatchSignature(
                f"Expected one of '{prototypical_outputs}' but found '{o.name_in_task_signature}' as output of task '{name}'")


def generate_final_assembled_workflows(parsed_workflows, assembled_wfs_data):
    new_wfs = []
    for assembled_wf_data in assembled_wfs_data:
        wf = next(w for w in parsed_workflows if w.name == assembled_wf_data["parent"]).clone(parsed_workflows)
        wf.name = assembled_wf_data["name"]
        new_wfs.append(wf)
        logger.info(wf.name)
        for task in wf.tasks:
            if task.name in assembled_wf_data["tasks"].keys():
                logger.info(f"Need to configure task '{task.name}'")
                task_data = assembled_wf_data["tasks"][task.name]
                logger.info(f"Changing prototypical_name of task '{task.name}' to '{task_data['prototypical_name']}'")
                task.prototypical_name = task_data["prototypical_name"]
                logger.info(f"Changing implementation of task '{task.name}' to '{task_data['implementation']}'")
                task.add_implementation_file(task_data["implementation"])
                if "metrics" in task_data:
                    logger.info(f"Changing metrics of task '{task.name}' to '{task_data['metrics']}'")
                    for metric in task_data['metrics']:
                        task.add_metric(metric)
                if "requirements_file" in task_data:
                    logger.info(f"Changing requirements file of task '{task.name}' to '{task_data['requirements_file']}'")
                    task.add_requirements_file(task_data["requirements_file"])
                if "python_version" in task_data:
                    logger.info(f"Changing python version of task '{task.name}' to '{task_data['python_version']}'")
                    task.add_python_version(task_data["python_version"])
                if "taskType" in task_data:
                    logger.info(f"Changing type of task '{task.name}' to '{task_data['taskType']}'")
                    task.set_type(task_data["taskType"])
                if "prototypical_inputs" in task_data:
                    logger.info(f"Changing prototypical_inputs of task '{task.name}' to '{task_data['prototypical_inputs']}'")
                    task.add_prototypical_inputs(task_data["prototypical_inputs"])
                if "prototypical_outputs" in task_data:
                    logger.info(f"Changing prototypical outputs of task '{task.name}' to '{task_data['prototypical_outputs']}'")
                    task.add_prototypical_outputs(task_data["prototypical_outputs"])
                if "dependency" in task_data:
                    logger.info(f"Changing dependency of task '{task.name}' to '{task_data['dependency']}'")
                    task.add_dependent_module(CONFIG.PYTHON_DEPENDENCIES_RELATIVE_PATH, task_data["dependency"])
                check_whether_dataflow_respects_task_signatures(task.name, task.prototypical_inputs, task.prototypical_outputs, task.input_files, task.output_files)
            else:
                logger.info(f"Do not need to configure task '{task.name}'")
            if task.sub_workflow:
                # For now, we cannot configure a subworkflow TODO
                pass
        logger.info("-------------------------------")
    return new_wfs


def generate_assembled_flat_workflows(assembled_wfs, assembled_flat_wfs):
    for wf in assembled_wfs:
        flat_wf = flatten_workflows(wf)
        assembled_flat_wfs.append(flat_wf)
        flat_wf.print()


def get_task_metadata(implementation):
    folder_path = os.path.join(CONFIG.TASK_LIBRARY_PATH, implementation)
    return parse_task(folder_path)


def get_task_subworkflow_path(implementation):
    return os.path.join(CONFIG.EXPERIMENT_LIBRARY_PATH, implementation + '.xxp')


def check_python_code_use_of_task_signature(task_name, implementation_file_path, inputs, outputs, params):
    inputs_outputs_params = inputs + outputs + params
    with open(implementation_file_path, 'r') as source_code:
        for line in source_code:
            if "variables.get" in line:
                variable_name = line.split("variables.get(")[1].split(")")[0].strip()
                variable_name = (variable_name [1:-1])
                if variable_name not in KNOWN_TASK_INPUTS and variable_name not in inputs_outputs_params:
                    raise exceptions.SourceCodeAttemptsToReadVariableNotInTaskSignature(
                        f"Variable '{variable_name}' not found in the signature ('{inputs_outputs_params}') of task '{task_name}'")
            if "load_datasets" in line:
                dataset_names = [(name.strip() [1:-1]) for name in (line.split("load_datasets(")[1].strip() [:-1]).split(",") if name != "variables"]
                for ds in dataset_names:
                    if ds not in inputs:
                        raise exceptions.SourceCodeAttemptsToLoadDatasetNotInTaskSignature(
                            f"Dataset '{ds}' not found in the inputs ('{inputs}') of task '{task_name}'")
            if "save_datasets" in line:
                dataset_names = [name.strip() for name in (line.split("save_datasets(")[1].strip() [:-1]).split(",") if name != "variables"]
                dataset_names = [((ds [1:]).strip() [1:-1]) for ds in dataset_names if ds.startswith("(")]
                for ds in dataset_names:
                    if ds not in outputs:
                        raise exceptions.SourceCodeAttemptsToSaveDatasetNotInTaskSignature(
                            f"Dataset '{ds}' not found in the outputs ('{outputs}') of task '{task_name}'")


def parse_task(folder_path):
    file_path = os.path.join(folder_path, 'task.xxp')
    with open(file_path, 'r') as task_file:
        task_dsl= task_file.read()
    workflow_metamodel = textx.metamodel_from_file(TASK_GRAMMAR_PATH)
    workflow_model = workflow_metamodel.model_from_str(task_dsl)
    parsed_data = {}
    metrics, params, inputs, outputs = [], [], [], []
    parsed_data["metrics"] = metrics
    parsed_data["params"] = params
    parsed_data["prototypical_inputs"] = inputs
    parsed_data["prototypical_outputs"] = outputs
    for component in workflow_model.component:
        if component.__class__.__name__ == "Task":
            parsed_data["task_name"] = component.name
        for e in component.elements:
            if e.__class__.__name__ == "InputData":
                inputs.append(e.name)
            if e.__class__.__name__ == "OutputData":
                outputs.append(e.name)
            if e.__class__.__name__ == "Implementation":
                if e.filename:
                    implementation_file_path = os.path.join(CONFIG.TASK_LIBRARY_PATH, e.filename)
                    parsed_data["implementation_file_path"] = implementation_file_path
                    if not os.path.exists(implementation_file_path):
                        raise exceptions.ImplementationFileNotFound(f"{implementation_file_path}")
            if e.__class__.__name__ == "Metric":
                metric = Metric(e.name, e.semantic_type, e.kind, e.data_type)
                metrics.append(metric)
            if e.__class__.__name__ == "Parameter":
                params.append(e.name)
            if e.__class__.__name__ == "VirtualEnv":
                if e.requirements_file_path:
                    parsed_data["requirements_file"] = os.path.join(CONFIG.TASK_LIBRARY_PATH, e.requirements_file_path)
            if e.__class__.__name__ == "PythonVersion":
                if e.python_version:
                    parsed_data["python_version"] = e.python_version
            if e.__class__.__name__ == "Dependency":
                if e.dependency:
                    parsed_data["dependency"] = e.dependency
            if e.__class__.__name__ == "Type":
                if e.taskType:
                    parsed_data["taskType"] = e.taskType
    if "taskType" not in parsed_data:
        parsed_data["taskType"] = "custom"
    check_python_code_use_of_task_signature(parsed_data["task_name"], parsed_data["implementation_file_path"],
                                            parsed_data["prototypical_inputs"], parsed_data["prototypical_outputs"],
                                            parsed_data["params"])
    return parsed_data


def get_workflow_components(experiments_metamodel, experiment_model, parsed_workflows, task_dependencies):
    for component in experiment_model.component:
        if component.__class__.__name__ == 'Workflow':
            wf = Workflow(component.name)

            parsed_workflows.append(wf)

            for e in component.elements:
                if e.__class__.__name__ == "Task":
                    task = Task(e.name)
                    wf.add_task(task)

                if e.__class__.__name__ == "Data":
                    ds = Dataset(e.name)
                    wf.add_dataset(ds)

                if e.__class__.__name__ == "ConfigureTask":
                    task = wf.get_task(e.alias.name)

                if e.__class__.__name__ == "Task" or e.__class__.__name__ == "ConfigureTask":
                    if e.filename:
                        actual_path = e.filename.replace(".", os.sep)
                        parsed_data = get_task_metadata(actual_path)
                        implementation_file_path = parsed_data["implementation_file_path"]
                        if not os.path.exists(implementation_file_path):
                            raise exceptions.ImplementationFileNotFound(
                                f"{implementation_file_path} in task {e.alias.name}")
                        for metric in parsed_data["metrics"]:
                            task.add_metric(metric)
                        task.prototypical_name = parsed_data["task_name"]
                        task.add_implementation_file(parsed_data["implementation_file_path"])
                        task.add_requirements_file(parsed_data.get("requirements_file"))
                        task.add_python_version(parsed_data.get("python_version"))
                        task.set_type(parsed_data.get("taskType"))
                        task.add_prototypical_inputs(parsed_data.get("prototypical_inputs"))
                        task.add_prototypical_outputs(parsed_data.get("prototypical_outputs"))
                        if "dependency" in parsed_data:
                            task.add_dependent_module(CONFIG.PYTHON_DEPENDENCIES_RELATIVE_PATH, parsed_data.get("dependency"))
                    if e.subworkflow:
                        task_subworkflow_path = get_task_subworkflow_path(e.subworkflow)
                        with open(task_subworkflow_path) as file:
                            workflow_specification = file.read()
                            subworkflow_model = experiments_metamodel.model_from_str(workflow_specification)
                            sub_wf, parsed_workflows, task_dependencies = get_workflow_components(experiments_metamodel,subworkflow_model,parsed_workflows,task_dependencies)
                            task.add_sub_workflow(sub_wf)
                            task.add_sub_workflow_name(sub_wf.name)

                if e.__class__.__name__ == "ConfigureData":
                    ds = wf.get_dataset(e.alias.name)
                    dataset_relative_path = os.path.join(CONFIG.DATASET_LIBRARY_RELATIVE_PATH, e.path)
                    ds.add_path(dataset_relative_path)
                    if e.dataset_type:
                        ds.set_dataset_type(e.dataset_type)

                if e.__class__.__name__ == "StartAndEndEvent":
                    process_dependencies(task_dependencies, e.nodes, "StartAndEndEvent")

                if e.__class__.__name__ == "StartEvent":
                    process_dependencies(task_dependencies, e.nodes, "StartEvent")

                if e.__class__.__name__ == "EndEvent":
                    process_dependencies(task_dependencies, e.nodes, "EndEvent")

                if e.__class__.__name__ == "TaskLink":
                    process_dependencies(task_dependencies, [e.initial_node] + e.nodes, "TaskLink")

                if e.__class__.__name__ == "DataLink":
                    add_input_output_data(wf, e.firstNode, e.firstData, e.firstData2, e.firstData3,
                                          e.secondNode, e.secondData, e.secondData1, e.secondData2)

                if e.__class__.__name__ == "ConditionLink":
                    condition = e.condition
                    fromNode = e.from_node
                    ifNode = e.if_node
                    elseNode = e.else_node
                    contNode = e.continuation_Node

                    conditional_task = wf.get_task(e.from_node.name)
                    conditional_task.set_conditional_tasks(ifNode.name, elseNode.name, contNode.name, condition)

    return wf, parsed_workflows, task_dependencies


def parse_workflows(experiment_specification):
    parsed_workflows = []
    task_dependencies = {}

    experiments_metamodel = textx.metamodel_from_file(GRAMMAR_PATH)
    experiment_model = experiments_metamodel.model_from_str(experiment_specification)

    _, parsed_workflows, task_dependencies = get_workflow_components(experiments_metamodel, experiment_model, parsed_workflows, task_dependencies)

    for wf in parsed_workflows:
        apply_task_dependencies_and_set_order(wf, task_dependencies)

    set_is_main_attribute(parsed_workflows)

    for wf in parsed_workflows:
        for t in wf.tasks:
            print(t.name)
        wf.print()

    return parsed_workflows, task_dependencies


def parse_assembled_workflow_data(experiment_specification):
    experiments_metamodel = textx.metamodel_from_file(GRAMMAR_PATH)
    experiment_model = experiments_metamodel.model_from_str(experiment_specification)

    assembled_workflows_data = []
    for component in experiment_model.component:
        if component.__class__.__name__ == 'AssembledWorkflow':
            assembled_workflow_data = {}
            assembled_workflows_data.append(assembled_workflow_data)
            assembled_workflow_data["name"] = component.name
            assembled_workflow_data["parent"] = component.parent_workflow.name
            assembled_workflow_tasks = {}
            assembled_workflow_data["tasks"] = assembled_workflow_tasks

            configurations = component.tasks

            while configurations:
                for config in component.tasks:
                    assembled_workflow_task = {}
                    if config.subworkflow:
                        # TODO not supported for now
                        None
                    elif config.filename:
                        actual_file = config.filename.replace(".", os.sep)
                        parsed_data = get_task_metadata(actual_file)
                        task_file_path = parsed_data["implementation_file_path"]
                        if not os.path.exists(task_file_path):
                            raise exceptions.ImplementationFileNotFound(
                                f"{task_file_path} in task {config.task.name}")
                        assembled_workflow_task["prototypical_name"] = parsed_data["task_name"]
                        assembled_workflow_task["implementation"] = task_file_path
                        properties = ["metrics", "requirements_file", "python_version",
                                      "taskType", "prototypical_inputs", "prototypical_outputs", "dependency"]
                        for property in properties:
                            if property in parsed_data:
                                assembled_workflow_task[property] = parsed_data.get(property)
                        assembled_workflow_tasks[config.task.name] = assembled_workflow_task
                    configurations.remove(config)


    from pprint import pformat
    logger.debug(pformat(assembled_workflows_data))

    return assembled_workflows_data


def extract_parallel_node_names(n):
    node_names = []
    if n.single_node:
        node_names.append(n.single_node.name)
    if n.node_one and n.rest_nodes:
        node_names.append(n.node_one.name)
        for rest_node in n.rest_nodes:
            node_names.append(rest_node.name)
    return node_names


def create_if_needed_control_node_container(exp, names):
    if exp.has_control_node_container(names):
        node = exp.get_control_node_container(names)
    else:
        node = ControlNodeContainer(names)
        exp.add_control_node_container(node)
    return node


def process_control_node_dependencies(exp, nodes, condition="True"):
    if len(nodes)==1:
        node_names = extract_parallel_node_names(nodes[0])
        logger.debug(f"single node names: {node_names}")
        create_if_needed_control_node_container(exp, node_names)
    else:
        for n1, n2 in zip(nodes[0::1], nodes[1::1]):
            n1_node_names = extract_parallel_node_names(n1)
            n2_node_names = extract_parallel_node_names(n2)
            logger.debug(f"n1_node_names: {n1_node_names}")
            logger.debug(f"n2_node_names: {n2_node_names}")
            node1 = create_if_needed_control_node_container(exp, n1_node_names)
            node2 = create_if_needed_control_node_container(exp, n2_node_names)
            node1.add_next(node2, condition)


def get_experiment_task(node):
    wf = Workflow(node.name)
    # TODO support composite experiment tasks
    if node.implementation:
        task = Task(node.name)
        wf.add_task(task)
        actual_path = node.implementation.replace(".", os.sep)
        parsed_data = get_task_metadata(actual_path)
        implementation_file_path = parsed_data["implementation_file_path"]
        if not os.path.exists(implementation_file_path):
            raise exceptions.ImplementationFileNotFound(
                f"{implementation_file_path} in task {node.name}")
        for metric in parsed_data["metrics"]:
            task.add_metric(metric)
        task.prototypical_name = parsed_data["task_name"]
        task.add_implementation_file(parsed_data["implementation_file_path"])
        task.add_requirements_file(parsed_data.get("requirements_file"))
        task.add_python_version(parsed_data.get("python_version"))
        task.set_type(parsed_data.get("taskType"))
        task.add_prototypical_inputs(parsed_data.get("prototypical_inputs"))
        task.add_prototypical_outputs(parsed_data.get("prototypical_outputs"))
        if "dependency" in parsed_data:
            task.add_dependent_module(CONFIG.PYTHON_DEPENDENCIES_RELATIVE_PATH, parsed_data.get("dependency"))
    return wf


def parse_experiment_specification(experiment_specification):
    experiments_metamodel = textx.metamodel_from_file(GRAMMAR_PATH)
    experiment_model = experiments_metamodel.model_from_str(experiment_specification)
    for component in experiment_model.component:
        if component.__class__.__name__ == 'Experiment':
            exp = Experiment(component.name)
            exp.set_intent(component.intent_name)
            for node in component.experimentNode:
                if node.__class__.__name__ == 'SpaceConfig':
                    space = Space(node.name)
                    exp.add_space(space)
                    space.set_assembled_workflow(node.assembled_workflow.name)
                    space.set_strategy(node.strategy_name)
                    space.set_filter_function(node.filter_function)
                    space.set_generator_function(node.generator_function)
                    if node.tasks:
                        for task_config in node.tasks:
                            for param_config in task_config.config:
                                space.add_task_param_to_vp_mapping(task_config.task.name,
                                                                   param_config.param_name, param_config.vp)
                    if node.vps:
                        for vp in node.vps:
                            if vp.vp_values.__class__.__name__ == 'ENUM':
                                vp_type = "enum"
                                vp_data = {
                                    "values": vp.vp_values.values,
                                }
                            if vp.vp_values.__class__.__name__ == 'RANGE':
                                vp_type = "range"
                                vp_data = {
                                    "min": vp.vp_values.minimum,
                                    "max": vp.vp_values.maximum,
                                    "step": getattr(vp.vp_values, 'step', 1),
                                }
                            space.add_variability_point(vp.vp_name, vp_type, vp_data)
                    if node.runs:
                        space.set_runs(int(node.runs))
                if node.__class__.__name__ == 'ExperimentControlTask':
                    wf = get_experiment_task(node)
                    exp.add_task(node.name, wf)
                if node.__class__.__name__ == 'ExperimentControlInteraction':
                    wf = get_experiment_task(node)
                    task = wf.get_task(node.name)
                    if task.taskType != "interactive":
                        raise exceptions.InteractionTaskDoesNotHaveInteractiveType(f"Interaction {node.name} is not implemented by a interactive task")
                    exp.add_task(node.name, wf)
            for node in component.control:
                if node.explink:
                    for link in node.explink:
                        if link.__class__.__name__ == 'RegularExpLink':
                            if link.nodes:
                                logger.debug("link with nodes")
                                process_control_node_dependencies(exp, link.nodes)
                            if link.start_nodes:
                                logger.debug("link with start_nodes")
                                process_control_node_dependencies(exp, link.start_nodes)
                            if link.end_nodes:
                                logger.debug("link with end_nodes")
                                process_control_node_dependencies(exp, link.end_nodes)
                            if link.first_node and link.other_nodes:
                                logger.debug("link with first_node and rest_nodes")
                                process_control_node_dependencies(exp, [link.first_node] + link.other_nodes)
                        if link.__class__.__name__ == 'ConditionalExpLink':
                            logger.debug("conditional link")
                            process_control_node_dependencies(exp, [link.from_node] + [link.to_node], link.condition)
            return exp
