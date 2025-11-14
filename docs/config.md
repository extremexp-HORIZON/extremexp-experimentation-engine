# Configuration

ExtremeXP uses a central configuration file `eexp_config.py` to manage all system settings. This file controls experiment execution, data management, logging, and integration with external services.

## Configuration File Structure

The configuration file should be placed in your project root directory and named `eexp_config.py`. Below is a complete example configuration:

```python
# eexp_config.py

# Main Directories
EXPERIMENT_LIBRARY_PATH = 'relative_path/to/experiments_directory'
TASK_LIBRARY_PATH = 'relative_path/to/tasks_directory'
PYTHON_DEPENDENCIES_RELATIVE_PATH = 'relative_path/to/dependencies_directory'
DATASET_LIBRARY_RELATIVE_PATH = 'relative_path/to/datasets_directory'

# Helper Modules
PYTHON_CONDITIONS = '<relative_path_to_experiment_conditions_directory>.<name_of_the_python_file_to_use>' # 'library-tasks,experiment_conditions'
PYTHON_CONFIGURATIONS = '<relative_path_to_experiment_configurations_directory>.<name_of_the_python_file_to_use>' # 'library-tasks.experiment_configurations'

# Execution Configuration
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 3
EXECUTIONWARE = "PROACTIVE"
PROACTIVE_URL = "https://your-proactive-server.com"
PROACTIVE_USERNAME = "your_username"
PROACTIVE_PASSWORD = "your_password"
PROACTIVE_PYTHON_VERSIONS = {
    "3.8": "/usr/bin/python3.8",
    "3.9": "/usr/bin/python3.9"
}

# Data Management
DATA_ABSTRACTION_BASE_URL = "https://your-dal-server.com/api"
DATA_ABSTRACTION_ACCESS_TOKEN = 'your_DAL_token'
DATASET_MANAGEMENT = "DDM"
DDM_URL = "https://your-ddm-server.com/api"
PORTAL_USERNAME = "your_portal_username"
PORTAL_PASSWORD = "your_portal_password"

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'loggers': {
        'eexp_engine': {'level': 'DEBUG'},
        'eexp_engine.functions': {'level': 'DEBUG'},
        'eexp_engine.functions.parsing': {'level': 'INFO'},
        'eexp_engine.functions.execution': {'level': 'DEBUG'},
        'eexp_engine.data_abstraction_layer': {'level': 'DEBUG'},
        'eexp_engine.models': {'level': 'DEBUG'},
        'eexp_engine.models.experiment': {'level': 'DEBUG'},
        'eexp_engine.proactive_executionware': {'level': 'DEBUG'}
    }
}
```

## Configuration Sections

### Main Directories

These settings define the core directory structure for your ExtremeXP project:

| Field | Description | Example |
|-------|-------------|---------|
| `EXPERIMENT_LIBRARY_PATH` | Path to experiment specs (`.xxp` files). Can be absolute or relative. | `'experiments'` |
| `TASK_LIBRARY_PATH` | Path to tasks referenced by specs. Each task is a folder with `.xxp` file. | `'tasks'` |
| `PYTHON_DEPENDENCIES_RELATIVE_PATH` | Path to additional Python dependencies, relative to runner script. | `'dependencies'` |
| `DATASET_LIBRARY_RELATIVE_PATH` | Path for input/output dataset files (LOCAL dataset management). | `'datasets'` |

!!! info "Directory Structure"
    Ensure these directories exist in your project structure:
    ```
    your_project/
    ├── experiments/          # .xxp experiment files
    ├── tasks/               # task implementations
    ├── dependencies/        # Python modules
    └── datasets/           # input/output data files
    ```

### Helper Modules

These settings specify Python modules that provide custom functions for experiments:

| Field | Description | Example |
|-------|-------------|---------|
| `PYTHON_CONDITIONS` | Python module for condition functions used in experiments. | `'library-tasks.experiment_conditions'` |
| `PYTHON_CONFIGURATIONS` | Python module for config filtering/generation for spaces. | `'library-tasks.experiment_configurations'` |

!!! note "Custom Functions"
    These modules should contain Python functions that can be referenced in your experiment DSL for conditions, filters, and generators.

### Execution Configuration

Controls how experiments are executed:

| Field | Description | Options | Default |
|-------|-------------|---------|---------|
| `MAX_WORKFLOWS_IN_PARALLEL_PER_NODE` | Max parallel workflows per node. | Any positive integer | `1` |
| `EXECUTIONWARE` | Execution engine selection. | `"PROACTIVE"` or `"LOCAL"` | `"LOCAL"` |
| `PROACTIVE_URL` | Proactive endpoint URL (required if using PROACTIVE). | Valid URL | - |
| `PROACTIVE_USERNAME` | Username for Proactive authentication. | String | - |
| `PROACTIVE_PASSWORD` | Password for Proactive authentication. | String | - |
| `PROACTIVE_PYTHON_VERSIONS` | Dict mapping Python versions to executables on server. | `{"3.8": "/usr/bin/python3.8"}` | - |

#### Execution Mode Examples

**Local Execution:**
```python
EXECUTIONWARE = "LOCAL"
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 1
```

**Proactive Execution:**
```python
EXECUTIONWARE = "PROACTIVE"
PROACTIVE_URL = "https://your-proactive-server.com"
PROACTIVE_USERNAME = "your_username"
PROACTIVE_PASSWORD = "your_password"
PROACTIVE_PYTHON_VERSIONS = {
    "3.8": "/usr/bin/python3.8",
    "3.9": "/usr/bin/python3.9"
}
```

### Data Management

Configures how data is handled and accessed:

| Field | Description | Options | Required |
|-------|-------------|---------|----------|
| `DATA_ABSTRACTION_BASE_URL` | URL of the Data Abstraction Layer. | Valid URL | If using DAL |
| `DATA_ABSTRACTION_ACCESS_TOKEN` | Access token for DAL authentication. | String | If using DAL |
| `DATASET_MANAGEMENT` | Data management strategy. | `"LOCAL"` or `"DDM"` | Yes |
| `DDM_URL` | Endpoint for DDM (used if `DDM` selected). | Valid URL | If using DDM |
| `PORTAL_USERNAME` | credentials you use to login to the portal deployed in ICOM | String | If using DDM |
| `PORTAL_PASSWORD` | credentials you use to login to the portal deployed in ICOM | String | If using DDM |

#### Data Management Options

**Local Data Management:**
```python
DATASET_MANAGEMENT = "LOCAL"
DATASET_LIBRARY_RELATIVE_PATH = 'datasets'
```

**Decentralized Data Management (DDM):**
```python
DATASET_MANAGEMENT = "DDM"
DDM_URL = "http://your-ddm-server.com/api"
PORTAL_USERNAME = "your_portal_username"
PORTAL_PASSWORD = "your_portal_password"
```

### Logging Configuration

Controls logging levels and output for different components:

| Field | Description |
|-------|-------------|
| `LOGGING_CONFIG` | Python `logging` dict to control log levels. See [Python Logging Config DictSchema](https://docs.python.org/3/library/logging.config.html#logging-config-dictschema). |

#### Logging Levels

The logging configuration uses standard Python logging levels:

- `DEBUG`: Detailed information, typically of interest only when diagnosing problems
- `INFO`: General information about program execution
- `WARNING`: Something unexpected happened, but the program is still working
- `ERROR`: A serious problem occurred, the program couldn't perform a function
- `CRITICAL`: A very serious error occurred, the program may not be able to continue

#### Example Logging Configurations

**Development (Verbose):**
```python
LOGGING_CONFIG = {
    'version': 1,
    'loggers': {
        'eexp_engine': {'level': 'DEBUG'},
        'eexp_engine.functions': {'level': 'DEBUG'},
        'eexp_engine.functions.parsing': {'level': 'DEBUG'},
        'eexp_engine.functions.execution': {'level': 'DEBUG'},
    }
}
```

**Production (Minimal):**
```python
LOGGING_CONFIG = {
    'version': 1,
    'loggers': {
        'eexp_engine': {'level': 'INFO'},
        'eexp_engine.functions': {'level': 'WARNING'},
        'eexp_engine.functions.parsing': {'level': 'WARNING'},
        'eexp_engine.functions.execution': {'level': 'INFO'},
    }
}
```