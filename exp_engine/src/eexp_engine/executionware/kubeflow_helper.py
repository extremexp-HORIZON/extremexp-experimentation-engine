from io import BytesIO
import logging
import os
import sys
import pickle
from typing import List
import requests
import json
import fsspec
from minio import Minio

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
    print(f"Error loading configuration: {e}")
    DDM_URL = None
    AUTH_HEADERS = {}


def get_experiment_results(variables: dict):
    if os.path.exists(f"experiment_results_{variables.get('wf_id')}.json"):
        with open(f"experiment_results_{variables.get('wf_id')}.json", "r") as file:
            return json.load(file)
    print("results file does not exist")
    return None


def save_datasets(
    variables: dict,
    resultMap: dict,
    key: str,
    values: list[BytesIO],
    file_names: list[str] = None,
):
    if DATASET_MANAGEMENT == "LOCAL":
        for i in range(len(values)):
            save_dataset_local(variables, resultMap, key, values[i])
        return
    if DATASET_MANAGEMENT == "DDM":
        return save_datasets_ddm(variables, resultMap, key, values, file_names)
    print("save_datasets is only available for DDM, please update your config.py")
    exit(1)


def save_dataset(variables: dict, resultMap: dict, key: str, value: BytesIO):
    if DATASET_MANAGEMENT == "LOCAL":
        return save_dataset_local(variables, resultMap, key, value)
    if DATASET_MANAGEMENT == "DDM":
        return save_datasets_ddm(variables, resultMap, key, [value])
    print("Cannot load dataset, please setup DATASET_MANAGEMENT in config.py")
    exit(1)


def load_datasets(variables: dict, resultMap: dict, key: str):
    if DATASET_MANAGEMENT == "LOCAL":
        return [load_dataset_local(variables, key)]
    if DATASET_MANAGEMENT == "DDM":
        return load_datasets_ddm(variables, key, resultMap)
    print("load_datasets is only available for DDM, please update your config.py")
    exit(1)


def load_dataset(variables: dict, resultMap: dict, key: str):
    if DATASET_MANAGEMENT == "LOCAL":
        return load_dataset_local(variables, key)
    if DATASET_MANAGEMENT == "DDM":
        return load_datasets_ddm(variables, key, resultMap)[0]
    print("Cannot load dataset, please setup DATASET_MANAGEMENT in config.py")
    exit(1)


########## LOCAL DATASET MANAGEMENT #############


def save_dataset_local(variables: dict, resultMap: dict, key: str, value: BytesIO):
    value_size = sys.getsizeof(value)
    print(f"Saving output data of size {value_size} with key {key}")

    workflow_id = variables.get("exp_engine_metadata").get("wf_id")
    task_id = variables.get("task_name")
    task_outputs = variables.get("mapping", {}).get(task_id, {}).get("outputs", {})
    output_file_path = ""

    # Check if key is in outputs
    if key not in task_outputs:
        raise Exception(f"Output key '{key}' not defined in task outputs mapping.")
    
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
        print(f"Saved output data to s3://workflow-outputs/{workflow_id}/{key}")


    if resultMap is not None:
        print(f"Adding file {output_file_path} path for file {key} to job results")
        resultMap[key] = output_file_path


def load_dataset_local(variables: dict, key: str):
    print(f"Loading input data with key {key}")

    workflow_id = variables.get("exp_engine_metadata").get("wf_id")
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

                print(f"Intermediate file located at: {input_filename}")
                print(f"  User can open and read this file directly")

                # Return open file object for consistency
                return open(input_filename, 'rb')

    raise Exception(f"Could not resolve input '{key}' for task '{current_task_name}'")


########## DDM DATASET MANAGEMENT #############


def load_datasets_ddm(variables: dict, key: str, resultMap: dict) -> List[BytesIO]:
    execution_engine_mapping = variables.get("mapping", {})
    exp_engine_metadata = variables.get("exp_engine_metadata", {})
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
            # This mirrors the save_datasets_ddm pattern
            project_id = os.path.join(project_id_prefix, OUTPUT_FILE, source_task_name) if source_task_name else os.path.join(project_id_prefix, INPUT_FILE, current_task_name)
    else:
        raise Exception(f"Input key '{key}' not found in task inputs.")
    
    results = _look_up_file_in_catalog(fname, project_id)

    contents = []
    result_key = f"file:{current_task_name}:{INPUT_FILE}:{key}"
    result_value = []
    for entry in results:
        file_id = entry.get("id")
        file_url = file_url_template.format(file_id)
        print("Downloading:", file_url)
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
    upload_url = f"{DDM_URL}/ddm/files/upload"
    file_url_template = f"{DDM_URL}/ddm/file/{{}}"
    execution_engine_mapping = variables.get("mapping", {})
    current_task_name = variables.get("task_name")
    exp_engine_metadata = variables.get("exp_engine_metadata", {})
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
        raise Exception(f"Output key '{key}' not found in task outputs.")
    
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

        except Exception as e:
            print(f"Error processing:", str(e))

        form_data = {
            "project_id": project_id,
            "descriptions": "Generated by the exp engine",
        }
        all_files = upload_files + metadata_files

        print("Uploading to:", upload_url)
        response = requests.post(
            upload_url, headers=AUTH_HEADERS, files=all_files, data=form_data
        )
        print("Status:", response.status_code)

        #Check if response is empty
        if not response.content:
            raise Exception("Empty response from DDM upload API")

        generated_file_id = response.json()["files"][0]["id"]
        file_url = file_url_template.format(generated_file_id)
        file_metadata = _return_file_metadata(
            output_file_name, file_url, project_id, file_type
        )
        result_value.append(file_metadata)

        try:
            print("Response:", response.json())
        except Exception:
            print("Raw response:", response.text)
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

    Example usage in task:
        file_obj = load_dataset(variables, resultMap, "my_input")
        data = file_obj.read()  # Read all bytes
        # OR
        chunk = file_obj.read(1024*1024)  # Read 1MB chunk
        # OR
        import pickle
        obj = pickle.load(file_obj)  # Works directly!
    """
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

        print(f"File handle opened for {s3_path}")

        return file_obj

    except Exception as e:
        raise Exception(f"Error opening file from MinIO: {e}")


def load_pickled_dataset_by_path(file_path: str):
    with open(file_path, "rb") as f:
        file_contents = pickle.load(f)
    return file_contents


def _return_file_metadata(
    file_name: str, file_url: str, project_id: str, file_type: str
):
    file_metadata = {
        "file_name": file_name,
        "file_url": file_url,
        "project_id": project_id,
        "file_type": file_type,
    }
    return file_metadata


def _look_up_file_in_catalog(fname: str, project_id: str):
    print(f"Looking up {fname} in project {project_id}")
    catalog_url = f"{DDM_URL}/ddm/catalog/list"
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
    results = r.json().get("data", [])
    if not results:
        raise Exception(f"No files with name {fname}.")
    results = [r for r in results if r["project_id"] == project_id]
    if len(results) == 0:
        raise Exception(f"No files with name {fname} found in project {project_id}.")
    return results