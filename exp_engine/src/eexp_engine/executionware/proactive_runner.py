import proactive
import os
import json
from ..data_abstraction_layer.data_abstraction_api import DataAbstractionClient
import logging

packagedir = os.path.dirname(os.path.abspath(__file__))
interactive_path_folder = os.path.join(packagedir, "scripts", "user_interaction")
TASK_PRESCRIPT_FULL_PATH = os.path.join(packagedir, "scripts", "task_prescript.py")
INTERACTIVE_TASK_PRESCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "prescript.py")
INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH = os.path.join(interactive_path_folder, "user_interaction_requirements.txt")
INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "postscript.py")
DEFAULT_REQS_PATH = os.path.join(packagedir, "default_task_requirements", "task_requirements.txt")
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
PROACTIVE_FORK_SCRIPTS_PATH = os.path.join(packagedir, "scripts")


def create_gateway_and_connect_to_it(config):
    import time
    logger = logging.getLogger(__name__)
    logger.info("Logging on proactive-server...")
    proactive_url  = config.PROACTIVE_URL
    proactive_username = config.PROACTIVE_USERNAME
    proactive_password = config.PROACTIVE_PASSWORD
    logger.info("Creating gateway ")
    gateway = proactive.ProActiveGateway(proactive_url, debug=False)
    logger.info("Gateway created")

    max_retries = 3

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Connecting to {proactive_url} (attempt {attempt}/{max_retries})...")
            gateway.connect(username=proactive_username, password=proactive_password)

            if gateway.isConnected():
                logger.info("Connected successfully")
                return gateway
            else:
                logger.warning(f"Connection attempt {attempt} failed: not connected")
        except Exception as e:
            logger.error(f"Connection attempt {attempt} failed: {e}")

        if attempt < max_retries:
            logger.info(f"Retrying in 2 seconds...")
            time.sleep(2)

    logger.error(f"Failed to connect after {max_retries} attempts")
    raise ConnectionError(f"Could not connect to ProActive server at {proactive_url} after {max_retries} attempts")


def _create_job(gateway, workflow_name, config):
    print("Creating a proactive job...")
    gateway = reconnect_if_needed(gateway, config)
    proactive_job = gateway.createJob()
    proactive_job.setJobName(workflow_name)
    print("Job created.")
    return proactive_job


def _create_fork_env(gateway, proactive_job, config):
    print("Adding a fork environment to the import task...")
    gateway = reconnect_if_needed(gateway, config)
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


def _create_python_task(gateway, config, data_client, results_so_far, wf_id, task_name, fork_environment, mapping, exp_engine_metadata, task_impl, requirements_file, python_version, taskType,
                        runtime_config_path, results_file_path,
                        input_files=None, output_files=None, dependent_modules=None, dependencies=None):
    if input_files is None: input_files = []
    if output_files is None: output_files = []
    if dependent_modules is None: dependent_modules = []
    if dependencies is None: dependencies = []
    print(f"Creating task {task_name}...")
    gateway = reconnect_if_needed(gateway, config)
    task = gateway.createPythonTask()
    task.setTaskName(task_name)
    print(f"Setting implementation from file {task_impl}")
    task.setTaskImplementationFromFile(task_impl)

    if taskType=="interactive":
        print(f"Setting pre_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway, config)
        pre_script = gateway.createPreScript(proactive.ProactiveScriptLanguage().python())
        pre_script.setImplementationFromFile(INTERACTIVE_TASK_PRESCRIPT_FULL_PATH)
        task.setPreScript(pre_script)

        print(f"Setting post_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway, config)
        post_script = gateway.createPostScript(proactive.ProactiveScriptLanguage().python())
        post_script.setImplementationFromFile(INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH)
        task.setPostScript(post_script)

        task.addVariable("wf_id", wf_id)
        task.addVariable("task_name", task_name)
        task.addVariable("data_abstraction_base_url", config.DATA_ABSTRACTION_BASE_URL)
        task.addVariable("data_abstraction_access_token", config.DATA_ABSTRACTION_ACCESS_TOKEN)

        python_version_path = "/usr/bin/python3.8"  # Depends on deployment
        task.setDefaultPython(python_version_path)

        requirements = _get_requirements_from_file(INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH)
        if requirements_file:
            requirements += _get_requirements_from_file(requirements_file)
        if config.DATASET_MANAGEMENT == "DDM":
            requirements += _get_requirements_from_file(DEFAULT_REQS_PATH)
        print(f"Setting virtual environment to {requirements}")
        task.setVirtualEnv(requirements=requirements)
    else:
        
        # Set pre_script for all non-interactive tasks
        gateway = reconnect_if_needed(gateway, config)
        pre_script = gateway.createPreScript(proactive.ProactiveScriptLanguage().python())
        pre_script.setImplementationFromFile(TASK_PRESCRIPT_FULL_PATH)
        task.setPreScript(pre_script)

        if requirements_file:
            if not python_version:
                print("You need to set a Python version when configuring a virtual environment.")
                exit(1)
            if not config.PROACTIVE_PYTHON_VERSIONS:
                print(f"You need to add PROACTIVE_PYTHON_VERSIONS to your config.py, and set a path for version {python_version}")
                exit(1)
            if python_version not in config.PROACTIVE_PYTHON_VERSIONS:
                print(f"You need to set a path for version {python_version} in the PROACTIVE_PYTHON_VERSIONS of your config.py")
                exit(1)
            python_version_path = config.PROACTIVE_PYTHON_VERSIONS[python_version]
            print(f"Setting python version to {python_version_path}")
            task.setDefaultPython(python_version_path)
            requirements = _get_requirements_from_file(requirements_file)
            requirements += _get_requirements_from_file(DEFAULT_REQS_PATH)
            print(f"Setting virtual environment to {requirements}")
            task.setVirtualEnv(requirements=requirements)
        elif python_version and not requirements_file:
            python_version_path = config.PROACTIVE_PYTHON_VERSIONS[python_version]
            print(f"Setting python version to {python_version_path}")
            task.setDefaultPython(python_version_path)
            requirements = _get_requirements_from_file(DEFAULT_REQS_PATH)
            print(f"Setting virtual environment to {requirements}")
            task.setVirtualEnv(requirements=requirements)
        else:
            task.setForkEnvironment(fork_environment)

    for input_file in input_files:
        if input_file.path:
            task.addInputFile(input_file.path)
            input_file_path = os.path.dirname(input_file.path) if "**" in input_file.path else input_file.path
            task.addVariable(input_file.name_in_task_signature, input_file_path)
        if input_file.filename or input_file.project:
            task.addVariable(input_file.name_in_task_signature, f"{input_file.filename}|{input_file.project}")
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
        if output_file.filename or output_file.project:
            task.addVariable(output_file.name_in_task_signature, f"{output_file.filename}|{output_file.project}")

    dependent_modules_folders = []
    for dependent_module in dependent_modules:
        task.addInputFile(dependent_module)
        dependent_modules_folders.append(os.path.dirname(dependent_module))

    with open(runtime_config_path, 'w') as f:
        dataset_config = {}
        dataset_config["DATASET_MANAGEMENT"] = config.DATASET_MANAGEMENT
        dataset_config["DDM_URL"] = config.DDM_URL
        dataset_config["DDM_TOKEN"] = config.DDM_TOKEN
        runtime_job_config = {}
        runtime_job_config["EXECUTIONWARE"] = config.EXECUTIONWARE
        runtime_job_config["mapping"] = mapping
        runtime_job_config["exp_engine_metadata"] = exp_engine_metadata
        runtime_job_config["dataset_config"] = dataset_config
        json.dump(runtime_job_config, f)
    task.addInputFile(runtime_config_path)

    if results_so_far:
        with open(results_file_path, 'w') as f:
            json.dump(results_so_far, f)
        task.addInputFile(results_file_path)

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


def _create_flow_script(gateway, config, condition_task_name, if_task_name, else_task_name, continuation_task_name, condition):
    branch_script = """
if """ + condition + """:
    branch = "if"
else:
    branch = "else"
    """
    print(f"Creating flow script for condition task {condition_task_name}")
    gateway = reconnect_if_needed(gateway, config)
    flow_script = gateway.createBranchFlowScript(
        branch_script,
        if_task_name,
        else_task_name,
        continuation_task_name,
        script_language=proactive.ProactiveScriptLanguage().python()
    )
    return flow_script


def _submit_job_and_retrieve_results_and_outputs(wf_id, gateway, job, task_statuses, data_client, config, runtime_config_path, results_file_path):
    logger = logging.getLogger(__name__)
    logger.info("Submitting the job to the scheduler...")

    gateway = reconnect_if_needed(gateway, config)
    job_id = gateway.submitJobWithInputsAndOutputsPaths(job, debug=False)
    logger.info(f"job_id: {job_id}")
    data_client.update_workflow(wf_id, {"metadata": {"proactive_job_id": str(job_id)}})

    if os.path.isfile(runtime_config_path):
        os.remove(runtime_config_path)
    if os.path.isfile(results_file_path):
        os.remove(results_file_path)
    import time
    is_finished = False
    seconds = 0
    while not is_finished:
        try:
            gateway = reconnect_if_needed(gateway, config)
            job_status = gateway.getJobStatus(job_id)
            for ts in task_statuses:
                task_previous_status = ts["status"].upper()
                task_name = ts["name"]
                gateway = reconnect_if_needed(gateway, config)
                task_current_status = gateway.getTaskStatus(job_id, task_name).upper()
                ts["status"] = task_current_status
                wf = data_client.get_workflow(wf_id)
                this_task = next(t for t in wf["tasks"] if t["name"] == task_name)
                current_time  = data_client.get_current_time()
                if (task_previous_status == "PENDING" or task_previous_status == "SUBMITTED") and task_current_status == "RUNNING":
                    this_task["start"] = current_time
                    logger.info(f"Task {task_name} started at {current_time}")
                if task_previous_status == "RUNNING" and task_current_status in ["FINISHED", "CANCELED", "FAILED"]:
                    this_task["end"] = current_time
                    logger.info(f"Task {task_name} completed at {current_time}")
                this_task["metadata"]["status"] = task_current_status
                data_client.update_workflow(wf_id, {"tasks": wf["tasks"]})

            logger.info(f"Current job status: {job_status}: {seconds}")
            if job_status.upper() in ["FINISHED", "CANCELED", "FAILED", "KILLED"]:
                data_client.update_workflow(wf_id, {"status": job_status.upper()})
                is_finished = True
            else:
                seconds += 1
                time.sleep(1)
        except (ConnectionError, RuntimeError) as e:
            logger.error(f"Connection error during job monitoring: {e}")
            data_client.update_workflow(wf_id, {"status": "FAILED"})
            raise

    logger.info("Getting job result map...")
    gateway = reconnect_if_needed(gateway, config)
    result_map = dict(gateway.waitForJob(job_id, 300000).getResultMap())
    logger.info(result_map)

    logger.info("Getting job outputs...")
    gateway = reconnect_if_needed(gateway, config)
    job_outputs = gateway.printJobOutput(job_id, 300000)
    logger.info(job_outputs)

    return job_id, result_map, job_outputs


def _teardown(gateway):
    print("Disconnecting")
    if gateway and gateway.isConnected():
        gateway.disconnect()
        print("Disconnected")
        if gateway and gateway.isConnected():
            gateway.terminate()
            print("Finished")


def reconnect_if_needed(gateway, config=None):
    if gateway and gateway.isConnected():
        return gateway
    if config is None:
        raise RuntimeError("Config required to (re)connect when gateway is not connected")
    return create_gateway_and_connect_to_it(config)


def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config, results_so_far):
    """Execute a workflow on ProActive."""
    data_client = DataAbstractionClient(config)
    runtime_config_path = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
    results_file_path = f"experiment_results_{wf_id}.json"

    logger = logging.getLogger(__name__)
    logger.info("****************************")
    logger.info(f"Executing workflow {w.name}")
    logger.info("****************************")
    w.print()
    logger.info("****************************")

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)

    gateway = None
    job_result_map = {}
    job_params_str = ""
    try:
        gateway = create_gateway_and_connect_to_it(config)
        job = _create_job(gateway, w.name, config)
        fork_env = _create_fork_env(gateway, job, config)
        mapping = _create_execution_engine_mapping(sorted_tasks)
        exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)

        created_tasks = []
        task_statuses = []

        for t in sorted_tasks:
            dependent_tasks = [ct for ct in created_tasks if ct.getTaskName() in t.dependencies]
            task_to_execute = _create_python_task(
                gateway,
                config,
                data_client,
                results_so_far,
                wf_id,
                t.name,
                fork_env,
                mapping,
                exp_engine_metadata,
                t.impl_file,
                t.requirements_file,
                t.python_version,
                t.taskType,
                runtime_config_path,
                results_file_path,
                input_files=t.input_files,
                output_files=t.output_files,
                dependent_modules=t.dependent_modules,
                dependencies=dependent_tasks,
            )
            if len(t.params) > 0:
                job_params_str += _configure_task(task_to_execute, t.params)
                job_params_str += ", "
            if t.is_condition_task():
                task_to_execute.setFlowScript(
                    _create_flow_script(gateway, config, t.name, t.if_task_name, t.else_task_name, t.continuation_task_name, t.condition)
                )
            job.addTask(task_to_execute)
            task_statuses.append({"name": t.name, "status": "Pending"})
            created_tasks.append(task_to_execute)
        print("Tasks added.")
        if job_params_str.endswith(", "):
            job_params_str = job_params_str[:-2]
        job.addVariable(f"params", job_params_str)
        job.addVariable(f"wf_id", wf_id)
        job.addVariable(f"exp_id", exp_id)

        _, job_result_map, _ = _submit_job_and_retrieve_results_and_outputs(
            wf_id, gateway, job, task_statuses, data_client, config, runtime_config_path, results_file_path
        )
        print("****************************")
        print(f"Finished executing workflow {w.name}")
        print(job_params_str)
        print(job_result_map)
        print("****************************")
        return job_result_map
    finally:
        try:
            if gateway:
                _teardown(gateway)
        except Exception as e:
            logging.error(f"Error during gateway teardown: {e}")
        for path in (runtime_config_path, results_file_path):
            try:
                if path and os.path.isfile(path):
                    os.remove(path)
            except Exception as e:
                logging.error(f"Error removing file {path}: {e}")
