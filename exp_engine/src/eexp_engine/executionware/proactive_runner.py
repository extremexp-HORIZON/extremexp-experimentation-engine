import proactive
import os
import json
from ..data_abstraction_layer.data_abstraction_api import get_workflow, update_workflow, get_current_time, set_data_abstraction_config
import logging

packagedir = os.path.dirname(os.path.abspath(__file__))
PROACTIVE_HELPER_FULL_PATH = os.path.join(packagedir, "proactive_helper.py")
interactive_path_folder = os.path.join(packagedir, "user_interaction")
INTERACTIVE_TASK_PRESCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "prescript.py")
INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH = os.path.join(interactive_path_folder, "user_interaction_requirements.txt")
INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "postscript.py")
ZENOH_REQS_PATH = os.path.join(packagedir, "zenoh", "zenoh_requirements.txt")
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
PROACTIVE_FORK_SCRIPTS_PATH = os.path.join(packagedir, "scripts")
RESULTS_FILE = "experiment_results.json"


def create_gateway_and_connect_to_it(username, password):
    print("Logging on proactive-server...")
    proactive_url  = CONFIG.PROACTIVE_URL
    print("Creating gateway ")
    gateway = proactive.ProActiveGateway(proactive_url, debug=False)
    print("Gateway created")

    print("Connecting on: " + proactive_url)
    gateway.connect(username=username, password=password)
    assert gateway.isConnected() is True
    print("Connected")
    return gateway


def _create_job(gateway, workflow_name):
    print("Creating a proactive job...")
    gateway = reconnect_if_needed(gateway)
    proactive_job = gateway.createJob()
    proactive_job.setJobName(workflow_name)
    print("Job created.")
    return proactive_job


def _create_fork_env(gateway, proactive_job):
    print("Adding a fork environment to the import task...")
    gateway = reconnect_if_needed(gateway)
    proactive_fork_env = gateway.createForkEnvironment(language="groovy")

    groovy_env_path = os.path.join(PROACTIVE_FORK_SCRIPTS_PATH, "fork_env.groovy")
    proactive_fork_env.setImplementationFromFile(groovy_env_path)
    proactive_job.addVariable("CONTAINER_PLATFORM", "docker")
    proactive_job.addVariable("CONTAINER_IMAGE", "docker://activeeon/dlm3")
    proactive_job.addVariable("CONTAINER_GPU_ENABLED", "false")
    proactive_job.addVariable("CONTAINER_LOG_PATH", "/shared")
    proactive_job.addVariable("HOST_LOG_PATH", "/shared")
    print("Fork environment created.")
    return proactive_fork_env


def _create_execution_engine_mapping(tasks):
    mapping = {}
    for t in tasks:
        map = {}
        mapping[t.name] = map
        for ds in t.input_files:
            if ds.name_in_generating_task:
                map[ds.name_in_task_signature] = ds.name_in_generating_task
    print("EXECUTION ENGINE MAPPING")
    print("*****************")
    import pprint
    pprint.pp(mapping)
    print("*****************")
    return mapping


def _create_exp_engine_metadata(exp_id, exp_name, wf_id):
    exp_engine_metadata = {}
    exp_engine_metadata["exp_id"] = exp_id
    exp_engine_metadata["exp_name"] = exp_name
    exp_engine_metadata["wf_id"] = wf_id
    return exp_engine_metadata


def _get_requirements_from_file(reqs_file):
    with open(reqs_file) as file:
        user_reqs = [line.rstrip() for line in file]
    return user_reqs


def _create_python_task(gateway, results_so_far, wf_id, task_name, fork_environment, mapping, exp_engine_metadata, task_impl, requirements_file, python_version, taskType,
                        input_files=[], output_files=[], dependent_modules=[], dependencies=[]):
    print(f"Creating task {task_name}...")
    gateway = reconnect_if_needed(gateway)
    task = gateway.createPythonTask()
    task.setTaskName(task_name)
    print(f"Setting implementation from file {task_impl}")
    task.setTaskImplementationFromFile(task_impl)

    if taskType=="interactive":
        print(f"Setting pre_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway)
        pre_script = gateway.createPreScript(proactive.ProactiveScriptLanguage().python())
        pre_script.setImplementationFromFile(INTERACTIVE_TASK_PRESCRIPT_FULL_PATH)
        task.setPreScript(pre_script)

        print(f"Setting post_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway)
        post_script = gateway.createPostScript(proactive.ProactiveScriptLanguage().python())
        post_script.setImplementationFromFile(INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH)
        task.setPostScript(post_script)

        task.addVariable("wf_id", wf_id)
        task.addVariable("task_name", task_name)
        task.addVariable("data_abstraction_base_url", CONFIG.DATA_ABSTRACTION_BASE_URL)
        task.addVariable("data_abstraction_access_token", CONFIG.DATA_ABSTRACTION_ACCESS_TOKEN)

        python_version_path = "/usr/bin/python3.8" # This depends on the Proactive deployment (here in ICOM)
        task.setDefaultPython(python_version_path)

        requirements = _get_requirements_from_file(INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH)
        if requirements_file:
            requirements += _get_requirements_from_file(requirements_file)
        if CONFIG.DATASET_MANAGEMENT == "DDM":
            requirements += _get_requirements_from_file(ZENOH_REQS_PATH)
        print(f"Setting virtual environment to {requirements}")
        task.setVirtualEnv(requirements=requirements)

    else:
        if requirements_file:
            if not python_version:
                print("You need to set a Python version when configuring a virtual environment.")
                exit(1)
            if not CONFIG.PROACTIVE_PYTHON_VERSIONS:
                print(f"You need to add PROACTIVE_PYTHON_VERSIONS to your config.py, and set a path for version {python_version}")
                exit(1)
            if python_version not in CONFIG.PROACTIVE_PYTHON_VERSIONS:
                print(f"You need to set a path for version {python_version} in the PROACTIVE_PYTHON_VERSIONS of your config.py")
                exit(1)
            python_version_path = CONFIG.PROACTIVE_PYTHON_VERSIONS[python_version]
            print(f"Setting python version to {python_version_path}")
            task.setDefaultPython(python_version_path)
            requirements = _get_requirements_from_file(requirements_file)
            requirements += _get_requirements_from_file(ZENOH_REQS_PATH)
            print(f"Setting virtual environment to {requirements}")
            task.setVirtualEnv(requirements=requirements)
        elif python_version and not requirements_file:
                python_version_path = CONFIG.PROACTIVE_PYTHON_VERSIONS[python_version]
                print(f"Setting python version to {python_version_path}")
                task.setDefaultPython(python_version_path)
                requirements = _get_requirements_from_file(ZENOH_REQS_PATH)
                print(f"Setting virtual environment to {requirements}")
                task.setVirtualEnv(requirements=requirements)
        else:
            task.setForkEnvironment(fork_environment)

    for input_file in input_files:
        if input_file.path:
            task.addInputFile(input_file.path)
            input_file_path = os.path.dirname(input_file.path) if "**" in input_file.path else input_file.path
            task.addVariable(input_file.name_in_task_signature, input_file_path)
        if input_file.zenoh_name or input_file.zenoh_project:
            task.addVariable(input_file.name_in_task_signature, f"{input_file.zenoh_name}|{input_file.zenoh_project}")
    for output_file in output_files:
        if output_file.path:
            # take out the '**' or the file name to retrieve the path to the folder
            output_folder_path = os.path.dirname(output_file.path)
            output_folder_path_with_wf_id = os.path.join(output_folder_path, wf_id)
            if "**" in output_file.path:
                task.addVariable(output_file.name_in_task_signature, output_folder_path_with_wf_id)
                print(f"Adding '{output_file.name_in_task_signature}'->'{output_folder_path_with_wf_id}' to proactive 'variables'")
            else:
                # if this is not a folder path (i.e. it does not end with "**"), append the file name at the end
                output_file_name = os.path.basename(output_file.path)
                output_file_path = os.path.join(output_folder_path, wf_id, output_file_name)
                task.addVariable(output_file.name_in_task_signature, output_file_path)
                print(f"Adding '{output_file.name_in_task_signature}'->'{output_file_path}' to proactive 'variables'")
            # add back the '**' to ensure that proactive treats it as a folder
            final_output_path_proactive = os.path.join(output_folder_path_with_wf_id, "**")
            task.addOutputFile(final_output_path_proactive)
            print(f"Declaring '{final_output_path_proactive}' as output file for task {task_name}")
        if output_file.zenoh_name or output_file.zenoh_project:
            task.addVariable(output_file.name_in_task_signature, f"{output_file.zenoh_name}|{output_file.zenoh_project}")

    dependent_modules_folders = []
    for dependent_module in dependent_modules:
        task.addInputFile(dependent_module)
        dependent_modules_folders.append(os.path.dirname(dependent_module))
    # Adding the helper to all tasks as input:
    PROACTIVE_HELPER_RELATIVE_PATH = os.path.relpath(PROACTIVE_HELPER_FULL_PATH)
    task.addInputFile(PROACTIVE_HELPER_RELATIVE_PATH)

    with open(EXECUTION_ENGINE_RUNTIME_CONFIG, 'w') as f:
        dataset_config = {}
        dataset_config["DATASET_MANAGEMENT"] = CONFIG.DATASET_MANAGEMENT
        dataset_config["DDM_URL"] = CONFIG.DDM_URL
        dataset_config["DDM_TOKEN"] = CONFIG.DDM_TOKEN
        runtime_job_config = {}
        runtime_job_config["mapping"] = mapping
        runtime_job_config["exp_engine_metadata"] = exp_engine_metadata
        runtime_job_config["dataset_config"] = dataset_config
        json.dump(runtime_job_config, f)
    task.addInputFile(EXECUTION_ENGINE_RUNTIME_CONFIG)

    if results_so_far:
        with open(RESULTS_FILE, 'w') as f:
            json.dump(results_so_far, f)
        task.addInputFile(RESULTS_FILE)

    proactive_helper_folder = os.path.dirname(PROACTIVE_HELPER_RELATIVE_PATH)
    dependent_modules_folders.append(proactive_helper_folder)
    task.addVariable("dependent_modules_folders", ','.join(dependent_modules_folders))
    for dependency in dependencies:
        print(f"Adding dependency of '{task_name}' to '{dependency.getTaskName()}'")
        task.addDependency(dependency)
    task.setPreciousResult(False)
    print("Task created.")

    return task


def _configure_task(task, configurations):
    task_name = task.getTaskName()
    print(f"Configuring task {task_name}")
    task_params_str = f"{task_name}["
    for k in configurations.keys():
        value = configurations[k]
        if type(value) == int or type(value) == float:
            value = str(value)
        task.addVariable(k, value)
        task_params_str += f"{k} --> {value} | "
    task_params_str = task_params_str[:-3]
    task_params_str += "]"
    return task_params_str


def _create_flow_script(gateway, condition_task_name, if_task_name, else_task_name, continuation_task_name, condition):
    branch_script = """
if """ + condition + """:
    branch = "if"
else:
    branch = "else"
    """
    print(f"Creating flow script for condition task {condition_task_name}")
    gateway = reconnect_if_needed(gateway)
    flow_script = gateway.createBranchFlowScript(
        branch_script,
        if_task_name,
        else_task_name,
        continuation_task_name,
        script_language=proactive.ProactiveScriptLanguage().python()
    )
    return flow_script


def _submit_job_and_retrieve_results_and_outputs(wf_id, gateway, job, task_statuses):
    print("Submitting the job to the scheduler...")

    gateway = reconnect_if_needed(gateway)
    job_id = gateway.submitJobWithInputsAndOutputsPaths(job, debug=False)
    print("job_id: " + str(job_id))
    update_workflow(wf_id, {"metadata": {"proactive_job_id": str(job_id)}})

    os.remove(EXECUTION_ENGINE_RUNTIME_CONFIG)
    if os.path.isfile(RESULTS_FILE):
        os.remove(RESULTS_FILE)
    import time
    is_finished = False
    seconds = 0
    while not is_finished:
        gateway = reconnect_if_needed(gateway)
        job_status = gateway.getJobStatus(job_id)
        for ts in task_statuses:
            task_previous_status = ts["status"].upper()
            task_name = ts["name"]
            gateway = reconnect_if_needed(gateway)
            task_current_status = gateway.getTaskStatus(job_id, task_name).upper()
            ts["status"] = task_current_status
            wf = get_workflow(wf_id)
            this_task = next(t for t in wf["tasks"] if t["name"] == task_name)
            current_time  = get_current_time()
            if (task_previous_status == "PENDING" or task_previous_status == "SUBMITTED") and task_current_status == "RUNNING":
                this_task["start"] = current_time
                print(f"Task {task_name} started at {current_time}")
            if task_previous_status == "RUNNING" and task_current_status in ["FINISHED", "CANCELED", "FAILED"]:
                this_task["end"] = current_time
                print(f"Task {task_name} completed at {current_time}")
            this_task["metadata"]["status"] = task_current_status
            update_workflow(wf_id, {"tasks": wf["tasks"]})

        print(f"Current job status: {job_status}: {seconds}")
        if job_status.upper() in ["FINISHED", "CANCELED", "FAILED", "KILLED"]:
            update_workflow(wf_id, {"status": job_status.upper()})
            is_finished = True
        else:
            seconds += 1
            time.sleep(1)

    # print("Getting job results...")
    # job_result = gateway.getJobResult(job_id, 300000)
    # print("****")
    # print(type(job_result))
    # print(job_result)
    # print("****")

    # task_result = gateway.getTaskResult(job_id, "TrainModel", 300000)
    # print(task_result)

    print("Getting job result map...")
    result_map = dict(gateway.waitForJob(job_id, 300000).getResultMap())
    print(result_map)

    print("Getting job outputs...")
    job_outputs = gateway.printJobOutput(job_id, 300000)
    print(job_outputs)

    return job_id, result_map, job_outputs


def _teardown(gateway):
    print("Disconnecting")
    if gateway and gateway.isConnected():
        gateway.disconnect()
        print("Disconnected")
        if gateway and gateway.isConnected():
            gateway.terminate()
            print("Finished")


def reconnect_if_needed(gateway):
    if gateway and gateway.isConnected():
        return gateway
    return create_gateway_and_connect_to_it(CONFIG.PROACTIVE_USERNAME, CONFIG.PROACTIVE_PASSWORD)


def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config, results_so_far):
    global RUNNER_FOLDER, CONFIG, EXECUTION_ENGINE_RUNTIME_CONFIG, GATEWAY
    RUNNER_FOLDER = runner_folder
    CONFIG = config
    set_data_abstraction_config(CONFIG)
    EXECUTION_ENGINE_RUNTIME_CONFIG = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"

    logger = logging.getLogger(__name__)
    logger.info("****************************")
    logger.info(f"Executing workflow {w.name}")
    logger.info("****************************")
    w.print()
    logger.info("****************************")

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)

    gateway = create_gateway_and_connect_to_it(CONFIG.PROACTIVE_USERNAME, CONFIG.PROACTIVE_PASSWORD)
    job = _create_job(gateway, w.name)
    fork_env = _create_fork_env(gateway, job)
    mapping = _create_execution_engine_mapping(sorted_tasks)
    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)

    created_tasks = []
    task_statuses = []

    job_params_str = ""
    for t in sorted_tasks:
        dependent_tasks = [ct for ct in created_tasks if ct.getTaskName() in t.dependencies]
        task_to_execute = _create_python_task(gateway, results_so_far, wf_id, t.name, fork_env, mapping, exp_engine_metadata, t.impl_file, t.requirements_file,
                                              t.python_version, t.taskType, t.input_files, t.output_files, t.dependent_modules,
                                              dependent_tasks)
        if len(t.params) > 0:
            job_params_str += _configure_task(task_to_execute, t.params)
            job_params_str += ", "
        if t.is_condition_task():
            task_to_execute.setFlowScript(
                _create_flow_script(gateway, t.name, t.if_task_name, t.else_task_name, t.continuation_task_name, t.condition)
            )
        job.addTask(task_to_execute)
        task_statuses.append({"name": t.name, "status": "Pending"})
        created_tasks.append(task_to_execute)
    print("Tasks added.")
    job_params_str = job_params_str[:-2]
    job.addVariable(f"params", job_params_str)
    job.addVariable(f"wf_id", wf_id)
    job.addVariable(f"exp_id", exp_id)

    job_id, job_result_map, job_outputs = _submit_job_and_retrieve_results_and_outputs(wf_id, gateway, job, task_statuses)
    _teardown(gateway)

    print("****************************")
    print(f"Finished executing workflow {w.name}")
    print(job_params_str)
    print(job_result_map)
    print("****************************")

    return job_result_map
