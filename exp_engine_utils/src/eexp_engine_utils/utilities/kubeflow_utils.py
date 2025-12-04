from io import BytesIO
import os
import pickle
from typing import List, Dict, Any, Optional
import requests
import json
import fsspec
from minio import Minio

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
try:
    DDM_URL = os.getenv("DDM_URL")
    DDM_TOKEN = os.getenv("DDM_TOKEN")
    DATASET_MANAGEMENT = os.getenv("DATASET_MANAGEMENT")
    DATA_ABSTRACTION_BASE_URL = os.getenv("DATA_ABSTRACTION_BASE_URL")
    DATA_ABSTRACTION_ACCESS_TOKEN = os.getenv("DATA_ABSTRACTION_ACCESS_TOKEN")
    MINIO_USERNAME = os.getenv("KUBEFLOW_MINIO_USERNAME")
    MINIO_PASSWORD = os.getenv("KUBEFLOW_MINIO_PASSWORD")
    # MinIO endpoint without protocol (for minio.Minio client)
    MINIO_ENDPOINT = "minio-service.kubeflow:9000"
    # MinIO endpoint with protocol (for fsspec/s3fs client)
    MINIO_ENDPOINT_URL = "http://minio-service.kubeflow:9000"
    AUTH_HEADERS = {"Authorization": DDM_TOKEN}
except Exception as e:
    DDM_URL = None
    AUTH_HEADERS = {}


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
        with open(results_file, "r") as file:
            return json.load(file)

    return None


def save_datasets(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    values: List[BytesIO],
    file_names: Optional[List[str]] = None,
) -> None:
    """
    Save multiple datasets.

    Args:
        variables: Runtime variables containing experiment metadata and mappings
        resultMap: Dictionary to store result metadata
        key: Dataset key
        values: List of dataset values to save (BytesIO objects)
        file_names: Optional list of filenames for the datasets

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not properly configured
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

    for i, value in enumerate(values):
        if not isinstance(value, BytesIO):
            raise ValidationError(
                f"values[{i}] must be a BytesIO object, got {type(value).__name__}"
            )

    if file_names is not None:
        if not isinstance(file_names, list):
            raise ValidationError(
                f"file_names must be a list or None, got {type(file_names).__name__}"
            )
        if len(file_names) != len(values):
            raise ValidationError(
                f"file_names length ({len(file_names)}) must match values length ({len(values)})"
            )

    if DATASET_MANAGEMENT == "LOCAL":
        for i in range(len(values)):
            save_dataset_local(variables, resultMap, key, values[i])
        return

    if DATASET_MANAGEMENT == "DDM":
        return save_datasets_ddm(variables, resultMap, key, values, file_names)

    error_msg = (
        f"save_datasets requires DATASET_MANAGEMENT to be 'LOCAL' or 'DDM', "
        f"but got '{DATASET_MANAGEMENT}'. Please check your configuration."
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
        variables: Runtime variables.
        resultMap: Dictionary to store result metadata
        key: Dataset key
        value: Dataset value to save (BytesIO object)

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


def load_datasets(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str
) -> List[BytesIO]:
    """
    Load multiple datasets.

    Args:
        variables: Runtime variables.
        resultMap: Dictionary to store result metadata
        key: Dataset key to load

    Returns:
        List[BytesIO]: List of loaded datasets

    Raises:
        ValidationError: If inputs are invalid
        ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        DatasetNotFoundError: If datasets cannot be found
    """
    # Validate inputs
    validate_dataset_inputs(variables, resultMap, key)

    if DATASET_MANAGEMENT == "LOCAL":
        return [load_dataset_local(variables, key)]

    if DATASET_MANAGEMENT == "DDM":
        return load_datasets_ddm(variables, key, resultMap)

    error_msg = (
        f"load_datasets requires DATASET_MANAGEMENT to be 'LOCAL' or 'DDM', "
        f"but got '{DATASET_MANAGEMENT}'. Please check your configuration."
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
        variables: Runtime variables.
        resultMap: Dictionary to store result metadata
        key: Dataset key to load

    Returns:
        BytesIO: The loaded dataset as a file-like object

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


########## LOCAL DATASET MANAGEMENT #############


def save_dataset_local(
    variables: Dict[str, Any],
    resultMap: Dict[str, Any],
    key: str,
    value: BytesIO
) -> None:
    """Save dataset locally."""
    # Validate required keys in variables
    validate_variables_has_key(variables, "exp_engine_metadata", "variables")
    validate_variables_has_key(variables, "task_name", "variables")

    exp_engine_metadata = variables.get("exp_engine_metadata")
    if not isinstance(exp_engine_metadata, dict):
        raise ValidationError("exp_engine_metadata must be a dict")

    validate_variables_has_key(exp_engine_metadata, "wf_id", "exp_engine_metadata")

    workflow_id = exp_engine_metadata.get("wf_id")
    task_id = variables.get("task_name")
    task_outputs = variables.get("mapping", {}).get(task_id, {}).get("outputs", {})
    output_file_path = ""

    # Check if key is in outputs
    if key not in task_outputs:
        error_msg = f"Output key '{key}' not defined in task outputs mapping for task '{task_id}'"
        raise ValidationError(error_msg)

    file_type = task_outputs[key].get("file_type", "intermediate")

    if file_type == "intermediate":
        task_folder = os.path.join("/shared", workflow_id, task_id)
        os.makedirs(task_folder, exist_ok=True)
        output_file_path = os.path.join(task_folder, key)

        with open(output_file_path, "wb") as outfile:
            pickle.dump(value, outfile)

        print(f"Saved output data to {output_file_path}")

    else:
        file_path = task_outputs[key].get("file_path", "")
        client = Minio(
                    MINIO_ENDPOINT,
                    access_key=MINIO_USERNAME,
                    secret_key=MINIO_PASSWORD,
                    secure=False
                )
        # Local external save file handling
        client.put_object(
            bucket_name="workflow-outputs",
            object_name=f"{workflow_id}/{key}",
            data=value,
            length=len(value.getvalue()),
            metadata={"save-path": file_path}
        )
        output_file_path = f"s3://workflow-outputs/{workflow_id}/{key}"
        print(f"Saved output data to MinIO: s3://workflow-outputs/{workflow_id}/{key}")


    if resultMap is not None:
        print(f"Adding file path '{output_file_path}' for key '{key}' to result map")
        resultMap[key] = output_file_path


def load_dataset_local(variables: Dict[str, Any], key: str) -> BytesIO:
    """Load dataset from local storage (filesystem or MinIO)."""
    print(f"Loading input data with key '{key}'")

    # Validate required keys
    validate_variables_has_key(variables, "exp_engine_metadata", "variables")
    validate_variables_has_key(variables, "task_name", "variables")

    exp_engine_metadata = variables.get("exp_engine_metadata")
    if not isinstance(exp_engine_metadata, dict):
        raise ValidationError("exp_engine_metadata must be a dict")

    validate_variables_has_key(exp_engine_metadata, "wf_id", "exp_engine_metadata")

    workflow_id = exp_engine_metadata.get("wf_id")
    current_task_name = variables.get("task_name")
    mapping = variables.get("mapping", {})

    # Check mapping for input file details
    if current_task_name in mapping:
        # Check if key is in inputs
        if key in mapping[current_task_name]["inputs"]:
            # Get mapping info
            mapping_info = mapping[current_task_name]["inputs"][key]
            # Determine file type
            if mapping_info["file_type"] == "external":
                # Open file from MinIO
                file_path = mapping_info.get("file_path", "")
                if file_path.startswith("s3://"):
                    return open_minio_file(file_path)
                else:
                    raise Exception(f"Invalid S3 path format: {file_path}")
            else:  # intermediate file
                source_task = mapping_info["source_task"]
                output_name = mapping_info["file_name"]

                # Build path using source task name
                task_folder = os.path.join("/shared", workflow_id, source_task)
                input_filename = os.path.join(task_folder, output_name)

                # Return open file object for consistency
                return open(input_filename, 'rb')

    error_msg = f"Could not resolve input '{key}' for task '{current_task_name}'"
    raise DatasetNotFoundError(error_msg)


########## DDM DATASET MANAGEMENT #############


def load_datasets_ddm(variables: dict, key: str, resultMap: dict) -> List[BytesIO]:
    """Load multiple datasets from DDM."""
    # Validate required configuration
    if not DDM_URL:
        raise ConfigurationError("DDM_URL is required when DATASET_MANAGEMENT=DDM")
    if not DDM_TOKEN:
        raise ConfigurationError("DDM_TOKEN is required when DATASET_MANAGEMENT=DDM")

    # Validate required keys in variables
    validate_variables_has_key(variables, "exp_engine_metadata", "variables")
    validate_variables_has_key(variables, "task_name", "variables")

    execution_engine_mapping = variables.get("mapping", {})
    exp_engine_metadata = variables.get("exp_engine_metadata", {})

    if not isinstance(exp_engine_metadata, dict):
        raise ValidationError("exp_engine_metadata must be a dict")

    file_url_template = f"{DDM_URL}/ddm/file/{{}}"
    current_task_name = variables.get("task_name")
    task_inputs = execution_engine_mapping.get(current_task_name, {}).get("inputs", {})

    if key in task_inputs:
        if task_inputs[key].get("file_type") == "external":
            file_type = FILE_TYPE_EXTERNAL
            ddm_value = task_inputs[key].get("file_path")
            ddm_value_parts = ddm_value.split("|")
            project_id = ddm_value_parts[0]
            fname = ddm_value_parts[1]
        else:
            file_type = FILE_TYPE_INTERMEDIATE
            fname = key
            source_task_name = task_inputs[key].get("source_task")
            fname = task_inputs[key].get("file_name")
            project_id_prefix = os.path.join(
                exp_engine_metadata["exp_name"],
                exp_engine_metadata["exp_id"],
                exp_engine_metadata["wf_id"],
            )
            # For intermediate files, look in the OUTPUT_FILE of the source task
            project_id = os.path.join(project_id_prefix, OUTPUT_FILE, source_task_name) if source_task_name else os.path.join(project_id_prefix, INPUT_FILE, current_task_name)
    else:
        error_msg = f"Input key '{key}' not found in task inputs"
        raise DatasetNotFoundError(error_msg)
    
    results = _look_up_file_in_catalog(fname, project_id)

    contents = []
    result_key = f"file:{current_task_name}:{INPUT_FILE}:{key}"
    result_value = []
    for entry in results:
        file_id = entry.get("id")
        file_url = file_url_template.format(file_id)
        print(f"Downloading file from DDM: {file_url}")
        f_response = requests.get(file_url, headers=AUTH_HEADERS)
        file_metadata = _return_file_metadata(
            entry.get("upload_filename"), file_url, project_id, file_type
        )
        result_value.append(file_metadata)
        f_response.raise_for_status()
        contents.append(BytesIO(f_response.content))
    resultMap[result_key] = json.dumps(result_value)
    return contents


def save_datasets_ddm(
    variables: dict, resultMap: dict, key: str, values: List[bytes], file_names: list[str] = None
):
    """Save multiple datasets to DDM."""
    # Validate required configuration
    if not DDM_URL:
        raise ConfigurationError("DDM_URL is required when DATASET_MANAGEMENT=DDM")
    if not DDM_TOKEN:
        raise ConfigurationError("DDM_TOKEN is required when DATASET_MANAGEMENT=DDM")

    # Validate required keys in variables
    validate_variables_has_key(variables, "exp_engine_metadata", "variables")
    validate_variables_has_key(variables, "task_name", "variables")

    exp_engine_metadata = variables.get("exp_engine_metadata", {})
    if not isinstance(exp_engine_metadata, dict):
        raise ValidationError("exp_engine_metadata must be a dict")

    # Validate required metadata keys
    validate_variables_has_key(exp_engine_metadata, "exp_name", "exp_engine_metadata")
    validate_variables_has_key(exp_engine_metadata, "exp_id", "exp_engine_metadata")
    validate_variables_has_key(exp_engine_metadata, "wf_id", "exp_engine_metadata")

    upload_url = f"{DDM_URL}/ddm/files/upload"
    file_url_template = f"{DDM_URL}/ddm/file/{{}}"
    execution_engine_mapping = variables.get("mapping", {})
    current_task_name = variables.get("task_name")
    task_outputs = execution_engine_mapping.get(current_task_name, {}).get("outputs", {})

    project_id_prefix = os.path.join(
        exp_engine_metadata["exp_name"],
        exp_engine_metadata["exp_id"],
        exp_engine_metadata["wf_id"],
    )
    if key in task_outputs:
        if task_outputs[key].get("file_type") == "external":
            file_type = FILE_TYPE_EXTERNAL
            ddm_value = variables.get(key)
            ddm_value_parts = ddm_value.split("|")
            project_name = ddm_value_parts[0]
            output_file_name = ddm_value_parts[1]
            project_id = os.path.join(project_id_prefix, OUTPUT_FILE, current_task_name)
            if project_name:
                project_id = os.path.join(project_id, project_name)
        else:
            file_type = FILE_TYPE_INTERMEDIATE
            output_file_name = key
            project_id = os.path.join(project_id_prefix, OUTPUT_FILE, current_task_name)
    else:
        error_msg = f"Output key '{key}' not found in task outputs"
        raise ValidationError(error_msg)
    
    provided_output_file_name = output_file_name
    result_value = []
    result_key = f"file:{current_task_name}:{OUTPUT_FILE}:{key}"
    upload_files = []
    metadata_files = []
    for i in range(len(values)):
        value = values[i]
        if len(provided_output_file_name) == 0:
            if file_names:
                output_file_name = file_names[i]
            else:
                output_file_name = f"output_{i}"
        try:
            file_bytes = BytesIO(value)
            upload_files.append(
                ("files", (output_file_name, file_bytes, "application/octet-stream"))
            )

            file_metadata = {
                "dataset_signature": key,
                "task": current_task_name,
                "assembled_wf": exp_engine_metadata["wf_id"],
            }
            metadata_json = json.dumps(file_metadata)
            metadata_bytes = BytesIO(metadata_json.encode("utf-8"))
            metadata_files.append(
                ("metadata-files", ("", metadata_bytes, "application/json"))
            )

        except Exception:
            raise

        form_data = {
            "project_id": project_id,
            "descriptions": "Generated by the exp engine",
        }
        all_files = upload_files + metadata_files

        print(f"Uploading file to DDM: {upload_url}")
        response = requests.post(
            upload_url, headers=AUTH_HEADERS, files=all_files, data=form_data
        )
        print(f"Upload response status: {response.status_code}")

        # Check if response is empty
        if not response.content:
            error_msg = "Empty response from DDM upload API"
            raise DataManagementError(error_msg)

        generated_file_id = response.json()["files"][0]["id"]
        file_url = file_url_template.format(generated_file_id)
        file_metadata = _return_file_metadata(
            output_file_name, file_url, project_id, file_type
        )
        result_value.append(file_metadata)

    resultMap[result_key] = json.dumps(result_value)


########## HELPER FUNCTIONS #############


def open_minio_file(s3_path: str) -> BytesIO:
    """
    Open a file from MinIO using fsspec and return a file-like object.
    User can read bytes by calling .read() on the returned object.

    Args:
        s3_path: Full S3 URI (e.g., "s3://bucket-name/path/to/file")

    Returns:
        File-like object that supports .read(), .read(size), iteration, etc.
        Works with any file format - pickle, numpy, pandas, custom binary, etc.

    Raises:
        ValidationError: If s3_path is invalid
        ConfigurationError: If MinIO credentials are not configured
        DataManagementError: If file cannot be opened

    Example usage in task:
        file_obj = load_dataset(variables, resultMap, "my_input")
        data = file_obj.read()  # Read all bytes
        # OR
        chunk = file_obj.read(1024*1024)  # Read 1MB chunk
        # OR
        import pickle
        obj = pickle.load(file_obj)  # Works directly!
    """
    # Validate s3_path
    if not s3_path:
        raise ValidationError("s3_path parameter cannot be empty")
    if not isinstance(s3_path, str):
        raise ValidationError(f"s3_path must be a string, got {type(s3_path).__name__}")
    if not s3_path.startswith("s3://"):
        raise ValidationError(f"s3_path must start with 's3://', got: {s3_path}")

    # Validate MinIO configuration
    if not MINIO_USERNAME:
        raise ConfigurationError("KUBEFLOW_MINIO_USERNAME environment variable is not set")
    if not MINIO_PASSWORD:
        raise ConfigurationError("KUBEFLOW_MINIO_PASSWORD environment variable is not set")

    print(f"Opening file from MinIO: {s3_path}")

    try:
        # Create MinIO client using environment variables
        # Create fsspec filesystem for S3/MinIO
        fs = fsspec.filesystem('s3',
            key=MINIO_USERNAME,
            secret=MINIO_PASSWORD,
            client_kwargs={
                'endpoint_url': MINIO_ENDPOINT_URL,
                'use_ssl': False
            }
        )

        # Open and return file object - fsspec handles the path parsing
        file_obj = fs.open(s3_path, 'rb')

        return file_obj

    except Exception as e:
        error_msg = f"Error opening file from MinIO: {e}"
        raise DataManagementError(error_msg)


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


def _return_file_metadata(
    file_name: str, file_url: str, project_id: str, file_type: str
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
        "file_type": file_type,
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
            },
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