import os
import logging
import time
from ..data_abstraction_layer.data_abstraction_api import DataAbstractionClient
from .kubeflow_utils import (
    _fetch_result_map_from_last_exit_handler,
    _get_requirements_from_file,
    _get_task_dependencies,
    _create_execution_engine_mapping,
    _create_exp_engine_metadata,
    _create_dataset_config,
    _pass_environment_variables_to_task
)

logger = logging.getLogger(__name__)

# Global variables
CONFIG = None
RUNNER_FOLDER = None
EXECUTION_ENGINE_RUNTIME_CONFIG = None
KFP_CLIENT = None
DATA_CLIENT = None

# Constants
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
RESULTS_FILE = "experiment_results.json"

try:
    import kfp
    from kfp.v2.dsl import component, pipeline
    from kfp import kubernetes
    KFP_AVAILABLE = True
except ImportError:
    logger.warning(
        "Kubeflow Pipelines SDK not found. Please install with: pip install kfp kfp-kubernetes"
    )
    KFP_AVAILABLE = False


def create_kfp_client():
    """Create and return Kubeflow Pipelines client"""

    logger.info("Creating Kubeflow Pipelines client...")

    # Use configuration to connect to KFP
    if hasattr(CONFIG, "KUBEFLOW_URL"):
        endpoint = CONFIG.KUBEFLOW_URL
    else:
        endpoint = "http://localhost:8080"  # Default for development

    try:
        client = kfp.Client(host=endpoint)
        logger.info(f"Connected to Kubeflow Pipelines at: {endpoint}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Kubeflow Pipelines: {e}")
        raise


def _create_kubeflow_component(task):
    """Create a Kubeflow component from a task"""
    logger.info(f"Creating Kubeflow component for task {task.name}...")
    # Base image for the component
    if task.python_version:
        base_image = f"python:{task.python_version}"
    else:
        base_image = "python:3.9"  # Use 3.9 which is compatible with KFP 2.x

    # Gather requirements
    requirements = []
    if task.requirements_file:
        requirements.extend(_get_requirements_from_file(task.requirements_file))
    else:
        logger.info(
            "No requirements file specified for this task. Continuing without additional requirements."
        )

    # Create the component function
    @component(
        base_image=base_image, packages_to_install=["eexp_engine_utils"] + requirements,
    )
    def task_component(
        task_name: str,
        variables: dict,
        resultMap: dict,
        task_code: str,
        dependency_files: dict,
        results_so_far: dict = {},
    ) -> dict:
        """Kubeflow component that wraps the original task implementation"""
        import sys
        import os

        # ===========================
        # Dependency handling
        # ===========================
        print("Handling dependencies...")

        # Create workspace directory
        work_dir = "/tmp/task_workspace"
        os.makedirs(work_dir, exist_ok=True)
        
        # Recreate directory structure and write all files
        for file_path, file_content in dependency_files.items():
            full_path = os.path.join(work_dir, file_path)

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            # Write the file
            with open(full_path, "w") as f:
                f.write(file_content)

        # Create __init__.py files for subdirectories to make them Python packages
        for file_path in dependency_files.keys():
            dir_path = os.path.dirname(file_path)
            while dir_path and dir_path != ".":
                init_file = os.path.join(work_dir, dir_path, "__init__.py")
                if not os.path.exists(init_file):
                    with open(init_file, "w") as f:
                        f.write("# Auto-generated __init__.py\n")
                dir_path = os.path.dirname(dir_path)

        # Add workspace to Python path
        sys.path.insert(0, work_dir)

        # Make variables available in execution context
        exec_globals = {
            "__name__": "__main__",
            "variables": variables,
            "resultMap": resultMap,
            "results_so_far": results_so_far,
            "task_name": task_name,
        }

        # Execute the task code
        print(f"Executing task code for {task_name}...")
        exec(task_code, exec_globals)

        # Return the mutated variables and resultMap as a dict
        return resultMap

    return task_component


def _create_exit_handler_component():
    """Create an exit handler component to collect and persist final workflow output"""

    @component(
        base_image="python:3.9",
        packages_to_install=["minio", "requests"]
    )
    def exit_handler(
        final_resultMap: dict,
        workflow_id: str,
    ):
        """Exit handler that saves final workflow output to MinIO"""
        import json
        import os
        from minio import Minio
        from io import BytesIO

        # Get MinIO configuration from environment
        minio_endpoint = "minio-service.kubeflow:9000"
        minio_access_key = os.environ.get("KUBEFLOW_MINIO_USERNAME")
        minio_secret_key = os.environ.get("KUBEFLOW_MINIO_PASSWORD")

        if not all([minio_endpoint, minio_access_key, minio_secret_key]):
            raise ValueError(
                "MinIO credentials not found in environment. "
                "Required: MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY"
            )

        try:
            # Initialize MinIO client
            client = Minio(
                minio_endpoint,
                access_key=minio_access_key,
                secret_key=minio_secret_key,
                secure=False  # Set to True if using HTTPS
            )

            # Define storage location
            bucket_name = "workflow-outputs"
            object_name = f"{workflow_id}/final_output.json"

            # Create bucket if it doesn't exist
            if not client.bucket_exists(bucket_name):
                client.make_bucket(bucket_name)
                print(f"Created bucket: {bucket_name}")

            # Upload the resultMap as JSON
            result_bytes = json.dumps(final_resultMap, default=str).encode('utf-8')
            client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(result_bytes),
                length=len(result_bytes),
                content_type='application/json'
            )

            print(f"Final output saved to: s3://{bucket_name}/{object_name}")

        except Exception as e:
            raise RuntimeError(f"ERROR saving to MinIO: {e}")

    return exit_handler


def _convert_workflow_to_pipeline(workflow, exp_engine_runtime_config, secrets: dict, results_so_far):
    """Convert a workflow to a Kubeflow pipeline"""
    logger.info(f"Converting workflow {workflow.name} to Kubeflow pipeline...")

    # Create components for each task and store task codes
    task_components = {}
    task_codes = {}
    task_dependencies = {}
    sorted_tasks = sorted(workflow.tasks, key=lambda t: t.order)
    exp_engine_runtime_config = _create_execution_engine_mapping(sorted_tasks, exp_engine_runtime_config, secrets)
    for task in sorted_tasks:

        # Store task code
        with open(task.impl_file, "r") as f:
            task_codes[task.name] = f.read()

        # Get file dependencies as dictionary
        task_dependencies[task.name] = _get_task_dependencies(task)

        # Create the component function
        component_func = _create_kubeflow_component(task)
        task_components[task.name] = component_func

    # Create the exit handler component
    exit_handler_func = _create_exit_handler_component()

    @pipeline(
        name=workflow.name.lower().replace(" ", "-"),
        description=f"Generated pipeline for workflow {workflow.name}",
    )
    def workflow_pipeline():
        """The main pipeline function with exit handler"""
        # Get workflow ID for exit handler
        wf_id = exp_engine_runtime_config["exp_engine_metadata"]["wf_id"]

        task_outputs = {}
        variables = exp_engine_runtime_config
        resultMap = {}

        # Create a dynamic PVC for this workflow
        # Using pvc_name_suffix to create a unique PVC per workflow run
        pvc_name_suffix = f"-{workflow.name.lower().replace(' ', '-')}-pvc"

        create_shared = kubernetes.CreatePVC(
            pvc_name_suffix=pvc_name_suffix,
            access_modes=["ReadWriteOnce"],
            size="5Gi",
            storage_class_name="standard",
        )

        for task in sorted_tasks:
            print(f"Adding task {task.name} to pipeline...")

            # Get the component function
            component_func = task_components[task.name]

            # Create task-specific variables
            task_variables = dict(variables)
            task_variables.update(dict(task.params) if hasattr(task, "params") else {})
            task_variables.update({"task_name": task.name})

            # Determine resultMap input: use previous task's output if it has dependencies
            if task.dependencies and len(task.dependencies) > 0:
                dep_task_name = task.dependencies[0]
                if dep_task_name in task_outputs:
                    # Pass the previous task's output directly (KFP will resolve at runtime)
                    task_resultMap_input = task_outputs[dep_task_name].output
                else:
                    task_resultMap_input = resultMap
            else:
                # First task - use initial resultMap
                task_resultMap_input = resultMap

            # Create the task in the pipeline
            task_op = component_func(
                task_name=task.name,
                variables=task_variables,
                resultMap=task_resultMap_input,
                task_code=task_codes[task.name],
                dependency_files=task_dependencies[task.name],
                results_so_far=results_so_far if results_so_far else {},
            )
            # Set task name
            task_op.set_display_name(task.name)

            # Pass environment variables to the task
            task_op = _pass_environment_variables_to_task(task_op, secrets)

            # Mount at /shared so tasks can exchange data via the volume
            kubernetes.mount_pvc(
                task_op,
                pvc_name=create_shared.outputs["name"],
                mount_path="/shared",
            )

            # Add dependencies
            for dep_name in task.dependencies:
                if dep_name in task_outputs:
                    task_op.after(task_outputs[dep_name])

            # Store task output for dependencies
            task_outputs[task.name] = task_op

        # Get the last task from sorted list
        last_task = sorted_tasks[-1]

        # Create exit handler task that receives the final output
        exit_task = exit_handler_func(
            final_resultMap=task_outputs[last_task.name].output,
            workflow_id=wf_id
        )
        exit_task.set_display_name("save-final-output")
        exit_task = _pass_environment_variables_to_task(exit_task, secrets)
        exit_task.after(task_outputs[last_task.name])

        # Delete the PVC after the exit handler completes
        delete_shared = kubernetes.DeletePVC(pvc_name=create_shared.outputs["name"])
        delete_shared.after(exit_task)

    return workflow_pipeline


def _submit_pipeline_and_monitor(exp_id, wf_id, client, pipeline_func, task_statuses):
    """Submit pipeline and monitor execution"""
    logger.info("Compiling and submitting pipeline...")

    # Submit pipeline run
    experiment_name = exp_id
    run_name = wf_id

    try:
        # Create experiment if it doesn't exist
        try:
            experiment = client.create_experiment(experiment_name)
        except Exception:
            experiment = client.get_experiment(experiment_name=experiment_name)

        # Submit the run
        run = client.create_run_from_pipeline_func(
            pipeline_func=pipeline_func,
            arguments={},
            run_name=run_name,
            experiment_name=experiment_name,
        )

        run_id = run.run_id
        logger.info(f"Pipeline run submitted with ID: {run_id}")

        # Update workflow metadata
        DATA_CLIENT.update_workflow(wf_id, {"metadata": {"kubeflow_run_id": run_id}})

        # Monitor the run
        _monitor_pipeline_run(wf_id, client, run_id, task_statuses)

        # Get final results
        run_details = client.get_run(run_id)

        return run_id, run_details

    except Exception as e:
        logger.error(f"Failed to submit or monitor pipeline: {e}")
        raise

def _update_workflow_task_statuses(wf_id, task_statuses):
    """Update workflow task statuses in the data abstraction layer"""
    wf = DATA_CLIENT.get_workflow(wf_id)
    if not wf:
        return
    new_tasks = []
    for task in wf.get("tasks", []):
        task_name = task["name"]
        status_update = next((ts for ts in task_statuses if ts["name"] == task_name), {})
        if status_update.get("start") is not None:
            task["start"] = status_update.get("start")
        if status_update.get("end") is not None:
            task["end"] = status_update.get("end")
        new_tasks.append(task)
    DATA_CLIENT.update_workflow(wf_id, {"tasks": new_tasks})


def _monitor_pipeline_run(wf_id, client, run_id, task_statuses):
    """Monitor pipeline run and update task statuses"""
    import copy

    logger.info(f"Monitoring pipeline run {run_id}...")
    default_timestamp = "0001-01-01T00:00:00+00:00"
    is_finished = False
    current_task_statuses = copy.deepcopy(task_statuses)
    while not is_finished:
        try:
            run_info = client.get_run(run_id)
            run_state = run_info.state
            if hasattr(run_info.run_details, "task_details") and run_info.run_details.task_details:
                task_details = run_info.run_details.task_details
                task_metadata = [x for x in task_details if str(x.display_name).startswith("task-component") and not str(x.display_name).endswith("driver")]
                for index in range(1, len(task_statuses) + 1):
                    if index == 1:
                        task_statuses[index - 1].update({
                            "start": next((x.start_time.isoformat() if x.start_time.isoformat() != default_timestamp else None 
                                           for x in task_metadata if str(index) not in x.display_name), None),
                            "end": next((x.end_time.isoformat() if x.end_time.isoformat() != default_timestamp else None 
                                         for x in task_metadata if str(index) not in x.display_name), None),
                        })
                    else:
                        task_statuses[index - 1].update({
                            "start": next((x.start_time.isoformat() if x.start_time.isoformat() != default_timestamp else None 
                                           for x in task_metadata if str(index) in x.display_name), None),
                            "end": next((x.end_time.isoformat() if x.end_time.isoformat() != default_timestamp else None 
                                         for x in task_metadata if str(index) in x.display_name), None),
                        })
            if current_task_statuses != task_statuses:
                _update_workflow_task_statuses(wf_id, task_statuses)
                current_task_statuses = copy.deepcopy(task_statuses)
            logger.info(f"Current run state: {run_state}")
            # Update workflow status
            if run_state in [
                "SUCCEEDED",
                "FAILED",
                "CANCELLED",
                "SKIPPED",
                "COMPLETED",
            ]:
                DATA_CLIENT.update_workflow(wf_id, {"status": "COMPLETED" if run_state == "SUCCEEDED" else run_state})
                is_finished = True

            time.sleep(5)  # Poll every 5 seconds

        except Exception as e:
            logger.error(f"Error monitoring pipeline: {e}")
            time.sleep(10)


def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config, results_so_far):
    """
    Main execution function for Kubeflow

    Args:
        w = Workflow object to execute
        exp_id = Experiment ID
        exp_name = Experiment name
        wf_id = Workflow ID
        runner_folder = Runner folder path
        config = Configuration object
        results_so_far = Previous results

    Returns:
        Experiment result map
    """
    global RUNNER_FOLDER, CONFIG, EXECUTION_ENGINE_RUNTIME_CONFIG, KFP_CLIENT, DATA_CLIENT
    if not KFP_AVAILABLE:
        raise ImportError(
            "Kubeflow Pipelines SDK is required. Install with: pip install kfp"
        )

    # Set global variables
    RUNNER_FOLDER = runner_folder
    EXECUTION_ENGINE_RUNTIME_CONFIG = (
        f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
    )
    DATA_CLIENT = DataAbstractionClient(config)
    CONFIG = config

    logger.info("****************************")
    logger.info(f"Executing workflow {w.name} using Kubeflow Pipelines")
    logger.info("****************************")
    w.print()
    logger.info("****************************")

    # Create KFP client
    KFP_CLIENT = create_kfp_client()

    # Prepare execution data
    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)
    secrets = _create_dataset_config(CONFIG)

    exp_engine_runtime_config = {
        "exp_engine_metadata": exp_engine_metadata,
    }

    # Create task status tracking
    task_statuses = [{"name": task.name, "start": None, "end": None} for task in w.tasks]

    # Convert workflow to pipeline
    pipeline_func = _convert_workflow_to_pipeline(
        w, exp_engine_runtime_config, secrets, results_so_far,
    )
    logger.info("Pipeline function created successfully.")
    logger.info("****************************")

    # # Submit and monitor pipeline
    try:
        run_id, run_details = _submit_pipeline_and_monitor(
            exp_id, wf_id, KFP_CLIENT, pipeline_func, task_statuses
        )

        # Get final status
        final_status = run_details.state
        experiment_result_map = {}

        # Retrieve final workflow output from MinIO if workflow succeeded
        if final_status in ["SUCCEEDED", "COMPLETED"]:
            logger.info("Retrieving final workflow output from MinIO...")
            experiment_result_map = _fetch_result_map_from_last_exit_handler(wf_id, CONFIG, logger)

        logger.info("****************************")
        logger.info(f"Finished executing workflow {w.name}")
        logger.info(f"Kubeflow Run ID: {run_id}")
        logger.info(f"Final Status: {final_status}")
        logger.info(f"Experiment Result Map: {experiment_result_map}")
        logger.info("****************************")

        return experiment_result_map

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        DATA_CLIENT.update_workflow(wf_id, {"status": "FAILED"})
        raise

    finally:
        # Cleanup
        if os.path.exists(EXECUTION_ENGINE_RUNTIME_CONFIG):
            os.remove(EXECUTION_ENGINE_RUNTIME_CONFIG)
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
