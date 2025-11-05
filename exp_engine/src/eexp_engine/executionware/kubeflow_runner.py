import os
import json
import logging
import time
from ..data_abstraction_layer.data_abstraction_api import DataAbstractionClient

logger = logging.getLogger(__name__)

# Global variables - similar to proactive_runner
CONFIG = None
RUNNER_FOLDER = None
EXECUTION_ENGINE_RUNTIME_CONFIG = None
KFP_CLIENT = None
DATA_CLIENT = None

# Constants
packagedir = os.path.dirname(os.path.abspath(__file__))
KUBEFLOW_HELPER_FULL_PATH = os.path.join(packagedir, "kubeflow_helper.py")
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
RESULTS_FILE = "experiment_results.json"

try:
    import kfp
    from kfp.v2.dsl import component, pipeline
    from kfp import kubernetes
    KFP_AVAILABLE = True
except ImportError:
    logger.warning("Kubeflow Pipelines SDK not found. Please install with: pip install kfp")
    KFP_AVAILABLE = False


def create_kfp_client():
    """Create and return Kubeflow Pipelines client""" 
    
    print("Creating Kubeflow Pipelines client...")
    
    # Use configuration to connect to KFP
    if hasattr(CONFIG, 'KUBEFLOW_PIPELINES_ENDPOINT'):
        endpoint = CONFIG.KUBEFLOW_PIPELINES_ENDPOINT
    else:
        endpoint = 'http://localhost:8080'  # Default for development
    
    try:
        client = kfp.Client(host=endpoint)
        print(f"Connected to Kubeflow Pipelines at: {endpoint}")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Kubeflow Pipelines: {e}")
        raise


def _create_execution_engine_mapping(tasks):
    """Create mapping for execution engine"""
    mapping = {}
    output_to_task = {}
    
    for t in tasks:
        for ds in t.output_files:
            output_to_task[ds.name_in_task_signature] = t.name
    
    for t in tasks:
        map = {}
        mapping[t.name] = map
        for ds in t.input_files:
            if ds.name_in_generating_task:
                # Store both the output name AND the source task
                map[ds.name_in_task_signature] = {
                    "file_name": ds.name_in_generating_task,
                    "source_task": output_to_task.get(ds.name_in_generating_task)
                }
    print("EXECUTION ENGINE MAPPING")
    print("*****************")
    import pprint
    pprint.pp(mapping)
    print("*****************")
    return mapping


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
    dataset_config["DATASET_MANAGEMENT"] = getattr(config, 'DATASET_MANAGEMENT', None)
    dataset_config["DDM_URL"] = getattr(config, 'DDM_URL', None)
    dataset_config["DDM_TOKEN"] = getattr(config, 'DDM_TOKEN', None)
    dataset_config["DATA_ABSTRACTION_BASE_URL"] = getattr(config, 'DATA_ABSTRACTION_BASE_URL', None)
    dataset_config["DATA_ABSTRACTION_ACCESS_TOKEN"] = getattr(config, 'DATA_ABSTRACTION_ACCESS_TOKEN', None)
    return dataset_config


def _get_requirements_from_file(reqs_file):
    """Get requirements from file"""
    if not os.path.exists(reqs_file):
        logger.info(f"Requirements file {reqs_file} does not exist. No requirements to install.")
        return []
    with open(reqs_file) as file:
        user_reqs = [line.rstrip() for line in file]
    return user_reqs

def _get_task_dependencies(task):
    """Get task dependencies from the task object as a dictionary with relative paths and file contents"""
    dependencies = {}

    # Always include kubeflow_helper.py (similar to proactive_helper.py in ProActive)
    if os.path.exists(KUBEFLOW_HELPER_FULL_PATH):
        try:
            with open(KUBEFLOW_HELPER_FULL_PATH, 'r', encoding='utf-8') as f:
                dependencies['kubeflow_helper.py'] = f.read()
        except Exception as e:
            logger.warning(f"Could not read kubeflow_helper.py: {e}")

    if not hasattr(task, 'dependent_modules'):
        return dependencies
    
    for dep in task.dependent_modules:
        if dep.endswith('**'):
            # Include all possible directories of the path recursively
            base_path = dep[:-2]  # Remove the '**' suffix
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith('.py'):
                            file_path = os.path.join(root, file)
                            # Get relative path from base_path
                            rel_path = os.path.relpath(file_path, base_path)
                            
                            # Read file content
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
                                    file_content = f.read()
                                dependencies[rel_path] = file_content
                            except Exception as e:
                                logger.warning(f"Could not read file {file_path}: {e}")
                                
        elif dep.endswith('*'):
            # Include files in the directory (non-recursive)
            base_path = dep[:-1]  # Remove the '*' suffix
            if os.path.exists(base_path):
                for file in os.listdir(base_path):
                    if file.endswith('.py'):
                        file_path = os.path.join(base_path, file)
                        if os.path.isfile(file_path):
                            # For single directory, just use filename as key
                            rel_path = file
                            
                            # Read file content
                            try:
                                with open(file_path, 'r', encoding='utf-8') as f:
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
                    with open(dep, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    dependencies[rel_path] = file_content
                except Exception as e:
                    logger.warning(f"Could not read file {dep}: {e}")
    
    return dependencies


def _create_kubeflow_component(task):
    """Create a Kubeflow component from a task"""
    print(f"Creating Kubeflow component for task {task.name}...")
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
        print("No requirements file specified for this task. Continuing without additional requirements.")

    # Create the component function
    @component(
        base_image=base_image,
        packages_to_install=requirements
    )
    def task_component(
        task_name: str,
        variables: dict,
        resultMap: dict,
        task_code: str,
        dependency_files: dict,
        results_so_far: dict = {}
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
            with open(full_path, 'w') as f:
                f.write(file_content)
        
        # Create __init__.py files for subdirectories to make them Python packages
        for file_path in dependency_files.keys():
            dir_path = os.path.dirname(file_path)
            while dir_path and dir_path != '.':
                init_file = os.path.join(work_dir, dir_path, '__init__.py')
                if not os.path.exists(init_file):
                    with open(init_file, 'w') as f:
                        f.write('# Auto-generated __init__.py\n')
                dir_path = os.path.dirname(dir_path)
        
        # Add workspace to Python path
        sys.path.insert(0, work_dir)
        
        # Make variables available in execution context
        exec_globals = {
            '__name__': '__main__',
            'variables': variables,
            'resultMap': resultMap,
            'results_so_far': results_so_far,
            'task_name': task_name
        }
        
        # Execute the task code
        print(f"Executing task code for {task_name}...")
        exec(task_code, exec_globals)

        # Return the mutated variables and resultMap as a dict
        return resultMap
    
    return task_component


def _convert_workflow_to_pipeline(workflow, exp_engine_runtime_config, results_so_far):
    """Convert a workflow to a Kubeflow pipeline"""
    print(f"Converting workflow {workflow.name} to Kubeflow pipeline...")
    
    # Create components for each task and store task codes
    task_components = {}
    task_codes = {}
    task_dependencies = {}
    sorted_tasks = sorted(workflow.tasks, key=lambda t: t.order)
    
    for task in sorted_tasks:
        component_func = _create_kubeflow_component(task)
        task_components[task.name] = component_func
        
        # Store task code for later use
        with open(task.impl_file, 'r') as f:
            task_codes[task.name] = f.read()

        # Get dependencies as dictionary
        task_dependencies[task.name] = _get_task_dependencies(task)
    
    @pipeline(
        name=workflow.name.lower().replace(' ', '-'),
        description=f"Generated pipeline for workflow {workflow.name}"
    )
    def workflow_pipeline():
        """The main pipeline function"""
        task_outputs = {}
        variables = exp_engine_runtime_config
        resultMap = {}

        # Create a dynamic PVC for this workflow
        # Using pvc_name_suffix to create a unique PVC per workflow run
        pvc_name_suffix = f"-{workflow.name.lower().replace(' ', '-')}-pvc"

        create_shared = kubernetes.CreatePVC(
            pvc_name_suffix=pvc_name_suffix,
            access_modes=['ReadWriteOnce'],
            size='5Gi',
            storage_class_name='standard',
        )

        for task in sorted_tasks:
            print(f"Adding task {task.name} to pipeline...")
            print(f"Task {task.name} dependencies: {task.dependencies}")

            # Get the component function
            component_func = task_components[task.name]

            # Create task-specific variables
            task_variables = dict(variables)
            task_variables.update(dict(task.params) if hasattr(task, 'params') else {})
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
                results_so_far=results_so_far if results_so_far else {}
            )

            # Set task name
            task_op.set_display_name(task.name)

            # Mount at /shared so tasks can exchange data via the volume
            kubernetes.mount_pvc(
                task_op,
                pvc_name=create_shared.outputs['name'],
                mount_path='/shared',
            )

            # Add dependencies
            for dep_name in task.dependencies:
                if dep_name in task_outputs:
                    task_op.after(task_outputs[dep_name])

            # Store task output for dependencies
            task_outputs[task.name] = task_op

        # Get the last task from sorted list
        last_task = sorted_tasks[-1]

        # Delete the PVC after the last task completes
        delete_shared = kubernetes.DeletePVC(pvc_name=create_shared.outputs['name'])
        delete_shared.after(task_outputs[last_task.name])

    return workflow_pipeline


def _submit_pipeline_and_monitor(exp_id, wf_id, client, pipeline_func, task_statuses):
    """Submit pipeline and monitor execution"""
    print("Compiling and submitting pipeline...")
    
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
            experiment_name=experiment_name
        )
        
        run_id = run.run_id
        print(f"Pipeline run submitted with ID: {run_id}")
        
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


def _monitor_pipeline_run(wf_id, client, run_id, task_statuses):
    """Monitor pipeline run and update task statuses"""
    print(f"Monitoring pipeline run {run_id}...")
    
    is_finished = False
    while not is_finished:
        try:
            run_details = client.get_run(run_id)
            
            # Handle different KFP API versions
            if hasattr(run_details, 'run'):
                run_status = run_details.run.status
            elif hasattr(run_details, 'status'):
                run_status = run_details.status
            elif hasattr(run_details, 'state'):
                run_status = run_details.state
            else:
                # Fallback - check attributes
                print(f"Run details type: {type(run_details)}")
                print(f"Run details attributes: {dir(run_details)}")
                run_status = "UNKNOWN"
            
            print(f"Pipeline status: {run_status}")
            
            # Update workflow status
            if run_status in ["SUCCEEDED", "FAILED", "CANCELLED", "SKIPPED", "COMPLETED"]:
                DATA_CLIENT.update_workflow(wf_id, {"status": run_status})
                is_finished = True
            
            time.sleep(5)  # Poll every 5 seconds
            
        except Exception as e:
            logger.error(f"Error monitoring pipeline: {e}")
            time.sleep(10)


def execute_wf(w, exp_id, exp_name, wf_id, runner_folder, config, results_so_far):
    """
    Main execution function for Kubeflow
    
    Args:
        w: Workflow object to execute
        exp_id: Experiment ID
        exp_name: Experiment name
        wf_id: Workflow ID
        runner_folder: Runner folder path
        config: Configuration object
        results_so_far: Previous results
    
    Returns:
        Dictionary with execution results
    """
    global RUNNER_FOLDER, CONFIG, EXECUTION_ENGINE_RUNTIME_CONFIG, KFP_CLIENT, DATA_CLIENT
    if not KFP_AVAILABLE:
        raise ImportError("Kubeflow Pipelines SDK is required. Install with: pip install kfp")
    
    # Set global variables
    RUNNER_FOLDER = runner_folder
    EXECUTION_ENGINE_RUNTIME_CONFIG = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
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
    mapping = _create_execution_engine_mapping(w.tasks)
    exp_engine_metadata = _create_exp_engine_metadata(exp_id, exp_name, wf_id)
    dataset_config = _create_dataset_config(CONFIG)

    exp_engine_runtime_config = {
        "mapping": mapping,
        "exp_engine_metadata": exp_engine_metadata,
        "dataset_config": dataset_config
    }
    
    # Create task status tracking
    task_statuses = [{"name": task.name, "status": "Pending"} for task in w.tasks]
    
    # Convert workflow to pipeline
    pipeline_func = _convert_workflow_to_pipeline(w, exp_engine_runtime_config, results_so_far)

    print("Pipeline function created successfully.")
    print("****************************")
    
    # Submit and monitor pipeline
    try:
        run_id, run_details = _submit_pipeline_and_monitor(exp_id, wf_id, KFP_CLIENT, pipeline_func, task_statuses)

        # Extract results (handle different KFP API versions)
        if hasattr(run_details, 'run'):
            final_status = run_details.run.status
        elif hasattr(run_details, 'status'):
            final_status = run_details.status
        elif hasattr(run_details, 'state'):
            final_status = run_details.state
        else:
            final_status = "COMPLETED"
        
        result_map = {"run_id": run_id, "status": final_status}
        
        print("****************************")
        print(f"Finished executing workflow {w.name}")
        print(f"Kubeflow Run ID: {run_id}")
        print(f"Final Status: {final_status}")
        print("****************************")
        
        return result_map
        
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
