# ExtremeXP Experimentation Engine

A Python framework for defining, executing, and managing adaptive experiments across multiple execution backends.

## Overview

The ExtremeXP Experimentation Engine is the core component implementing Continuous Adaptive Experiment Planning functionality. It enables researchers and data scientists to:

- **Define experiments** using a simple Domain-Specific Language (DSL)
- **Execute workflows** across different platforms (ProActive scheduler, Kubeflow pipelines, or local execution)
- **Manage datasets** through local storage or distributed data management (DDM)
- **Track experiment metadata** and results through the Data Abstraction Layer (DAL)
- **Support user interaction** workflows for human-in-the-loop experiments

### Components

1. **ExecutionWare** - Handles workflow scheduling and execution
   - **[ProActive](https://github.com/ow2-proactive)**: Executes on ActiveEon's ProActive platform
   - `Kubeflow`: Executes as Kubeflow pipelines
   - `Local`: Direct execution on local machine

2. **DataManager** - Manages dataset retrieval and storage
   - **[DDM](https://github.com/extremexp-HORIZON/DDM)**: Distributed data management via Zenoh framework
   - `LocalStorage`: Local filesystem-based storage

3. **[DAL](https://github.com/extremexp-HORIZON/extremexp-dal)** - Data Abstraction Layer for experiment metadata and metrics

## Installation

### Prerequisites

- Python >= 3.8
- Virtual environment (recommended)

### Quick Install

```bash
# Create and activate virtual environment
python3 -m venv env
source ./env/bin/activate  # On Windows: env\Scripts\activate

# Install from PyPI
pip install eexp_engine
```

### Development Installation

For development or to get the latest features:

```bash
# Clone the repository
git clone https://github.com/extremexp-HORIZON/extremexp-experimentation-engine.git
cd extremexp-experimentation-engine

# Create and activate virtual environment
python3 -m venv env
source ./env/bin/activate

# Install in editable mode
pip install -e exp_engine
```

## Configuration

### 1. Create Configuration File

Copy the template configuration file:

```bash
cp eexp_config_TEMPLATE.py eexp_config.py
```

### 2. Configure Settings

Edit `eexp_config.py` and configure the following sections:

#### Required Settings

```python
# Paths to your experiment and task libraries
TASK_LIBRARY_PATH = 'playground/tasks'
EXPERIMENT_LIBRARY_PATH = 'playground/experiments'
DATASET_LIBRARY_RELATIVE_PATH = 'playground/datasets'
PYTHON_DEPENDENCIES_RELATIVE_PATH = 'playground/dependencies'

# Python modules for conditions and configurations
PYTHON_CONDITIONS = 'playground/tasks/experiment_conditions'
PYTHON_CONFIGURATIONS = 'playground/tasks/experiment_configurations'

# Execution backend: "PROACTIVE", "KUBEFLOW", or "LOCAL"
EXECUTIONWARE = "PROACTIVE"

# Data Abstraction Layer credentials
DATA_ABSTRACTION_BASE_URL = "http://your-dal-server/api"
DATA_ABSTRACTION_ACCESS_TOKEN = 'your-access-token'

# Dataset management: "DDM" or "LOCAL"
DATASET_MANAGEMENT = "DDM"
```

#### ProActive Configuration (if using EXECUTIONWARE = "PROACTIVE")

```python
PROACTIVE_URL = "http://your-proactive-server"
PROACTIVE_USERNAME = "your-username"
PROACTIVE_PASSWORD = "your-password"
PROACTIVE_PYTHON_VERSIONS = {
    "3.8": "/usr/bin/python3.8",
    "3.9": "/usr/bin/python3.9"
}
```

#### Kubeflow Configuration (if using EXECUTIONWARE = "KUBEFLOW")

```python
KUBEFLOW_URL = "http://your-kubeflow-server"
KUBEFLOW_USERNAME = "your-username"
KUBEFLOW_PASSWORD = "your-password"
KUBEFLOW_MINIO_ENDPOINT = "your-minio-endpoint"
KUBEFLOW_MINIO_USERNAME = "minio-user"
KUBEFLOW_MINIO_PASSWORD = "minio-password"
```

#### Optional Settings

```python
# Parallel execution limits
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 3
MAX_EXPERIMENTS_IN_PARALLEL = 4

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'loggers': {
        'eexp_engine': {'level': 'INFO'}
    }
}
```

## Running Experiments

### Method 1: Using the CLI (`eexp-run`)

The easiest way to run experiments is using the command-line interface:

```bash
eexp-run
```

This launches an interactive menu where you can:
1. Browse available experiments from your `EXPERIMENT_LIBRARY_PATH`
2. Select an experiment to run
3. Monitor execution progress

### Method 2: Programmatically

Create a Python script (e.g., `my_experiment.py`):

```python
from eexp_engine import client
from eexp_engine.runner import select_file
import eexp_config

if __name__ == "__main__":
    # Interactive selection
    selected_file, exp_name = select_file()
    if selected_file and exp_name:
        client.run(selected_file, exp_name, eexp_config)
```

Or run a specific experiment directly:

```python
from eexp_engine import client
import eexp_config

if __name__ == "__main__":
    experiment_file = "playground/experiments/my_experiment.xxp"
    experiment_name = "MyExperiment"

    client.run(experiment_file, experiment_name, eexp_config)
```

Then execute:

```bash
python my_experiment.py
```

### Examples

The repository includes example experiment, workflows and tasks under `playground` directory:

## Running as a Service

The Experimentation Engine can be deployed as a REST API service using Docker, allowing remote execution and management of experiments.

### Service Architecture

The service provides a Flask-based REST API with the following endpoints:

- `POST /exp/run/<experimentname>` - Run an experiment
- `GET /exp/workflow/kill/<workflow_id>` - Kill a workflow
- `GET /exp/workflow/pause/<workflow_id>` - Pause a workflow
- `GET /exp/workflow/resume/<workflow_id>` - Resume a workflow
- `GET /exp/experiment/kill/<experiment_id>` - Kill an experiment
- `GET /exp/experiment/pause/<experiment_id>` - Pause an experiment
- `GET /exp/experiment/resume/<experiment_id>` - Resume an experiment
- `GET /exp/experiment/status/<experiment_id>` - Get experiment status

### Deployment Options

#### Option 1: Using Docker Compose (Recommended)

1. **Configure the service:**
   - Ensure your `eexp_config.py` is properly configured
   - Update `docker-compose.yaml` if needed to adjust ports or volumes

2. **Start the service:**
   ```bash
   docker-compose up -d
   ```

3. **Access the service:**
   The API will be available at `http://localhost:5556`

4. **View logs:**
   ```bash
   docker-compose logs -f exp_engine
   ```

5. **Stop the service:**
   ```bash
   docker-compose down
   ```

#### Option 2: Using Pre-built Images from GitHub Container Registry

The project includes GitHub Actions that automatically build and publish Docker images on every push to `main`.

1. **Pull the latest image:**
   ```bash
   docker pull ghcr.io/extremexp-horizon/exp-engine:latest
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name exp-engine-service \
     -p 5556:5556 \
     ghcr.io/extremexp-horizon/exp-engine:latest
   ```

## Documentation

For detailed documentation, see:

- **[Online Documentation](https://extremexp-horizon.github.io/extremexp-experimentation-engine/)**

## License

Apache License 2.0

## Links

- **Homepage**: https://github.com/extremexp-HORIZON/extremexp-experimentation-engine
- **Issues**: https://github.com/extremexp-HORIZON/extremexp-experimentation-engine/issues
- **PyPI**: https://pypi.org/project/eexp-engine/
