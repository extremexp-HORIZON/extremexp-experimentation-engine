import os
import sys
import pickle
import json
import numpy as np
import pandas as pd

EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"

with open(EXECUTION_ENGINE_MAPPING_FILE, 'r') as file:
    execution_engine_mapping = json.load(file)

with open(VARIABLES, 'r') as file:
    previous_variables = json.load(file)

def get_experiment_results():
    if os.path.exists(RESULT):
        with open(RESULT, 'r') as file:
            return json.load(file)
    print("results file does not exist")
    return None

def save_datasets(variables, *data):
    for (key, value) in data:
        save_dataset(variables, key, value)
    with open(VARIABLES, 'w') as f:
        new_variables = {**previous_variables, **variables}
        json.dump(new_variables, f)


def load_datasets(variables, *keys):
    new_variables = {**previous_variables, **variables}
    datasets = [load_dataset(new_variables, key) for key in keys]
    if len(datasets)==1:
        return datasets[0]
    return datasets


def save_dataset(variables, resultMap, key, value):
    value_size = sys.getsizeof(value)
    print(f"Saving output data of size {value_size} with key {key}")
    # Use workflow ID instead of process ID
    workflow_id = variables.get("workflow_id", "default_workflow")
    task_name = variables.get("task_name", "default_task")
    path = variables.get(key, None)
    if path:
        task_folder = os.path.dirname(path)
        os.makedirs(task_folder, exist_ok=True)
        with open(path, "w") as outfile:
            outfile.write(value)
    else:
        task_folder = os.path.join("intermediate_files", workflow_id, task_name)
        os.makedirs(task_folder, exist_ok=True)
        output_filename = os.path.join(task_folder, key)
        with open(output_filename, "wb") as outfile:
            pickle.dump(value, outfile)



def load_dataset(variables, resultmap, key):
    print(f"Loading input data with key {key}")
    process_id = variables.get("PREVIOUS_PROCESS_ID")
    workflow_id = variables.get("workflow_id", "default_workflow")
    task_name = variables.get("task_name")
    if task_name in execution_engine_mapping:
        if key in execution_engine_mapping[task_name]:
            key = execution_engine_mapping[task_name][key]
    # If this is the first node of a workflow
    if not process_id:
        file_contents = file_loader(variables[key])
        return file_contents
    # If its not the first node, we load from the intermediate files
    else:
        task_folder = os.path.join("intermediate_files", workflow_id, process_id)
        input_filename = os.path.join(task_folder, key)
        with open(input_filename, "rb") as f:
            file_contents = pickle.load(f)
        return file_contents

def file_loader(file_path):
    if "intermediate_files" in file_path:
        with open(file_path, "rb") as f:
            return pickle.load(f)
    else:
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.json':
            with open(file_path, 'r') as f:
                return json.load(f)
        elif file_extension == '.csv':
            return pd.read_csv(file_path)
        elif file_extension == '.parquet':
            return pd.read_parquet(file_path)
        elif file_extension in ['.xlsx', '.xls']:
            return pd.read_excel(file_path)
        elif file_extension == '.pkl':
            with open(file_path, 'rb') as f:
                return pickle.load(f)
        elif file_extension == '.npy':
            return np.load(file_path)
        elif file_extension == '.npz':
            return np.load(file_path)
        elif file_extension == '.txt':
            with open(file_path, 'r') as f:
                return f.read()
        else:
            raise ValueError(f"Unsupported file format: {file_extension} the local engine supports \
                             only .json, .csv, .parquet, .xlsx, .xls, .pkl, .npy, .npz, and .txt files.")

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
