import logging
from .proactive_runner import _create_execution_engine_mapping
import subprocess
import os

LOCAL_HELPER_FULL_PATH = os.path.dirname(os.path.abspath(__file__))
EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"


def find_and_replace_ResultMapPut(lines):
    new_lines = []
    for l in lines:
        if "resultMap.put" in l:
            new_line = l.replace("resultMap.put", "resultMap.__setitem__")
            new_lines.append(new_line)
        else:
            new_lines.append(l)
    return new_lines


def execute_wf(w, exp_id, wf_id, runner_folder, config):
    global RUNNER_FOLDER, CONFIG
    RUNNER_FOLDER = runner_folder
    CONFIG = config

    import json
    with open(VARIABLES, 'w') as f:
        variables = {}
        json.dump(variables, f)

    logger = logging.getLogger(__name__)
    logger.info("****************************")
    logger.info(f"Executing workflow {w.name} with id {wf_id}")
    logger.info("****************************")
    # w.print()
    logger.info("****************************")
    logger.info(f"RUNNER_FOLDER: {RUNNER_FOLDER}")
    logger.info("****************************")

    sorted_tasks = sorted(w.tasks, key=lambda t: t.order)
    mapping = _create_execution_engine_mapping(sorted_tasks)
    import json
    with open(EXECUTION_ENGINE_MAPPING_FILE, 'w') as f:
        json.dump(mapping, f)

    for t in sorted_tasks:
        print("----------------------------")
        print(t.name)
        print(t.impl_file)
        # t.print()
        new_path = f"{LOCAL_HELPER_FULL_PATH}:"
        print(LOCAL_HELPER_FULL_PATH)
        for dependency in t.dependent_modules:
            dependency = dependency.split("/**")[0] if "/**" in dependency else dependency
            new_path += f"{os.path.join(RUNNER_FOLDER, dependency)}:"
        my_env = os.environ.copy()
        my_env["PYTHONPATH"] = new_path
        print(f"new_path: {new_path}")
        new_file_path = os.path.join(os.path.dirname(t.impl_file), f"exec_{os.path.basename(t.impl_file)}")
        print(new_file_path)
        subprocess.run([f"cp {t.impl_file} {new_file_path}"], shell=True)

        variables = f"'task_name': '{t.name}', "
        for i in t.input_files:
            if i.path:
                path = i.path.split("/**")[0] if "/**" in i.path else i.path
                variables += f"'{i.name_in_task_signature}': '{path}', "

        for o in t.output_files:
            if o.path:
                path = o.path.split("/**")[0] if "/**" in o.path else o.path
                variables += f"'{o.name_in_task_signature}': '{path}', "

        if len(t.params) > 0:
            for k, v in t.params.items():
                variables += f"'{k}': '{v}', "

        with open(new_file_path, 'r+') as fp:
            lines = fp.readlines()
            fp.seek(0)
            fp.truncate()
            first_line = ["import local_helper as ph\n"]
            second_line = [f"variables = {{{variables}}}\n"]
            third_line = ["resultMap = {}\n"]
            last_line = ["ph.save_result(resultMap)"]
            filelines = first_line + second_line + third_line + find_and_replace_ResultMapPut(lines[2:]) + last_line
            fp.writelines(filelines)
        subprocess.run(["python -m venv local_env"], shell=True)
        print(f'configuring vnenv with requirements.txt: {t.requirements_file}')
        subprocess.run([f"source ./local_env/bin/activate; python -m pip install --upgrade pip --quiet; pip install -r {t.requirements_file} --quiet"], shell=True)
        subprocess.run([f"source ./local_env/bin/activate; python {new_file_path}"], env=my_env, shell=True)

        print("****************************")

    with open(RESULT, 'r') as file:
        result = json.load(file)
        return result
