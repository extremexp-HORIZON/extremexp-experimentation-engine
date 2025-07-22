"""
Main converter class for transforming .xxp DSL files to Kubeflow Pipelines
"""
import os
import yaml
import logging
from typing import Dict, List, Any
from ..functions import parsing
from ..models.workflow import Workflow
from ..models.task import Task

logger = logging.getLogger(__name__)

try:
    from kfp import dsl
    from kfp.v2 import compiler
    from kfp.v2.dsl import component, pipeline
    KFP_AVAILABLE = True
except ImportError:
    logger.warning("Kubeflow Pipelines SDK not found. Please install with: pip install kfp")
    KFP_AVAILABLE = False


class KubeflowConverter:
    """Converts .xxp DSL experiments to Kubeflow Pipelines"""
    
    def __init__(self, config=None):
        self.config = config
        self.task_components = {}
        
    def convert_xxp_to_kubeflow(self, experiment_specification: str, output_path: str) -> None:
        """
        Main conversion method from .xxp DSL to Kubeflow Pipeline
        
        Args:
            experiment_specification: The .xxp DSL content as string
            output_path: Directory where to save the generated pipeline files
        """
        if not KFP_AVAILABLE:
            raise ImportError("Kubeflow Pipelines SDK is required. Install with: pip install kfp")
            
        # Set up parsing configuration
        parsing.CONFIG = self.config
        
        logger.info("Starting .xxp to Kubeflow conversion...")
        
        # Parse workflows using existing infrastructure
        parsed_workflows, task_dependencies = parsing.parse_workflows(experiment_specification)
        assembled_workflows_data = parsing.parse_assembled_workflow_data(experiment_specification)
        
        # Handle assembled workflows if they exist
        if assembled_workflows_data:
            assembled_wfs = parsing.generate_final_assembled_workflows(parsed_workflows, assembled_workflows_data)
            assembled_flat_wfs = []
            parsing.generate_assembled_flat_workflows(assembled_wfs, assembled_flat_wfs)
            workflows_to_convert = assembled_flat_wfs
        else:
            workflows_to_convert = parsed_workflows
            
        # Create output directory
        os.makedirs(output_path, exist_ok=True)
        
        # Convert each workflow to a Kubeflow pipeline
        for workflow in workflows_to_convert:
            if workflow.is_main or workflow.is_main is None:  # Convert main workflows or when not specified
                logger.info(f"Converting workflow: {workflow.name}")
                pipeline_func = self._create_pipeline_function(workflow)
                
                # Compile the pipeline
                pipeline_filename = f"{workflow.name.lower().replace(' ', '_')}.yaml"
                pipeline_path = os.path.join(output_path, pipeline_filename)
                
                compiler.Compiler().compile(
                    pipeline_func=pipeline_func,
                    package_path=pipeline_path
                )
                
                logger.info(f"Generated pipeline: {pipeline_path}")
                
                # Also generate a Python file with the pipeline definition
                python_filename = f"{workflow.name.lower().replace(' ', '_')}_pipeline.py"
                python_path = os.path.join(output_path, python_filename)
                self._generate_pipeline_python_file(workflow, python_path)
                
        logger.info("Conversion completed successfully!")
        
    def _create_pipeline_function(self, workflow: Workflow):
        """Convert workflow to Kubeflow pipeline function"""
        
        # Create components for each task
        task_components = {}
        for task in workflow.tasks:
            component_func = self._create_task_component(task)
            task_components[task.name] = component_func
            
        @pipeline(
            name=workflow.name.lower().replace(' ', '-'),
            description=f"Generated from {workflow.name}.xxp DSL"
        )
        def pipeline_func():
            task_outputs = {}
            
            # Sort tasks by order to maintain execution sequence
            sorted_tasks = sorted(workflow.tasks, key=lambda t: t.order if t.order else 0)
            
            for task in sorted_tasks:
                component_func = task_components[task.name]
                
                # Create the task instance (simplified for now)
                task_op = component_func()
                task_op.set_display_name(task.name)
                
                # Set dependencies
                for dep_task_name in task.dependencies:
                    if dep_task_name in task_outputs:
                        task_op.after(task_outputs[dep_task_name])
                        
                task_outputs[task.name] = task_op
                
            # Return None for pipeline functions (no outputs for now)
            return None
            
        return pipeline_func
        
    def _create_task_component(self, task: Task):
        """Create a Kubeflow component for a task"""
        
        # Determine base image
        base_image = self._get_base_image(task)
        
        # Read task implementation
        task_script = self._get_task_script(task)
        
        # Define input/output specifications
        inputs_spec = self._get_task_inputs_spec(task)
        outputs_spec = self._get_task_outputs_spec(task)
        
        # Create a simpler component without dynamic kwargs
        @component(
            base_image=base_image,
            packages_to_install=self._get_required_packages(task)
        )
        def task_component():
            """Generated component for task execution"""
            import os
            import pickle
            import json
            
            # Create necessary directories
            os.makedirs("/tmp/inputs", exist_ok=True)
            os.makedirs("/tmp/outputs", exist_ok=True)
            
            # Execute the adapted task script
            # Create a globals dict with the task script context
            script_globals = {
                "__name__": "__main__",
                "os": os,
                "pickle": pickle,
                "json": json
            }
            
            # Execute the task script
            exec(task_script, script_globals)
            
        return task_component
        
    def _get_base_image(self, task: Task) -> str:
        """Determine the appropriate base image for the task"""
        if task.python_version:
            return f"python:{task.python_version}-slim"
        return "python:3.9-slim"
        
    def _get_task_script(self, task: Task) -> str:
        """Get and adapt the task script for Kubeflow execution"""
        if task.impl_file and os.path.exists(task.impl_file):
            with open(task.impl_file, 'r') as f:
                script_content = f.read()
                
            # Adapt the script for Kubeflow
            adapted_script = self._adapt_script_for_kubeflow(script_content, task)
            return adapted_script
        else:
            # Default script if no implementation file
            return '''
print(f"Executing task: {task.name}")
# Default task implementation
result = "Task completed successfully"
print(result)
'''
            
    def _adapt_script_for_kubeflow(self, script: str, task: Task) -> str:
        """Adapt ProActive script to work in Kubeflow environment"""
        
        # Replace ProActive-specific imports and calls
        adapted_script = script
        
        # Replace proactive_helper imports
        adapted_script = adapted_script.replace(
            "import proactive_helper as ph",
            "# Replaced proactive_helper with kubeflow equivalents"
        )
        
        # Replace common ProActive helper patterns
        replacements = {
            "ph.load_datasets(": "kubeflow_load_datasets(",
            "ph.save_datasets(": "kubeflow_save_datasets(",
            "ph.load_dataset(": "kubeflow_load_dataset(",
            "ph.save_dataset(": "kubeflow_save_dataset(",
            "variables.get(": "os.environ.get(",
            "resultMap": "result_map",
        }
        
        for old, new in replacements.items():
            adapted_script = adapted_script.replace(old, new)
            
        # Add Kubeflow helper functions at the beginning
        kubeflow_helpers = '''
import os
import pickle
import json

def kubeflow_load_datasets(*keys):
    """Load datasets in Kubeflow environment"""
    results = []
    for key in keys:
        input_path = f"/tmp/inputs/{key}"
        if os.path.exists(input_path):
            with open(input_path, 'rb') as f:
                results.append(pickle.load(f))
        else:
            results.append(None)
    return results if len(results) > 1 else results[0]

def kubeflow_save_datasets(result_map, key, values, file_names=None):
    """Save datasets in Kubeflow environment"""
    os.makedirs("/tmp/outputs", exist_ok=True)
    if isinstance(values, list):
        for i, value in enumerate(values):
            filename = file_names[i] if file_names and i < len(file_names) else f"{key}_{i}"
            output_path = f"/tmp/outputs/{filename}"
            with open(output_path, 'wb') as f:
                pickle.dump(value, f)
    else:
        output_path = f"/tmp/outputs/{key}"
        with open(output_path, 'wb') as f:
            pickle.dump(values, f)

def kubeflow_load_dataset(key):
    """Load single dataset"""
    return kubeflow_load_datasets(key)

def kubeflow_save_dataset(result_map, key, value):
    """Save single dataset"""
    return kubeflow_save_datasets(result_map, key, value)

# Initialize result_map for compatibility
result_map = {}

'''
        
        return kubeflow_helpers + adapted_script
        
    def _get_required_packages(self, task: Task) -> List[str]:
        """Get list of required packages for the task"""
        packages = []
        
        if task.requirements_file and os.path.exists(task.requirements_file):
            with open(task.requirements_file, 'r') as f:
                packages = [line.strip() for line in f.readlines() 
                           if line.strip() and not line.startswith('#')]
        else:
            # Default packages
            packages = ['numpy', 'pandas', 'scikit-learn']
            
        return packages
        
    def _get_task_inputs_spec(self, task: Task) -> Dict[str, Any]:
        """Get input specifications for the task component"""
        inputs = {}
        
        for input_file in task.input_files:
            # Use str type for file paths in Kubeflow
            inputs[input_file.name] = str
            
        # Add task parameters as inputs
        for param_name, param_value in task.params.items():
            if isinstance(param_value, str):
                inputs[param_name] = str
            elif isinstance(param_value, int):
                inputs[param_name] = int
            elif isinstance(param_value, float):
                inputs[param_name] = float
            else:
                inputs[param_name] = str
                
        return inputs
        
    def _get_task_outputs_spec(self, task: Task) -> Dict[str, Any]:
        """Get output specifications for the task component"""
        outputs = {}
        
        for output_file in task.output_files:
            outputs[output_file.name] = str
            
        return outputs
        
    def _prepare_task_inputs(self, task: Task, previous_outputs: Dict) -> Dict[str, Any]:
        """Prepare inputs for task execution"""
        inputs = {}
        
        # Add input files from previous tasks
        for input_file in task.input_files:
            if hasattr(input_file, 'name_in_generating_task') and input_file.name_in_generating_task in previous_outputs:
                source_task = previous_outputs[input_file.name_in_generating_task]
                # In Kubeflow, we reference outputs from previous tasks
                inputs[input_file.name] = source_task.outputs.get(input_file.name, "")
            else:
                inputs[input_file.name] = ""
                
        # Add task parameters
        for param_name, param_value in task.params.items():
            inputs[param_name] = param_value
            
        return inputs
        
    def _generate_pipeline_python_file(self, workflow: Workflow, output_path: str):
        """Generate a Python file with the pipeline definition for easy customization"""
        
        python_code = f'''"""
Generated Kubeflow Pipeline for {workflow.name}
This file contains the pipeline definition that can be customized and executed.
"""

from kfp import dsl
from kfp.v2 import compiler
from kfp.v2.dsl import component, pipeline

# Pipeline definition
@pipeline(
    name="{workflow.name.lower().replace(' ', '-')}",
    description="Generated from {workflow.name}.xxp DSL"
)
def {workflow.name.lower().replace(' ', '_')}_pipeline():
    """Pipeline function generated from .xxp DSL"""
    
    # TODO: Add your pipeline logic here
    # This is a template - customize as needed
    
    pass

if __name__ == "__main__":
    # Compile the pipeline
    compiler.Compiler().compile(
        pipeline_func={workflow.name.lower().replace(' ', '_')}_pipeline,
        package_path="{workflow.name.lower().replace(' ', '_')}.yaml"
    )
    print("Pipeline compiled successfully!")
'''
        
        with open(output_path, 'w') as f:
            f.write(python_code)
            
        logger.info(f"Generated Python pipeline file: {output_path}")
