import os
import sys
import pickle
import json
import numpy as np

EXECUTION_ENGINE_MAPPING_FILE_PREFIX = "execution_engine_mapping"
EXECUTION_ENGINE_MAPPING_FILE = next(filename for filename in os.listdir('.')
                                     if filename.startswith(EXECUTION_ENGINE_MAPPING_FILE_PREFIX))

RESULTS_FILE = "experiment_results.json"

with open(EXECUTION_ENGINE_MAPPING_FILE, 'r') as file:
    execution_engine_mapping = json.load(file)


def get_experiment_results():
    if os.path.exists(RESULTS_FILE):
        with open(RESULTS_FILE, 'r') as file:
            return json.load(file)
    print("results file does not exist")
    return None


def save_datasets(variables, *data):
    for (key, value) in data:
        _save_dataset(variables, key, value)


def load_datasets(variables, *keys):
    datasets = [_load_dataset(variables, key) for key in keys]
    if len(datasets) == 1:
        return datasets[0]
    return datasets


def _save_dataset(variables, key, value):
    value_size = sys.getsizeof(value)
    print(f"Saving output data of size {value_size} with key {key}")
    job_id = variables.get("PA_JOB_ID")
    task_id = variables.get("PA_TASK_ID")
    task_folder = os.path.join("/shared", job_id, task_id)
    os.makedirs(task_folder, exist_ok=True)
    output_filename = os.path.join(task_folder, key)
    with open(output_filename, "wb") as outfile:
        pickle.dump(value, outfile)
    variables.put("PREVIOUS_TASK_ID", str(task_id))


def _load_dataset(variables, key):
    print(f"Loading input data with key {key}")
    job_id = variables.get("PA_JOB_ID")
    task_id = variables.get("PREVIOUS_TASK_ID")
    task_folder = os.path.join("/shared", job_id, task_id)
    task_name = variables.get("PA_TASK_NAME")
    if task_name in execution_engine_mapping:
        if key in execution_engine_mapping[task_name]:
            key = execution_engine_mapping[task_name][key]
    input_filename = os.path.join(task_folder, key)
    with open(input_filename, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents


def create_dir(variables, key):
    job_id = variables.get("PA_JOB_ID")
    # TODO Check: shouldn't the next line be PA_TASK_ID instead of PREVIOUS_TASK_ID?
    task_id = variables.get("PREVIOUS_TASK_ID")
    folder = os.path.join("/shared", job_id, task_id, key)
    os.makedirs(folder, exist_ok=True)

    return folder


def get_file_path(variables, data_set_folder_path, file_name):
    folder_path = variables.get(data_set_folder_path)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)
    # TODO remove the next 3 lines once the bug with output files if fixed
    placeholder_path = os.path.join(folder_path, ".placeholder")
    with open(placeholder_path, 'w'):
        pass
    return file_path


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
