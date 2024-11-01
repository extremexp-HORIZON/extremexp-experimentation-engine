import os
import sys
import pickle
import json
import numpy as np


def save_datasets(variables, *data):
    for (key, value) in data:
        save_dataset(variables, key, value)


def load_datasets(variables, *keys):
    return [load_dataset(variables, key) for key in keys]


def save_dataset(variables, key, value):
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


def load_dataset(variables, key):
    print(f"Loading input data with key {key}")
    job_id = variables.get("PA_JOB_ID")
    task_id = variables.get("PREVIOUS_TASK_ID")
    task_folder = os.path.join("/shared", job_id, task_id)
    input_filename = os.path.join(task_folder, key)
    with open(input_filename, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents


def create_dir(variables, key):
    job_id = variables.get("PA_JOB_ID")
    task_id = variables.get("PREVIOUS_TASK_ID")
    folder = os.path.join("/shared", job_id, task_id, key)
    os.makedirs(folder, exist_ok=True)

    return folder

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
