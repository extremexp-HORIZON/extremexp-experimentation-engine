"""
Kubeflow helper functions - equivalents of proactive_helper for Kubeflow execution
"""
import os
import pickle
import json
import logging
from pathlib import Path
from typing import Any, List, Dict, Optional, Union

logger = logging.getLogger(__name__)

# Constants for Kubeflow environment
INPUTS_DIR = "/tmp/inputs"
OUTPUTS_DIR = "/tmp/outputs" 
METRICS_DIR = "/tmp/metrics"
CONFIG_DIR = "/tmp/config"


def setup_directories():
    """Create necessary directories for Kubeflow execution"""
    for directory in [INPUTS_DIR, OUTPUTS_DIR, METRICS_DIR, CONFIG_DIR]:
        os.makedirs(directory, exist_ok=True)


def load_datasets(*keys: str) -> Union[Any, List[Any]]:
    """
    Load datasets in Kubeflow environment
    
    Args:
        *keys: Dataset keys to load
        
    Returns:
        Single dataset if one key provided, list of datasets if multiple keys
    """
    setup_directories()
    results = []
    
    for key in keys:
        input_path = os.path.join(INPUTS_DIR, f"{key}.pkl")
        
        if os.path.exists(input_path):
            try:
                with open(input_path, 'rb') as f:
                    data = pickle.load(f)
                    results.append(data)
                    logger.info(f"Loaded dataset: {key}")
            except Exception as e:
                logger.warning(f"Failed to load dataset {key}: {e}")
                results.append(None)
        else:
            logger.warning(f"Dataset not found: {key}")
            results.append(None)
    
    return results[0] if len(results) == 1 else results


def save_datasets(*datasets: tuple) -> None:
    """
    Save datasets in Kubeflow environment
    
    Args:
        *datasets: Tuples of (key, value) pairs to save
    """
    setup_directories()
    
    for dataset in datasets:
        if isinstance(dataset, tuple) and len(dataset) == 2:
            key, value = dataset
            output_path = os.path.join(OUTPUTS_DIR, f"{key}.pkl")
            
            try:
                with open(output_path, 'wb') as f:
                    pickle.dump(value, f)
                logger.info(f"Saved dataset: {key}")
            except Exception as e:
                logger.error(f"Failed to save dataset {key}: {e}")
                raise
        else:
            logger.error(f"Invalid dataset format: {dataset}. Expected tuple (key, value)")


def save_dataset(key: str, value: Any) -> None:
    """
    Save a single dataset
    
    Args:
        key: Dataset key
        value: Dataset value
    """
    save_datasets((key, value))


def load_dataset(key: str) -> Any:
    """
    Load a single dataset
    
    Args:
        key: Dataset key
        
    Returns:
        The loaded dataset
    """
    return load_datasets(key)


def load_dataset_by_path(file_path: str) -> Any:
    """
    Load dataset from specific file path
    
    Args:
        file_path: Path to the dataset file
        
    Returns:
        The loaded dataset
    """
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except Exception as e:
        logger.error(f"Failed to load dataset from {file_path}: {e}")
        raise


def save_dataset_by_path(file_path: str, data: Any) -> None:
    """
    Save dataset to specific file path
    
    Args:
        file_path: Path where to save the dataset
        data: Data to save
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Saved dataset to: {file_path}")
    except Exception as e:
        logger.error(f"Failed to save dataset to {file_path}: {e}")
        raise


def create_dir(key: str) -> str:
    """
    Create directory for outputs
    
    Args:
        key: Directory key/name
        
    Returns:
        Path to created directory
    """
    output_dir = os.path.join(OUTPUTS_DIR, key)
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"Created directory: {output_dir}")
    return output_dir


def save_metrics(metrics: Dict[str, Any]) -> None:
    """
    Save metrics for the task
    
    Args:
        metrics: Dictionary of metric name to value mappings
    """
    setup_directories()
    
    metrics_file = os.path.join(METRICS_DIR, "metrics.json")
    
    try:
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Saved metrics: {list(metrics.keys())}")
    except Exception as e:
        logger.error(f"Failed to save metrics: {e}")
        raise


def load_config(config_key: str = "runtime_config") -> Dict[str, Any]:
    """
    Load configuration data
    
    Args:
        config_key: Configuration key to load
        
    Returns:
        Configuration dictionary
    """
    setup_directories()
    
    config_file = os.path.join(CONFIG_DIR, f"{config_key}.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded config: {config_key}")
            return config
        except Exception as e:
            logger.warning(f"Failed to load config {config_key}: {e}")
            return {}
    else:
        logger.warning(f"Config file not found: {config_key}")
        return {}


def save_config(config: Dict[str, Any], config_key: str = "runtime_config") -> None:
    """
    Save configuration data
    
    Args:
        config: Configuration dictionary to save
        config_key: Configuration key
    """
    setup_directories()
    
    config_file = os.path.join(CONFIG_DIR, f"{config_key}.json")
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Saved config: {config_key}")
    except Exception as e:
        logger.error(f"Failed to save config {config_key}: {e}")
        raise


def list_input_files() -> List[str]:
    """
    List all available input files
    
    Returns:
        List of input file names
    """
    setup_directories()
    
    if os.path.exists(INPUTS_DIR):
        files = [f for f in os.listdir(INPUTS_DIR) if f.endswith('.pkl')]
        return [f.replace('.pkl', '') for f in files]
    return []


def list_output_files() -> List[str]:
    """
    List all generated output files
    
    Returns:
        List of output file names
    """
    setup_directories()
    
    if os.path.exists(OUTPUTS_DIR):
        files = [f for f in os.listdir(OUTPUTS_DIR) if f.endswith('.pkl')]
        return [f.replace('.pkl', '') for f in files]
    return []


def get_environment_variable(key: str, default: Any = None) -> str:
    """
    Get environment variable (replacement for variables.get() in ProActive)
    
    Args:
        key: Environment variable key
        default: Default value if not found
        
    Returns:
        Environment variable value
    """
    return os.environ.get(key, default)


def set_environment_variable(key: str, value: str) -> None:
    """
    Set environment variable
    
    Args:
        key: Environment variable key
        value: Environment variable value
    """
    os.environ[key] = str(value)
    logger.info(f"Set environment variable: {key}")


# Compatibility aliases for ProActive helper functions
def get_experiment_results() -> Optional[Dict[str, Any]]:
    """Get experiment results (compatibility function)"""
    results_file = os.path.join(OUTPUTS_DIR, "experiment_results.json")
    
    if os.path.exists(results_file):
        try:
            with open(results_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load experiment results: {e}")
            return None
    
    logger.warning("Experiment results file not found")
    return None


def save_experiment_results(results: Dict[str, Any]) -> None:
    """Save experiment results"""
    setup_directories()
    
    results_file = os.path.join(OUTPUTS_DIR, "experiment_results.json")
    
    try:
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        logger.info("Saved experiment results")
    except Exception as e:
        logger.error(f"Failed to save experiment results: {e}")
        raise
