import os
import sys
import pickle
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

from ..exceptions import (
    DatasetNotFoundError,
    ConfigurationError,
    DataManagementError,
    ValidationError,
)
from ..validation import validate_dataset_inputs, validate_variables, validate_variables_has_key

EXECUTION_ENGINE_MAPPING_FILE = "execution_engine_mapping.json"
VARIABLES = "variables.json"
RESULT = "results.json"

with open(EXECUTION_ENGINE_MAPPING_FILE, 'r') as file:
    execution_engine_mapping = json.load(file)

with open(VARIABLES, 'r') as file:
    previous_variables = json.load(file)

def get_experiment_results() -> Optional[Dict[str, Any]]:
    """
    Get experiment results from the results file.

    Returns:
        Optional[Dict[str, Any]]: Experiment results if file exists, None otherwise
    """
    if os.path.exists(RESULT):
        with open(RESULT, 'r') as file:
            return json.load(file)
    print("results file does not exist")
    return None

def save_datasets(variables: Dict[str, Any], *data) -> None:
    """
    Save multiple datasets.

    Args:
        variables: Runtime variables containing experiment metadata
        *data: Variable number of (key, value) tuples

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate variables
    validate_variables(variables)

    if not data:
        raise ValidationError("At least one (key, value) tuple must be provided")

    for item in data:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValidationError("Each data item must be a (key, value) tuple")
        key, value = item
        if not isinstance(key, str):
            raise ValidationError(f"Key must be a string, got {type(key).__name__}")

    for (key, value) in data:
        save_dataset(variables, key, value)
    with open(VARIABLES, 'w') as f:
        new_variables = {**previous_variables, **variables}
        json.dump(new_variables, f)


def load_datasets(variables: Dict[str, Any], *keys) -> Any:
    """
    Load multiple datasets.

    Args:
        variables: Runtime variables
        *keys: Variable number of dataset keys to load

    Returns:
        Single dataset if one key provided, otherwise list of datasets

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate variables
    validate_variables(variables)

    if not keys:
        raise ValidationError("At least one key must be provided")

    for key in keys:
        if not isinstance(key, str):
            raise ValidationError(f"Key must be a string, got {type(key).__name__}")
        if not key.strip():
            raise ValidationError("Key cannot be an empty string")

    new_variables = {**previous_variables, **variables}
    datasets = [load_dataset(new_variables, key) for key in keys]
    if len(datasets)==1:
        return datasets[0]
    return datasets


def save_dataset(variables: Dict[str, Any], resultMap: Dict[str, Any], key: str, value: Any) -> None:
    """
    Save a single dataset.

    Args:
        variables: Runtime variables containing workflow and task info
        resultMap: Dictionary to store result metadata
        key: Dataset key
        value: Dataset value to save

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if value is None:
        raise ValidationError("value parameter cannot be None")

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



def load_dataset(variables: Dict[str, Any], resultmap: Dict[str, Any], key: str) -> Any:
    """
    Load a single dataset.

    Args:
        variables: Runtime variables
        resultmap: Dictionary to store result metadata
        key: Dataset key to load

    Returns:
        The loaded dataset

    Raises:
        ValidationError: If inputs are invalid
        DatasetNotFoundError: If the dataset cannot be found
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultmap, key)

    print(f"Loading input data with key {key}")
    process_id = variables.get("PREVIOUS_PROCESS_ID")
    workflow_id = variables.get("workflow_id", "default_workflow")
    task_name = variables.get("task_name")

    if task_name in execution_engine_mapping:
        if key in execution_engine_mapping[task_name]:
            key = execution_engine_mapping[task_name][key]

    # If this is the first node of a workflow
    if not process_id:
        if key not in variables:
            raise DatasetNotFoundError(
                f"Key '{key}' not found in variables. Available keys: {list(variables.keys())}"
            )
        file_contents = file_loader(variables[key])
        return file_contents
    # If its not the first node, we load from the intermediate files
    else:
        task_folder = os.path.join("intermediate_files", workflow_id, process_id)
        input_filename = os.path.join(task_folder, key)

        if not os.path.exists(input_filename):
            raise DatasetNotFoundError(
                f"Dataset file not found: {input_filename}"
            )

        with open(input_filename, "rb") as f:
            file_contents = pickle.load(f)
        return file_contents

def file_loader(file_path: str) -> Any:
    """
    Load a file from a file path with automatic format detection.

    Args:
        file_path: Path to the file to load

    Returns:
        The loaded file contents in appropriate format

    Raises:
        ValidationError: If file_path is invalid
        DatasetNotFoundError: If file does not exist
        DataManagementError: If file format is unsupported
    """
    # Validate input
    if not file_path:
        raise ValidationError("file_path parameter cannot be empty")
    if not isinstance(file_path, str):
        raise ValidationError(f"file_path must be a string, got {type(file_path).__name__}")

    if not os.path.exists(file_path):
        raise DatasetNotFoundError(f"File not found: {file_path}")

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
            error_msg = (
                f"Unsupported file format: {file_extension}. "
                f"The local engine supports only .json, .csv, .parquet, .xlsx, .xls, "
                f".pkl, .npy, .npz, and .txt files."
            )
            raise DataManagementError(error_msg)

def create_dir(variables: Dict[str, Any], key: str) -> str:
    """
    Create a directory for intermediate files.

    Args:
        variables: Runtime variables
        key: Directory key/name

    Returns:
        str: Path to the created directory

    Raises:
        ValidationError: If inputs are invalid
    """
    # Validate inputs
    validate_variables(variables)

    if not key:
        raise ValidationError("key parameter cannot be empty")
    if not isinstance(key, str):
        raise ValidationError(f"key must be a string, got {type(key).__name__}")

    process_id = str(os.getpid())
    folder = os.path.join("intermediate_files", process_id, key)
    os.makedirs(folder, exist_ok=True)
    return folder

def save_result(result: Dict[str, Any]) -> None:
    """
    Save experiment result to file.

    Args:
        result: Result dictionary to save

    Raises:
        ValidationError: If result is invalid
    """
    if result is None:
        raise ValidationError("result parameter cannot be None")

    if not isinstance(result, dict):
        raise ValidationError(f"result must be a dict, got {type(result).__name__}")

    with open(RESULT, 'w') as f:
        json.dump(result, f)


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
