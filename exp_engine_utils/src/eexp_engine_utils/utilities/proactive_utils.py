import os
import pickle
import json
import numpy as np
import requests
from io import BytesIO
from typing import List, Dict, Any, Optional

from ..exceptions import (
    DatasetNotFoundError,
    ConfigurationError,
    DataManagementError,
    ValidationError,
)
from ..validation import validate_dataset_inputs, validate_variables, validate_variables_has_key

METRICS_FILES_KEY = "file"
OUTPUT_FILE = "output"
INPUT_FILE = "input"
FILE_TYPE_EXTERNAL = "external"
FILE_TYPE_INTERMEDIATE = "intermediate"
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
EXECUTION_ENGINE_RUNTIME_CONFIG = next(filename for filename in os.listdir('.')
                                     if filename.startswith(EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX))
RESULTS_FILE = "experiment_results.json"

try:
    with open(EXECUTION_ENGINE_RUNTIME_CONFIG, 'r') as file:
        runtime_job_config = json.load(file)
        execution_engine_mapping = runtime_job_config["mapping"]
        exp_engine_metadata = runtime_job_config["exp_engine_metadata"]
        dataset_config = runtime_job_config["dataset_config"]
        DATASET_MANAGEMENT = dataset_config["DATASET_MANAGEMENT"]
        DDM_URL = dataset_config.get("DDM_URL")
        DDM_TOKEN = dataset_config.get("DDM_TOKEN")
except Exception as e:
    raise ConfigurationError(f"Failed to load runtime configuration: {e}")

AUTH_HEADERS = {'Authorization': DDM_TOKEN} if DDM_TOKEN else {}

def get_experiment_results(variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Get experiment results from the results file.

    Args:
        variables: Runtime variables containing workflow ID

    Returns:
        Optional[Dict[str, Any]]: Experiment results if file exists, None otherwise

    Raises:
        ValidationError: If variables is invalid or missing required keys
    """
    # Validate input
    validate_variables(variables)
    validate_variables_has_key(variables, "wf_id", "variables")

    wf_id = variables.get('wf_id')
    results_file = f"experiment_results_{wf_id}.json"

    if os.path.exists(results_file):
        with open(results_file, 'r') as file:
            return json.load(file)

    raise FileNotFoundError(f"Experiment results file '{results_file}' does not exist")


def save_datasets(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    values: List[BytesIO],
    file_names: Optional[List[str]] = None,
) -> None:
    """
    Save multiple datasets (requires DDM).

    Args:
        variables: Runtime variables containing experiment metadata
        resultMap: Dictionary to store result metadata
        key: Dataset key
        values: List of dataset values to save
        file_names: Optional list of filenames for the datasets

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not DDM
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if values is None:
        raise ValidationError("values parameter cannot be None")

    if not isinstance(values, list):
        raise ValidationError(
            f"values must be a list, got {type(values).__name__}"
        )

    if len(values) == 0:
        raise ValidationError("values list cannot be empty")

    if file_names is not None:
        if not isinstance(file_names, list):
            raise ValidationError(
                f"file_names must be a list or None, got {type(file_names).__name__}"
            )
        if len(file_names) != len(values):
            raise ValidationError(
                f"file_names length ({len(file_names)}) must match values length ({len(values)})"
            )

    if DATASET_MANAGEMENT == "DDM":
        return save_datasets_ddm(variables, resultMap, key, values, file_names)

    error_msg = (
        f"save_datasets is only available for DDM, but DATASET_MANAGEMENT is '{DATASET_MANAGEMENT}'. "
        f"Please update your configuration."
    )
    raise ConfigurationError(error_msg)


def save_dataset(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    value: BytesIO
) -> None:
    """
    Save a single dataset.

    Args:
        variables: Runtime variables containing experiment metadata
        resultMap: Dictionary to store result metadata
        key: Dataset key
        value: Dataset value to save

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not properly configured
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if value is None:
        raise ValidationError("value parameter cannot be None")

    if not isinstance(value, BytesIO):
        raise ValidationError(
            f"value must be a BytesIO object, got {type(value).__name__}"
        )

    if DATASET_MANAGEMENT == "LOCAL":
        return save_dataset_local(variables, resultMap, key, value)

    if DATASET_MANAGEMENT == "DDM":
        return save_datasets_ddm(variables, resultMap, key, [value])

    error_msg = (
        f"save_dataset requires DATASET_MANAGEMENT to be 'LOCAL' or 'DDM', "
        f"but got '{DATASET_MANAGEMENT}'. Please check your configuration."
    )
    raise ConfigurationError(error_msg)


def save_dataset_local(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    value: BytesIO
) -> None:
    """Save dataset locally using ProActive."""

    # Validate required keys
    validate_variables_has_key(variables, "PA_JOB_ID", "variables")
    validate_variables_has_key(variables, "PA_TASK_ID", "variables")

    if key in variables:
        output_file_path = variables.get(key)
        folder_path = output_file_path.rsplit("/", 1)[0]
        _create_folder(folder_path)
        with open(output_file_path, "wb") as outfile:
            outfile.write(value)
        print(f"Saved external output data to {output_file_path}")
    else:
        job_id = variables.get("PA_JOB_ID")
        task_id = variables.get("PA_TASK_ID")
        task_folder = os.path.join("/shared", job_id, task_id)
        os.makedirs(task_folder, exist_ok=True)
        output_file_path = os.path.join(task_folder, key)
        with open(output_file_path, "wb") as outfile:
            pickle.dump(value, outfile)
        variables.put("PREVIOUS_TASK_ID", str(task_id))
        print(f"Saved intermediate output data to {output_file_path}")

    if resultMap is not None:
        print(f"Adding file path '{output_file_path}' for key '{key}' to result map")
        resultMap.put(key, output_file_path)


def save_datasets_ddm(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    values: List[bytes],
    file_names: Optional[List[str]] = None
) -> None:
    """Save multiple datasets to DDM using ProActive."""
    # Validate required configuration
    if not DDM_URL:
        raise ConfigurationError("DDM_URL is required when DATASET_MANAGEMENT=DDM")
    if not DDM_TOKEN:
        raise ConfigurationError("DDM_TOKEN is required when DATASET_MANAGEMENT=DDM")

    # Validate required keys
    validate_variables_has_key(variables, "PA_TASK_NAME", "variables")
    validate_variables_has_key(variables, "PA_JOB_NAME", "variables")

    upload_url = f"{DDM_URL}/ddm/files/upload"
    file_url_template = f"{DDM_URL}/ddm/file/{{}}"
    task_name = variables['PA_TASK_NAME']
    variables.put("PREVIOUS_TASK_ID", str(task_name))

    project_id_prefix = os.path.join(exp_engine_metadata["exp_name"],
                                     exp_engine_metadata["exp_id"],
                                     exp_engine_metadata["wf_id"])
    if key in variables:
        file_type = FILE_TYPE_EXTERNAL
        ddm_value = variables.get(key)
        ddm_value_parts = ddm_value.split("|")
        output_file_name = ddm_value_parts[0]
        project_name = ddm_value_parts[1]
        project_id = os.path.join(project_id_prefix, OUTPUT_FILE, task_name)
        if project_name:
            project_id = os.path.join(project_id, project_name)
    else:
        file_type = FILE_TYPE_INTERMEDIATE
        output_file_name = key
        project_id = os.path.join(project_id_prefix, OUTPUT_FILE, task_name)
    provided_output_file_name = output_file_name
    result_value = []
    result_key = f"file:{task_name}:{OUTPUT_FILE}:{key}"
    for i in range(len(values)):
        value = values[i]
        if len(provided_output_file_name) == 0:
            if file_names:
                output_file_name = file_names[i]
            else:
                output_file_name = f"output_{i}"
        try:
            file_bytes = BytesIO(value)
            upload_files = []
            upload_files.append(("files", (output_file_name, file_bytes, "application/octet-stream")))

            metadata_files = []
            file_metadata = {"dataset_signature": key, 'task': task_name, 'assembled_wf': variables['PA_JOB_NAME']}
            metadata_json = json.dumps(file_metadata)
            metadata_bytes = BytesIO(metadata_json.encode("utf-8"))
            metadata_files.append(("metadata-files", ("", metadata_bytes, "application/json")))

        except Exception:
            raise

        form_data = {
            "project_id": project_id,
            "descriptions": "Generated by the exp engine",
        }
        all_files = upload_files + metadata_files

        print(f"Uploading file to DDM: {upload_url}")
        response = requests.post(upload_url, headers=AUTH_HEADERS, files=all_files, data=form_data)
        print(f"Upload response status: {response.status_code}")

        # Check if response is empty
        if not response.content:
            error_msg = "Empty response from DDM upload API"
            raise DataManagementError(error_msg)

        generated_file_id = response.json()["files"][0]["id"]
        file_url = file_url_template.format(generated_file_id)
        file_metadata = _return_file_metadata(output_file_name, file_url, project_id, file_type)
        result_value.append(file_metadata)

    resultMap.put(result_key, json.dumps(result_value))


def load_datasets(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str
) -> List[BytesIO]:
    """
    Load multiple datasets (requires DDM).

    Args:
        variables: Runtime variables containing experiment metadata
        resultMap: Dictionary to store result metadata
        key: Dataset key to load

    Returns:
        List[BytesIO]: List of loaded datasets

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not DDM
        DatasetNotFoundError: If datasets cannot be found
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if DATASET_MANAGEMENT == "DDM":
        return load_datasets_ddm(variables, key, resultMap)

    error_msg = (
        f"load_datasets is only available for DDM, but DATASET_MANAGEMENT is '{DATASET_MANAGEMENT}'. "
        f"Please update your configuration."
    )
    raise ConfigurationError(error_msg)


def load_dataset(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str
) -> BytesIO:
    """
    Load a single dataset.

    Args:
        variables: Runtime variables containing experiment metadata
        resultMap: Dictionary to store result metadata
        key: Dataset key to load

    Returns:
        BytesIO: The loaded dataset

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        DatasetNotFoundError: If the dataset cannot be found
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if DATASET_MANAGEMENT == "LOCAL":
        return load_dataset_local(variables, key)

    if DATASET_MANAGEMENT == "DDM":
        return load_datasets_ddm(variables, key, resultMap)[0]

    error_msg = (
        f"load_dataset requires DATASET_MANAGEMENT to be 'LOCAL' or 'DDM', "
        f"but got '{DATASET_MANAGEMENT}'. Please check your configuration."
    )
    raise ConfigurationError(error_msg)


def load_dataset_local(variables: Dict[str, Any], key: str) -> BytesIO:
    """Load dataset from local storage using ProActive."""
    print(f"Loading input data with key '{key}'")

    # Validate required keys
    validate_variables_has_key(variables, "PA_JOB_ID", "variables")
    validate_variables_has_key(variables, "PA_TASK_NAME", "variables")

    if key in variables:
        input_filename = variables.get(key)
        return load_dataset_by_path(input_filename)
    else:
        job_id = variables.get("PA_JOB_ID")
        task_id = variables.get("PREVIOUS_TASK_ID")
        task_folder = os.path.join("/shared", job_id, task_id)
        task_name = variables.get("PA_TASK_NAME")
        if task_name in execution_engine_mapping:
            if key in execution_engine_mapping[task_name]:
                key = execution_engine_mapping[task_name][key]
        input_filename = os.path.join(task_folder, key)
        return load_pickled_dataset_by_path(input_filename)


def load_datasets_ddm(
    variables: Dict[str, Any],
    key: str,
    resultMap: Dict[str, Any]
) -> List[BytesIO]:
    """Load multiple datasets from DDM using ProActive."""
    # Validate required configuration
    if not DDM_URL:
        raise ConfigurationError("DDM_URL is required when DATASET_MANAGEMENT=DDM")
    if not DDM_TOKEN:
        raise ConfigurationError("DDM_TOKEN is required when DATASET_MANAGEMENT=DDM")

    # Validate required keys
    validate_variables_has_key(variables, "PA_TASK_NAME", "variables")

    file_url_template = f"{DDM_URL}/ddm/file/{{}}"
    task_name = variables.get("PA_TASK_NAME")
    if key in variables:
        file_type = FILE_TYPE_EXTERNAL
        ddm_value = variables.get(key)
        ddm_value_parts = ddm_value.split("|")
        fname = ddm_value_parts[0]
        project_id = ddm_value_parts[1]
    else:
        file_type = FILE_TYPE_INTERMEDIATE
        fname = key
        if task_name in execution_engine_mapping:
            if fname in execution_engine_mapping[task_name]:
                fname = execution_engine_mapping[task_name][fname]
        task_id = variables.get("PREVIOUS_TASK_ID")
        project_id_prefix = os.path.join(exp_engine_metadata["exp_name"],
                                         exp_engine_metadata["exp_id"],
                                         exp_engine_metadata["wf_id"])
        project_id = os.path.join(project_id_prefix, OUTPUT_FILE, task_id)
    results = _look_up_file_in_catalog(fname, project_id)

    contents = []
    result_key = f"file:{task_name}:{INPUT_FILE}:{key}"
    result_value = []
    for entry in results:
        file_id = entry.get("id")
        file_url = file_url_template.format(file_id)
        print(f"Downloading file from DDM: {file_url}")
        f_response = requests.get(file_url, headers=AUTH_HEADERS)
        file_metadata = _return_file_metadata(entry.get("upload_filename"), file_url, project_id, file_type)
        result_value.append(file_metadata)
        f_response.raise_for_status()
        contents.append(f_response.content)
    resultMap.put(result_key, json.dumps(result_value))
    return contents

def _return_file_metadata(
    file_name: str,
    file_url: str,
    project_id: str,
    file_type: str
) -> Dict[str, str]:
    """
    Create file metadata dictionary.

    Args:
        file_name: Name of the file
        file_url: URL to access the file
        project_id: Project identifier
        file_type: Type of file (external or intermediate)

    Returns:
        Dict[str, str]: File metadata dictionary
    """
    file_metadata = {
        "file_name": file_name,
        "file_url": file_url,
        "project_id": project_id,
        "file_type": file_type
    }
    return file_metadata


def _look_up_file_in_catalog(fname: str, project_id: str) -> List[Dict[str, Any]]:
    """
    Look up files in DDM catalog.

    Args:
        fname: Filename to search for
        project_id: Project ID to search within

    Returns:
        List[Dict[str, Any]]: List of matching file entries

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DDM is not properly configured
        DataManagementError: If DDM request fails
        DatasetNotFoundError: If no matching files found
    """
    # Validate inputs
    if not fname:
        raise ValidationError("fname parameter cannot be empty")
    if not isinstance(fname, str):
        raise ValidationError(f"fname must be a string, got {type(fname).__name__}")
    if not project_id:
        raise ValidationError("project_id parameter cannot be empty")
    if not isinstance(project_id, str):
        raise ValidationError(f"project_id must be a string, got {type(project_id).__name__}")

    # Validate configuration
    if not DDM_URL:
        raise ConfigurationError("DDM_URL is required for DDM catalog lookup")

    catalog_url = f"{DDM_URL}/ddm/catalog/list"

    try:
        r = requests.get(
            catalog_url,
            headers=AUTH_HEADERS,
            params={
                "filename": fname,
                "project_id": project_id,
                "perPage": 5000,
            }
        )
        r.raise_for_status()
    except requests.RequestException as e:
        error_msg = f"Failed to query DDM catalog: {e}"
        raise DataManagementError(error_msg)

    results = r.json().get("data", [])
    if not results:
        error_msg = f"No files with name '{fname}' found in DDM"
        raise DatasetNotFoundError(error_msg)

    results = [r for r in results if r["project_id"] == project_id]
    if len(results) == 0:
        error_msg = f"No files with name '{fname}' found in project '{project_id}'"
        raise DatasetNotFoundError(error_msg)

    return results


def load_pickled_dataset_by_path(file_path: str):
    """
    Load a pickled dataset from a file path.

    Args:
        file_path: Path to the pickled file

    Returns:
        The unpickled object

    Raises:
        ValidationError: If file_path is invalid
        FileNotFoundError: If file does not exist
    """
    # Validate input
    if not file_path:
        raise ValidationError("file_path parameter cannot be empty")
    if not isinstance(file_path, str):
        raise ValidationError(f"file_path must be a string, got {type(file_path).__name__}")

    with open(file_path, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents


def load_dataset_by_path(file_path: str) -> bytes:
    """
    Load a dataset from a file path.

    Args:
        file_path: Path to the file

    Returns:
        bytes: File contents as bytes

    Raises:
        ValidationError: If file_path is invalid
        FileNotFoundError: If file does not exist
    """
    # Validate input
    if not file_path:
        raise ValidationError("file_path parameter cannot be empty")
    if not isinstance(file_path, str):
        raise ValidationError(f"file_path must be a string, got {type(file_path).__name__}")

    with open(file_path, "rb") as f:
        file_contents = BytesIO(f.read())
    return file_contents.getvalue()


def create_dir(variables: Dict[str, Any], key: str) -> str:
    """
    Create a directory for a dataset.

    Args:
        variables: Runtime variables containing job and task IDs
        key: Dataset key

    Returns:
        str: Path to the created directory

    Raises:
        ValidationError: If inputs are invalid
    """
    validate_variables_has_key(variables, "PA_JOB_ID", "variables")
    validate_variables_has_key(variables, "PA_TASK_ID", "variables")

    job_id = variables.get("PA_JOB_ID")
    task_id = variables.get("PA_TASK_ID")
    folder = os.path.join("/shared", job_id, task_id, key)
    os.makedirs(folder, exist_ok=True)

    return folder


def get_file_path(variables: Dict[str, Any], data_set_folder_path: str, file_name: str) -> str:
    """
    Get the file path for a dataset file.

    Args:
        variables: Runtime variables
        data_set_folder_path: Key to the folder path in variables
        file_name: Name of the file

    Returns:
        str: Full file path

    Raises:
        ValidationError: If inputs are invalid
    """
    if not data_set_folder_path:
        raise ValidationError("data_set_folder_path parameter cannot be empty")
    if not file_name:
        raise ValidationError("file_name parameter cannot be empty")

    validate_variables_has_key(variables, data_set_folder_path, "variables")

    folder_path = variables.get(data_set_folder_path)
    file_path = os.path.join(folder_path, file_name)
    _create_folder(folder_path)

    return file_path


def _create_folder(folder_path: str) -> None:
    """
    Create a folder and add a placeholder file.

    Args:
        folder_path: Path to the folder to create
    """
    os.makedirs(folder_path, exist_ok=True)
    # TODO remove the next 3 lines once the bug with output files is fixed
    placeholder_path = os.path.join(folder_path, ".placeholder")
    with open(placeholder_path, 'w'):
        pass


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)
