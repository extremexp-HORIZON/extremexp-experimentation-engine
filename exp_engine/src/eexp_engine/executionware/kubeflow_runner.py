import os
import json
import logging
import time
from ..data_abstraction_layer.data_abstraction_api import (update_workflow, set_data_abstraction_config)

logger = logging.getLogger(__name__)

# Global variables - similar to proactive_runner
CONFIG = None
RUNNER_FOLDER = None
EXECUTION_ENGINE_RUNTIME_CONFIG = None
KFP_CLIENT = None

# Constants
packagedir = os.path.dirname(os.path.abspath(__file__))
KUBEFLOW_HELPER_FULL_PATH = os.path.join(packagedir, "kubeflow_helper.py")
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"
RESULTS_FILE = "experiment_results.json"

try:
    import kfp
    from kfp import dsl
    from kfp.v2 import compiler
    from kfp.v2.dsl import component, pipeline
    KFP_AVAILABLE = True
except ImportError:
    logger.warning("Kubeflow Pipelines SDK not found. Please install with: pip install kfp")
    KFP_AVAILABLE = False


def create_kfp_client():
    """Create and return Kubeflow Pipelines client"""
    if not KFP_AVAILABLE:
        raise ImportError("Kubeflow Pipelines SDK is required. Install with: pip install kfp")
    
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
    """Create mapping for execution engine - same as proactive_runner"""
    mapping = {}
    for t in tasks:
        map = {}
        mapping[t.name] = map
        for ds in t.input_files:
            if ds.name_in_generating_task:
                map[ds.name_in_task_signature] = ds.name_in_generating_task
    print("EXECUTION ENGINE MAPPING")
    print("*****************")
    import pprint
    pprint.pp(mapping)
    print("*****************")
    return mapping


def _create_exp_engine_metadata(exp_id, exp_name, wf_id):
    """Create experiment engine metadata - same as proactive_runner"""
    exp_engine_metadata = {}
    exp_engine_metadata["exp_id"] = exp_id
    exp_engine_metadata["exp_name"] = exp_name
    exp_engine_metadata["wf_id"] = wf_id
    return exp_engine_metadata


def _get_requirements_from_file(reqs_file):
    """Get requirements from file - same as proactive_runner"""
    if not os.path.exists(reqs_file):
        logger.info(f"Requirements file {reqs_file} does not exist. No requirements to install.")
        return []
    with open(reqs_file) as file:
        user_reqs = [line.rstrip() for line in file]
    return user_reqs


def _create_kubeflow_component(task, mapping, exp_engine_metadata, results_so_far):
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
    
    # Read task implementation
    with open(task.impl_file, 'r') as f:
        task_code = f.read()
    
    print(f"Task code for {task.name} loaded successfully.")

    # Create the component function
    # Force empty requirements to test if KFP is being added automatically
    test_requirements = []  # Empty list to test
    print(f"Using empty requirements list for testing: {test_requirements}")
    
    @component(
        base_image=base_image,
        packages_to_install=test_requirements
    )
    def task_component(
        task_name: str,
        wf_id: str,
        exp_id: str,
        config_json: str,
        mapping_json: str,
        metadata_json: str,
        task_code_param: str,  # Required parameter - no default value
        results_json: str = "{}"
    ) -> str:
        """Kubeflow component that wraps the original task implementation"""
        import sys
        import os
        import json
        import pickle
        from pathlib import Path
        
        # Setup directories
        os.makedirs("/tmp/inputs", exist_ok=True)
        os.makedirs("/tmp/outputs", exist_ok=True)
        os.makedirs("/tmp/config", exist_ok=True)
        
        # Parse inputs
        config = json.loads(config_json)
        mapping = json.loads(mapping_json)
        metadata = json.loads(metadata_json)
        results = json.loads(results_json)
        
        # Set up environment variables for the task
        os.environ['TASK_NAME'] = task_name
        os.environ['WF_ID'] = wf_id
        os.environ['EXP_ID'] = exp_id
        
        # Set up task parameters as environment variables
        task_params = config.get('task_params', {})
        for param_name, param_value in task_params.items():
            os.environ[param_name] = str(param_value)
        
        # Write configuration files
        with open('/tmp/config/runtime_config.json', 'w') as f:
            runtime_config = {
                "mapping": mapping,
                "exp_engine_metadata": metadata,
                "dataset_config": {
                    "DATASET_MANAGEMENT": config.get("DATASET_MANAGEMENT"),
                    "DDM_URL": config.get("DDM_URL"),
                    "DDM_TOKEN": config.get("DDM_TOKEN")
                }
            }
            json.dump(runtime_config, f)
        
        # Write results file if exists
        if results:
            with open('/tmp/inputs/experiment_results.json', 'w') as f:
                json.dump(results, f)
        
        # Add helper functions to path
        sys.path.insert(0, '/tmp')
        
        # Execute the original task code
        print(f"Executing task code for {task_name}...")
        exec(task_code_param)
        
        # Return success status
        return "completed"
    
    return task_component


def _convert_workflow_to_pipeline(workflow, mapping, exp_engine_metadata, results_so_far):
    """Convert a workflow to a Kubeflow pipeline"""
    print(f"Converting workflow {workflow.name} to Kubeflow pipeline...")
    
    # Create components for each task and store task codes
    task_components = {}
    task_codes = {}
    sorted_tasks = sorted(workflow.tasks, key=lambda t: t.order)
    
    for task in sorted_tasks:
        component_func = _create_kubeflow_component(task, mapping, exp_engine_metadata, results_so_far)
        task_components[task.name] = component_func
        
        # Store task code for later use
        with open(task.impl_file, 'r') as f:
            task_codes[task.name] = f.read()
    
    @pipeline(
        name=workflow.name.lower().replace(' ', '-'),
        description=f"Generated pipeline for workflow {workflow.name}"
    )
    def workflow_pipeline():
        """The main pipeline function"""
        task_outputs = {}
        
        # Prepare common parameters
        config_json = json.dumps({
            "DATASET_MANAGEMENT": CONFIG.DATASET_MANAGEMENT,
            "DDM_URL": getattr(CONFIG, 'DDM_URL', None),
            "DDM_TOKEN": getattr(CONFIG, 'DDM_TOKEN', None),
            "DATA_ABSTRACTION_BASE_URL": getattr(CONFIG, 'DATA_ABSTRACTION_BASE_URL', None),
            "DATA_ABSTRACTION_ACCESS_TOKEN": getattr(CONFIG, 'DATA_ABSTRACTION_ACCESS_TOKEN', None)
        })
        mapping_json = json.dumps(mapping)
        metadata_json = json.dumps(exp_engine_metadata)
        results_json = json.dumps(results_so_far) if results_so_far else "{}"
        
        for task in sorted_tasks:
            print(f"Adding task {task.name} to pipeline...")
            
            # Get the component function
            component_func = task_components[task.name]
            
            # Prepare task-specific config including parameters
            task_config = {
                "DATASET_MANAGEMENT": CONFIG.DATASET_MANAGEMENT,
                "DDM_URL": getattr(CONFIG, 'DDM_URL', None),
                "DDM_TOKEN": getattr(CONFIG, 'DDM_TOKEN', None),
                "DATA_ABSTRACTION_BASE_URL": getattr(CONFIG, 'DATA_ABSTRACTION_BASE_URL', None),
                "DATA_ABSTRACTION_ACCESS_TOKEN": getattr(CONFIG, 'DATA_ABSTRACTION_ACCESS_TOKEN', None),
                "task_params": dict(task.params) if hasattr(task, 'params') else {}
            }
            task_config_json = json.dumps(task_config)
            
            # Create the task in the pipeline
            task_op = component_func(
                task_name=task.name,
                wf_id=exp_engine_metadata["wf_id"],
                exp_id=exp_engine_metadata["exp_id"],
                config_json=task_config_json,
                mapping_json=mapping_json,
                metadata_json=metadata_json,
                results_json=results_json,
                task_code_param=task_codes[task.name]  # Pass the task code
            )
            
            # Set task name
            task_op.set_display_name(task.name)
            
            # Add dependencies
            for dep_name in task.dependencies:
                if dep_name in task_outputs:
                    task_op.after(task_outputs[dep_name])
            
            # Store task output for dependencies
            task_outputs[task.name] = task_op
    
    return workflow_pipeline


def _submit_pipeline_and_monitor(wf_id, client, pipeline_func, task_statuses):
    """Submit pipeline and monitor execution"""
    print("Compiling and submitting pipeline...")
    
    # Compile the pipeline
    pipeline_yaml = f"/tmp/pipeline_{wf_id}.yaml"
    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=pipeline_yaml
    )
    
    # Submit pipeline run
    experiment_name = f"exp_{wf_id}"
    run_name = f"run_{wf_id}_{int(time.time())}"
    
    try:
        # Create experiment if it doesn't exist
        try:
            experiment = client.create_experiment(experiment_name)
        except Exception:
            experiment = client.get_experiment(experiment_name=experiment_name)
        
        # Submit the run
        run = client.create_run_from_pipeline_package(
            pipeline_file=pipeline_yaml,
            arguments={},
            run_name=run_name,
            experiment_name=experiment_name
        )
        
        run_id = run.run_id
        print(f"Pipeline run submitted with ID: {run_id}")
        
        # Update workflow metadata
        update_workflow(wf_id, {"metadata": {"kubeflow_run_id": run_id}})
        
        # Monitor the run
        _monitor_pipeline_run(wf_id, client, run_id, task_statuses)
        
        # Get final results
        run_details = client.get_run(run_id)
        
        # Clean up
        if os.path.exists(pipeline_yaml):
            os.remove(pipeline_yaml)
        
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
                update_workflow(wf_id, {"status": run_status})
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
    global RUNNER_FOLDER, CONFIG, EXECUTION_ENGINE_RUNTIME_CONFIG, KFP_CLIENT
    
    if not KFP_AVAILABLE:
        raise ImportError("Kubeflow Pipelines SDK is required. Install with: pip install kfp")
    
    # Set global variables
    RUNNER_FOLDER = runner_folder
    CONFIG = config
    set_data_abstraction_config(CONFIG)
    EXECUTION_ENGINE_RUNTIME_CONFIG = f"{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}_{wf_id}.json"
    
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
    
    # Create task status tracking
    task_statuses = [{"name": task.name, "status": "Pending"} for task in w.tasks]
    
    # Convert workflow to pipeline
    pipeline_func = _convert_workflow_to_pipeline(w, mapping, exp_engine_metadata, results_so_far)

    print("Pipeline function created successfully.")
    print("****************************")
    
    # Submit and monitor pipeline
    try:
        run_id, run_details = _submit_pipeline_and_monitor(wf_id, KFP_CLIENT, pipeline_func, task_statuses)
        
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
        update_workflow(wf_id, {"status": "FAILED"})
        raise
    
    finally:
        # Cleanup
        if os.path.exists(EXECUTION_ENGINE_RUNTIME_CONFIG):
            os.remove(EXECUTION_ENGINE_RUNTIME_CONFIG)
        if os.path.exists(RESULTS_FILE):
            os.remove(RESULTS_FILE)
