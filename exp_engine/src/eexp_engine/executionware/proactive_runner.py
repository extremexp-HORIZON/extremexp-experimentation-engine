import proactive
import os
import json
from ..data_abstraction_layer.data_abstraction_api import get_workflow, update_workflow, get_current_time, set_data_abstraction_config
import logging

packagedir = os.path.dirname(os.path.abspath(__file__))
PROACTIVE_HELPER_FULL_PATH = os.path.join(packagedir, "proactive_helper.py")
interactive_path_folder = os.path.join(packagedir, "user_interaction")
INTERACTIVE_TASK_PRESCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "prescript.py")
INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH = os.path.join(interactive_path_folder, "requirements.txt")
INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH = os.path.join(interactive_path_folder, "postscript.py")
EXECUTION_ENGINE_MAPPING_FILE_PREFIX = "execution_engine_mapping"
PROACTIVE_FORK_SCRIPTS_PATH = os.path.join(packagedir, "scripts")
RESULTS_FILE = "experiment_results.json"


def create_gateway_and_connect_to_it(username, password):
    print("Logging on proactive-server...")
    proactive_host = 'try.activeeon.com'
    proactive_port = '8443'
    proactive_url  = "https://"+proactive_host+":"+proactive_port
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


def _get_python_version(python_version, enforce_python_version=True):
    if not python_version and enforce_python_version:
        print("You need to set a Python version when configuring a virtual environment.")
        exit(0)
    if python_version == "3.9":
        return "/opt/miniconda3/py39/bin/python3"
    else:
        return python_version


def _create_python_task(gateway, results_so_far, wf_id, task_name, fork_environment, mapping, task_impl, requirements_file, python_version, taskType,
                        input_files=[], output_files=[], dependent_modules=[], dependencies=[]):
    print(f"Creating task {task_name}...")
    gateway = reconnect_if_needed(gateway)
    task = gateway.createPythonTask()
    task.setTaskName(task_name)
    print(f"setting implementation from file {task_impl}")
    task.setTaskImplementationFromFile(task_impl)

    if taskType=="interactive":
        print(f"setting pre_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway)
        pre_script = gateway.createPreScript(proactive.ProactiveScriptLanguage().python())
        pre_script.setImplementationFromFile(INTERACTIVE_TASK_PRESCRIPT_FULL_PATH)
        task.setPreScript(pre_script)

        print(f"setting post_script for interactive task {task_name}")
        gateway = reconnect_if_needed(gateway)
        post_script = gateway.createPostScript(proactive.ProactiveScriptLanguage().python())
        post_script.setImplementationFromFile(INTERACTIVE_TASK_POSTSCRIPT_FULL_PATH)
        task.setPostScript(post_script)

        task.addVariable("wf_id", wf_id)
        task.addVariable("task_name", task_name)
        task.addVariable("data_abstraction_base_url", CONFIG.DATA_ABSTRACTION_BASE_URL)
        task.addVariable("data_abstraction_access_token", CONFIG.DATA_ABSTRACTION_ACCESS_TOKEN)

        python_version_path = "/usr/bin/python3" # This is 3.6.9 in Proactive, and cannot be changed
        task.setDefaultPython(python_version_path)

        with open(INTERACTIVE_TASK_PRESCRIPT_REQS_FULL_PATH) as file:
            requirements = [line.rstrip() for line in file]
        if requirements_file:
            print(f"Adding extra requirements from file {requirements_file}")
            with open(requirements_file) as file:
                extra_reqs = [line.rstrip() for line in file]
            requirements += extra_reqs
        task.setVirtualEnv(requirements=requirements)

    else:
        if requirements_file:
            python_version_path = _get_python_version(python_version)
            print(f"setting python version to {python_version_path}")
            task.setDefaultPython(python_version_path)
            print(f"setting venv from file {requirements_file}")
            task.setVirtualEnvFromFile(requirements_file)
        else:
            task.setForkEnvironment(fork_environment)

    for input_file in input_files:
        if input_file.path:
            task.addInputFile(input_file.path)
            input_file_path = os.path.dirname(input_file.path) if "**" in input_file.path else input_file.path
            task.addVariable(input_file.name_in_task_signature, input_file_path)
    for output_file in output_files:
        if output_file.path:
            if "**" in output_file.path:
                # take out the '**' to reveal the actual path to the folder
                output_file_path = os.path.dirname(output_file.path)
                final_output_path = os.path.join(output_file_path, wf_id)
                task.addVariable(output_file.name_in_task_signature, final_output_path)
                # add back the '**' to ensure that proactive treats it as a folder
                final_output_path_proactive = os.path.join(final_output_path, "**")
                task.addOutputFile(final_output_path_proactive)
                print(f"final_output_path: {final_output_path}")
                print(f"final_output_path_proactive: {final_output_path_proactive}")
            else:
                output_file_path = os.path.dirname(output_file.path)
                output_file_name = os.path.basename(output_file.path)
                final_output_path = os.path.join(output_file_path, wf_id, output_file_name)
                task.addVariable(output_file.name_in_task_signature, final_output_path)
                task.addOutputFile(final_output_path)
                print(f"final_output_path: {final_output_path}")

    dependent_modules_folders = []
    for dependent_module in dependent_modules:
        task.addInputFile(dependent_module)
        dependent_modules_folders.append(os.path.dirname(dependent_module))
    # Adding the helper to all tasks as input:
    PROACTIVE_HELPER_RELATIVE_PATH = os.path.relpath(PROACTIVE_HELPER_FULL_PATH)
    task.addInputFile(PROACTIVE_HELPER_RELATIVE_PATH)

    with open(EXECUTION_ENGINE_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)
    task.addInputFile(EXECUTION_ENGINE_MAPPING_FILE)

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

    os.remove(EXECUTION_ENGINE_MAPPING_FILE)
    if os.path.isfile(RESULTS_FILE):
        os.remove(RESULTS_FILE)
    import time
    is_finished = False
    seconds = 0
    while not is_finished:
        gateway = reconnect_if_needed(gateway)
        job_status = gateway.getJobStatus(job_id)
        for ts in task_statuses:
            previous_task_status = ts["status"].upper()
            task_name = ts["name"]
            gateway = reconnect_if_needed(gateway)
            current_task_status = gateway.getTaskStatus(job_id, task_name).upper()
            ts["status"] = current_task_status
            if (previous_task_status == "PENDING" or previous_task_status == "SUBMITTED") and current_task_status == "RUNNING":
                wf = get_workflow(wf_id)
                completed_task = next(t for t in wf["tasks"] if t["name"] == task_name)
                current_time  = get_current_time()
                completed_task["start"] = current_time
                update_workflow(wf_id, {"tasks": wf["tasks"]})
                print(f"Task {task_name} started at {current_time}")
            if previous_task_status == "RUNNING" and current_task_status in ["FINISHED", "CANCELED", "FAILED"]:
                wf = get_workflow(wf_id)
                completed_task = next(t for t in wf["tasks"] if t["name"] == task_name)
                current_time  = get_current_time()
                completed_task["end"] = current_time
                update_workflow(wf_id, {"tasks": wf["tasks"]})
                print(f"Task {task_name} completed at {current_time}")
        
        print(f"Current job status: {job_status}: {seconds}")
        if job_status.upper() in ["FINISHED", "CANCELED", "FAILED", "KILLED"]:
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


def execute_wf(w, exp_id, wf_id, runner_folder, config, results_so_far):
    global RUNNER_FOLDER, CONFIG, EXECUTION_ENGINE_MAPPING_FILE, GATEWAY
    RUNNER_FOLDER = runner_folder
    CONFIG = config
    set_data_abstraction_config(CONFIG)
    EXECUTION_ENGINE_MAPPING_FILE = f"{EXECUTION_ENGINE_MAPPING_FILE_PREFIX}_{wf_id}.json"

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

    created_tasks = []
    task_statuses = []

    job_params_str = ""
    for t in sorted_tasks:
        dependent_tasks = [ct for ct in created_tasks if ct.getTaskName() in t.dependencies]
        task_to_execute = _create_python_task(gateway, results_so_far, wf_id, t.name, fork_env, mapping, t.impl_file, t.requirements_file,
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
