import logging
from typing import List
from venv import logger

from eexp_engine.executionware.proactive_runner import _create_execution_engine_mapping

from ..models.task import Task
from ..models.workflow import Workflow
import subprocess
import os

LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"
LOCAL_ENV_DEPENDENCIES = "numpy pandas openpyxl xlrd pyarrow"


def find_and_replace_ResultMapPut(lines):
    new_lines = []
    for l in lines:
        if "resultMap.put" in l:
            new_line = l.replace("resultMap.put", "resultMap.__setitem__")
            new_lines.append(new_line)
        else:
            new_lines.append(l)
    return new_lines


def execute_wf(w: Workflow, exp_id: str, exp_name: str, wf_id: str, runner_folder: str, config: dict):
    """
    Executes the workflow using the local runner.
    """
    global RUNNER_FOLDER, CONFIG
    RUNNER_FOLDER = runner_folder
    CONFIG = config

    logger = logging.getLogger(__name__)
    logger.info("****************************")
    logger.info(f"Executing workflow {w.name} with id {wf_id}")
    logger.info("****************************")
    # w.print()
    logger.info("****************************")
    logger.info(f"RUNNER_FOLDER: {RUNNER_FOLDER}")
    logger.info("****************************")

    sorted_tasks: List[Task] = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)
    
    import json

    if not os.path.exists("intermediate_files"):
        os.makedirs("intermediate_files")
    with open(EXECUTION_ENGINE_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)
    with open(VARIABLES, 'w') as f:
        json.dump({}, f)
    with open(RESULT, 'w') as f:
        json.dump({}, f)

    for index, task in enumerate(sorted_tasks):
        print("----------------------------")
        print(task.name)
        print(task.impl_file)
        # task.print()
        new_path = f"{LOCAL_HELPER_FULL_PATH}:"
        print(LOCAL_HELPER_FULL_PATH)
        for dependency in task.dependent_modules:
            dependency = dependency.split("/**")[0] if "/**" in dependency else dependency
            new_path += f"{os.path.join(RUNNER_FOLDER, dependency)}:"
        my_env = os.environ.copy()
        my_env["PYTHONPATH"] = new_path
        print(f"new_path: {new_path}")
        new_file_path = os.path.join(os.path.dirname(task.impl_file), f"exec_{os.path.basename(task.impl_file)}")
        print(new_file_path)
        subprocess.run([f"cp {task.impl_file} {new_file_path}"], shell=True)
        resultMap = json.loads(open(RESULT, 'r').read())

        variables = {'PREVIOUS_PROCESS_ID': sorted_tasks[index - 1].name if index > 0 else None, 'task_name': task.name, 'workflow_id': wf_id}
        for input_file in task.input_files:
            path = input_file.path.split("/**")[0] if "/**" in input_file.path else input_file.path
            variables[f'{input_file.name_in_task_signature}'] = str(path) if path else None
        for output_file in task.output_files:
            path = output_file.path.split("/**")[0] if "/**" in output_file.path else output_file.path
            variables[f'{output_file.name_in_task_signature}'] = str(path) if path else None

        if len(task.params) > 0:
            for k, v in task.params.items():
                variables[f'{k}'] = f'{v}'

        with open(new_file_path, 'r+') as fp:
            lines = fp.readlines()
            fp.seek(0)
            fp.truncate()
            first_line = ["import local_helper as ph\n"]
            second_line = [f"variables = {variables}\n"]
            third_line = [f"resultMap = {resultMap}\n"]
            last_line = ["\nph.save_result(resultMap)"]
            filelines = first_line + second_line + third_line + find_and_replace_ResultMapPut(lines[2:]) + last_line
            fp.writelines(filelines)
        subprocess.run(["python -m venv local_env"], shell=True)
        if task.requirements_file is None:
            subprocess.run([f"source ./local_env/bin/activate; python -m pip install --upgrade pip --quiet; pip install {LOCAL_ENV_DEPENDENCIES} --quiet"], shell=True)
        else:
            print(f'configuring vnenv with requirements.txt: {task.requirements_file}')
            subprocess.run([f"source ./local_env/bin/activate; python -m pip install --upgrade pip --quiet; pip install -r {task.requirements_file} --quiet; pip install {LOCAL_ENV_DEPENDENCIES} --quiet"], shell=True)
        result = subprocess.run([f"source ./local_env/bin/activate; python {new_file_path}"], env=my_env, shell=True, capture_output=True, text=True)
        if result.stdout:
            logger.info(f"Task {task.name} stdout: {result.stdout}")
        if result.stderr:
            logger.error(f"Task {task.name} stderr: {result.stderr}")
        if result.returncode != 0:
            logger.error(f"Task {task.name} failed with return code {result.returncode}")

        print("****************************")
