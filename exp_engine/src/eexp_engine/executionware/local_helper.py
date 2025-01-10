import os
import sys
import pickle
import json
import numpy as np

EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"

with open(EXECUTION_ENGINE_MAPPING_FILE, 'r') as file:
    execution_engine_mapping = json.load(file)

with open(VARIABLES, 'r') as file:
    previous_variables = json.load(file)

def save_datasets(variables, *data):
    for (key, value) in data:
        _save_dataset(variables, key, value)
    with open(VARIABLES, 'w') as f:
        new_variables = {**previous_variables, **variables}
        json.dump(new_variables, f)


def load_datasets(variables, *keys):
    new_variables = {**previous_variables, **variables}
    datasets = [_load_dataset(new_variables, key) for key in keys]
    if len(datasets)==1:
        return datasets[0]
    return datasets


def _save_dataset(variables, key, value):
    value_size = sys.getsizeof(value)
    print(f"Saving output data of size {value_size} with key {key}")
    process_id = str(os.getpid())
    task_folder = os.path.join("intermediate_files", process_id)
    os.makedirs(task_folder, exist_ok=True)
    output_filename = os.path.join(task_folder, key)
    with open(output_filename, "wb") as outfile:
        pickle.dump(value, outfile)
    variables["PREVIOUS_PROCESS_ID"] = str(process_id)


def _load_dataset(variables, key):
    print(f"Loading input data with key {key}")
    process_id = variables.get("PREVIOUS_PROCESS_ID")
    task_folder = os.path.join("intermediate_files", process_id)
    task_name = variables.get("task_name")
    if task_name in execution_engine_mapping:
        if key in execution_engine_mapping[task_name]:
            key = execution_engine_mapping[task_name][key]
    input_filename = os.path.join(task_folder, key)
    with open(input_filename, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents


def create_dir(variables, key):
    process_id = str(os.getpid())
    folder = os.path.join("intermediate_files", process_id, key)
    os.makedirs(folder, exist_ok=True)
    return folder


def save_result(result):
    with open(RESULT, 'w') as f:
        json.dump(result, f)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
