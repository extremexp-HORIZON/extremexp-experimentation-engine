import proactive
import os

packagedir = os.path.dirname(os.path.abspath(__file__))
PROACTIVE_HELPER_FULL_PATH = os.path.join(packagedir, "proactive_helper.py")
PROACTIVE_FORK_SCRIPTS_PATH = os.path.join(packagedir, "scripts")
RUNNER_FOLDER = ""


def _create_gateway_and_connect_to_it(username, password):
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
    proactive_job = gateway.createJob()
    proactive_job.setJobName(workflow_name)
    print("Job created.")
    return proactive_job


def _create_fork_env(gateway, proactive_job):
    print("Adding a fork environment to the import task...")
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


def _get_python_version(python_version, enforce_python_version=True):
    if not python_version and enforce_python_version:
        print("You need to set a Python version when configuring a virtual environment.")
        exit(0)
    if python_version == "3.9":
        return "/opt/miniconda3/py39/bin/python3"


def _create_python_task(gateway, task_name, fork_environment, task_impl, requirements_file, python_version, input_files=[], dependent_modules=[], dependencies=[], is_precious_result=False):
    print(f"Creating task {task_name}...")
    task = gateway.createPythonTask()
    task.setTaskName(task_name)
    task.setTaskImplementationFromFile(task_impl)

    # TODO Remove the next three lines after adding output files to the DSL
    if task_name == "TrainModel":
        print("inside TrainModel, adding output file")
        task.addOutputFile('library-datasets/**')

    if requirements_file:
        python_version_path = _get_python_version(python_version)
        print(f"setting python version to {python_version_path}")
        task.setDefaultPython(python_version_path)
        print(f"setting venv from file {requirements_file}")
        task.setVirtualEnvFromFile(requirements_file)
    else:
        task.setForkEnvironment(fork_environment)

    for input_file in input_files:
        task.addInputFile(input_file.path)
        input_file_path = os.path.dirname(input_file.path) if "**" in input_file.path else input_file.path
        task.addVariable(input_file.name, input_file_path)
    dependent_modules_folders = []
    for dependent_module in dependent_modules:
        task.addInputFile(dependent_module)
        dependent_modules_folders.append(os.path.dirname(dependent_module))
    # Adding the helper to all tasks as input:
    PROACTIVE_HELPER_RELATIVE_PATH = os.path.relpath(PROACTIVE_HELPER_FULL_PATH, RUNNER_FOLDER)
    task.addInputFile(PROACTIVE_HELPER_RELATIVE_PATH)
    proactive_helper_folder = os.path.dirname(PROACTIVE_HELPER_RELATIVE_PATH)
    dependent_modules_folders.append(proactive_helper_folder)
    task.addVariable("dependent_modules_folders", ','.join(dependent_modules_folders))
    for dependency in dependencies:
        print(f"Adding dependency of '{task_name}' to '{dependency.getTaskName()}'")
        task.addDependency(dependency)
    task.setPreciousResult(is_precious_result)
    print("Task created.")
    return task


def _configure_task(task, configurations):
    print(f"Configuring task {task.getTaskName()}")
    for k in configurations.keys():
        value = configurations[k]
        if type(value) == int:
            value = str(value)
        task.addVariable(k, value)


def _create_flow_script(gateway, condition_task_name, if_task_name, else_task_name, continuation_task_name, condition):
    branch_script = """
if """ + condition + """:
    branch = "if"
else:
    branch = "else"
    """
    print(f"Creating flow script for condition task {condition_task_name}")
    flow_script = gateway.createBranchFlowScript(
        branch_script,
        if_task_name,
        else_task_name,
        continuation_task_name,
        script_language=proactive.ProactiveScriptLanguage().python()
    )
    return flow_script


def _submit_job_and_retrieve_results_and_outputs(gateway, job):
    print("Submitting the job to the scheduler...")

    job_id = gateway.submitJobWithInputsAndOutputsPaths(job, debug=False)
    print("job_id: " + str(job_id))

    import time
    is_finished = False
    seconds = 0
    while not is_finished:
        # Get the current state of the job
        job_status = gateway.getJobStatus(job_id)
        # task_status = gateway.getTaskStatus(job_id)
        
        # Print the current job status
        print(f"Current job status: {job_status}: {seconds}")
        # Check if the job has finished
        if job_status.upper() in ["FINISHED", "CANCELED", "FAILED"]:
            is_finished = True
        else:
            # Wait for a few seconds before checking again
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
    gateway.disconnect()
    print("Disconnected")
    gateway.terminate()
    print("Finished")


def execute_wf(w, runner_folder, config):
    global RUNNER_FOLDER, CONFIG
    RUNNER_FOLDER = runner_folder
    CONFIG = config

    print("****************************")
    print(f"Executing workflow {w.name}")
    print("****************************")
    w.print()
    print("****************************")

    gateway = _create_gateway_and_connect_to_it(CONFIG.PROACTIVE_USERNAME, CONFIG.PROACTIVE_PASSWORD)
    job = _create_job(gateway, w.name)
    fork_env = _create_fork_env(gateway, job)

    created_tasks = []
    for t in sorted(w.tasks, key=lambda t: t.order):
        dependent_tasks = [ct for ct in created_tasks if ct.getTaskName() in t.dependencies]
        task_to_execute = _create_python_task(gateway, t.name, fork_env, t.impl_file, t.requirements_file,
                                              t.python_version, t.input_files, t.dependent_modules, dependent_tasks)
        if len(t.params) > 0:
            _configure_task(task_to_execute, t.params)
        if t.is_condition_task():
            task_to_execute.setFlowScript(
                _create_flow_script(gateway, t.name, t.if_task_name, t.else_task_name, t.continuation_task_name, t.condition)
            )
        job.addTask(task_to_execute)
        created_tasks.append(task_to_execute)
    print("Tasks added.")

    job_id, job_result_map, job_outputs = _submit_job_and_retrieve_results_and_outputs(gateway, job)
    _teardown(gateway)

    print("****************************")
    print(f"Finished executing workflow {w.name}")
    print("****************************")

    return job_result_map
