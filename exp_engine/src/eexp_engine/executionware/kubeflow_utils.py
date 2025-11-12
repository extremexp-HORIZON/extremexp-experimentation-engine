import logging
import os

logger = logging.getLogger(__name__)
packagedir = os.path.dirname(os.path.abspath(__file__))
KUBEFLOW_HELPER_FULL_PATH = os.path.join(packagedir, "kubeflow_helper.py")


def _upload_with_minio_client(
    local_file_path: str,
    workflow_name: str,
    minio_endpoint: str = "localhost:9000",
    minio_access_key: str = "minio",
    minio_secret_key: str = "minio123",
) -> list[str]:
    """
    Upload multiple local files to MinIO and return array of uploaded file paths (S3 URIs).
    """
    from minio import Minio
    from minio.error import S3Error
    import os

    uploaded_path = ""

    try:
        # Create MinIO client
        client = Minio(
            minio_endpoint,
            access_key=minio_access_key,
            secret_key=minio_secret_key,
            secure=False,  # Set to True if using HTTPS
        )
        print(f"Connected to MinIO at {minio_endpoint}")
        bucket_name = "workflow-input-files"
        # Create bucket if it doesn't exist
        try:
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"Created bucket '{bucket_name}'")
            else:
                print(f"Bucket '{bucket_name}' already exists")
        except S3Error as e:
            logger.error(f"Error checking/creating bucket '{bucket_name}': {e}")
            raise

        # Upload file
        if local_file_path:
            try:
                # Validate file exists
                if not os.path.exists(local_file_path):
                    raise FileNotFoundError(f"Local file not found: {local_file_path}")

                # Use the filename as the object name (you can customize this)
                object_name = os.path.basename(local_file_path)

                # Upload file to MinIO
                save_path = (
                    workflow_name.lower().replace(" ", "-").replace("_", "-")
                    + "/"
                    + object_name
                )
                client.fput_object(bucket_name, save_path, local_file_path)
                print(f"✓ Successfully uploaded {local_file_path} to s3://{bucket_name}/{save_path}")
                # Construct S3 path
                return f"s3://{bucket_name}/{save_path}"

            except FileNotFoundError as e:
                logger.error(f"File error: {e}")
                raise
            except S3Error as e:
                logger.error(f"MinIO error uploading {local_file_path}: {e}")
                raise
            except Exception as e:
                logger.error(f"Unexpected error uploading {local_file_path}: {e}")
                raise

        print(f"Successfully uploaded {uploaded_path} to MinIO")
        return uploaded_path

    except Exception as e:
        logger.error(f"Failed to upload files to MinIO: {e}")
        raise


def _pass_environment_variables_to_task(task_op, secrets: dict):
    """Pass necessary environment variables to the task operation"""
    # for each secret in secrets, add as environment variable
    for secret_name, secret_value in secrets.items():
        if secret_value is not None:
            task_op.set_env_variable(name=secret_name.upper(), value=str(secret_value))
    return task_op


def _create_execution_engine_mapping(tasks, exp_engine_runtime_config):
    """Create mapping for execution engine"""
    mapping = {}

    # Mapping of output variable names to their generating tasks
    output_to_task = {}
    for t in tasks:
        for ds in t.output_files:
            # Map the output variable name to the task that generates it
            output_to_task[ds.name_in_task_signature] = t.name
            

    # Build the full mapping with source task information
    for t in tasks:
        # Initialize the task entry in the mapping
        if t.name not in mapping:
            mapping[t.name] = {"inputs": {}, "outputs": {}}


        ##### INPUTS #####
        for ds in t.input_files:
            # LOCAL FILE case
            if ds.path and (not ds.filename and not ds.project):
                uploaded_path = _upload_with_minio_client(
                    ds.path,
                    workflow_name=exp_engine_runtime_config.get(
                        "exp_engine_metadata"
                    ).get("exp_id", "experiment-inputs"),
                )
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": uploaded_path,
                }
            # DDM case
            elif ds.filename and ds.project:
                uploaded_path = f"{ds.project}/{ds.filename if ds.filename else ''}"
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": uploaded_path,
                }
            # INTERMEDIATE FILE case
            else:
                # Find the task that generates this input by looking up the output variable name
                source_task = output_to_task.get(ds.name_in_generating_task)
                mapping[t.name]["inputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name_in_generating_task,
                    "file_type": "intermediate",
                    "source_task": source_task,
                }


        ##### OUTPUTS #####
        for ds in t.output_files:
            # LOCAL FILE case
            if ds.path and (not ds.filename and not ds.project):
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": ds.path,
                }
            # DDM case
            elif ds.filename and ds.project:
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "external",
                    "file_path": f"{ds.project}/{ds.filename if ds.filename else ''}",
                }
            # INTERMEDIATE FILE case
            else:
                mapping[t.name]["outputs"][ds.name_in_task_signature] = {
                    "file_name": ds.name,
                    "file_type": "intermediate",
                }
    exp_engine_runtime_config["mapping"] = mapping
    print("EXECUTION ENGINE MAPPING")
    print("*****************")
    import pprint

    pprint.pp(mapping)
    print("*****************")
    return exp_engine_runtime_config


def _create_exp_engine_metadata(exp_id, exp_name, wf_id):
    """Create experiment engine metadata"""
    exp_engine_metadata = {}
    exp_engine_metadata["exp_id"] = exp_id
    exp_engine_metadata["exp_name"] = exp_name
    exp_engine_metadata["wf_id"] = wf_id
    return exp_engine_metadata


def _create_dataset_config(config):
    """Create experiment engine metadata"""
    dataset_config = {}
    dataset_config["DATASET_MANAGEMENT"] = getattr(config, "DATASET_MANAGEMENT", None)
    dataset_config["DDM_URL"] = getattr(config, "DDM_URL", None)
    dataset_config["DDM_TOKEN"] = getattr(config, "DDM_TOKEN", None)
    dataset_config["DATA_ABSTRACTION_BASE_URL"] = getattr(
        config, "DATA_ABSTRACTION_BASE_URL", None
    )
    dataset_config["DATA_ABSTRACTION_ACCESS_TOKEN"] = getattr(
        config, "DATA_ABSTRACTION_ACCESS_TOKEN", None
    )
    dataset_config["KUBEFLOW_MINIO_USERNAME"] = getattr(
        config, "KUBEFLOW_MINIO_USERNAME", None
    )
    dataset_config["KUBEFLOW_MINIO_PASSWORD"] = getattr(
        config, "KUBEFLOW_MINIO_PASSWORD", None
    )
    return dataset_config


def _get_requirements_from_file(reqs_file):
    """Get requirements from file"""
    if not os.path.exists(reqs_file):
        logger.info(
            f"Requirements file {reqs_file} does not exist. No requirements to install."
        )
        return []
    with open(reqs_file) as file:
        user_reqs = [line.rstrip() for line in file]
    return user_reqs


def _has_local_input_files(task):
    """Check if a task has input files that need to be read from local filesystem"""
    if not hasattr(task, "input_files"):
        return False

    for input_file in task.input_files:
        # Check if this is a local file (not from another task's output)
        if not input_file.name_in_generating_task:
            # This is a local input file - use 'path' instead of 'local_path'
            if input_file.path and not input_file.filename and not input_file.project:
                print(f"  -> Found local input file: {input_file.path}")
                return True

    return False


def _get_local_input_files_paths(task):
    """Get the local input file paths for a task"""
    if not hasattr(task, "input_files"):
        return []

    local_paths = []
    for input_file in task.input_files:
        if input_file.path and not input_file.filename and not input_file.project:
            local_paths.append(input_file.path)

    return local_paths


def _get_task_dependencies(task):
    """Get task dependencies from the task object as a dictionary with relative paths and file contents"""
    dependencies = {}

    # Always include kubeflow_helper.py (similar to proactive_helper.py in ProActive)
    if os.path.exists(KUBEFLOW_HELPER_FULL_PATH):
        try:
            with open(KUBEFLOW_HELPER_FULL_PATH, "r", encoding="utf-8") as f:
                dependencies["kubeflow_helper.py"] = f.read()
        except Exception as e:
            logger.warning(f"Could not read kubeflow_helper.py: {e}")

    if not hasattr(task, "dependent_modules"):
        return dependencies

    for dep in task.dependent_modules:
        if dep.endswith("**"):
            # Include all possible directories of the path recursively
            base_path = dep[:-2]  # Remove the '**' suffix
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith(".py"):
                            file_path = os.path.join(root, file)
                            # Get relative path from base_path
                            rel_path = os.path.relpath(file_path, base_path)

                            # Read file content
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    file_content = f.read()
                                dependencies[rel_path] = file_content
                            except Exception as e:
                                logger.warning(f"Could not read file {file_path}: {e}")

        elif dep.endswith("*"):
            # Include files in the directory (non-recursive)
            base_path = dep[:-1]  # Remove the '*' suffix
            if os.path.exists(base_path):
                for file in os.listdir(base_path):
                    if file.endswith(".py"):
                        file_path = os.path.join(base_path, file)
                        if os.path.isfile(file_path):
                            # For single directory, just use filename as key
                            rel_path = file

                            # Read file content
                            try:
                                with open(file_path, "r", encoding="utf-8") as f:
                                    file_content = f.read()
                                dependencies[rel_path] = file_content
                            except Exception as e:
                                logger.warning(f"Could not read file {file_path}: {e}")
        else:
            # Import the file directly
            if os.path.exists(dep):
                # Use just the filename as key for single files
                rel_path = os.path.basename(dep)

                # Read file content
                try:
                    with open(dep, "r", encoding="utf-8") as f:
                        file_content = f.read()
                    dependencies[rel_path] = file_content
                except Exception as e:
                    logger.warning(f"Could not read file {dep}: {e}")

    return dependencies
