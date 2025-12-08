# ExecutionWare Overview

ExecutionWare is a core component of the ExtremeXP framework that provides runtime execution environments for workflows and tasks. It acts as an abstraction layer between the workflow definitions and the actual execution infrastructure, enabling workflows to run on different platforms while maintaining the same interface.

## What is ExecutionWare?

ExecutionWare implementations provide the necessary infrastructure and helper functions that enable tasks to:

- Load and save datasets from various sources
- Handle data serialization and deserialization
- Manage file paths and directories
- Coordinate data flow between tasks
- Access runtime variables and configuration
- Handle different data management backends

Each ExecutionWare implementation offers a consistent API through helper functions that task implementations use to interact with the underlying execution environment.

## Available ExecutionWare Types

ExtremeXP currently supports three main ExecutionWare implementations:

### 1. Local ExecutionWare
- **Purpose**: Executes workflows locally on a single machine using subprocess
- **Data Management**: Files are stored locally using the filesystem
- **Use Case**: Development, testing, and small-scale experiments
- **Helper Module**: Access via `eexp_engine_utils`

### 2. Proactive ExecutionWare
- **Purpose**: Executes workflows on ProActive Scheduler (distributed computing)
- **Data Management**: Supports both local files and DDM (Distributed Data Management)
- **Use Case**: Production experiments, distributed computing with ActiveEon ProActive
- **Helper Module**: Access via `eexp_engine_utils`

### 3. Kubeflow ExecutionWare
- **Purpose**: Executes workflows as Kubeflow Pipelines on Kubernetes clusters
- **Data Management**: Supports both local files (MinIO S3 for artifact storage ) and DDM (Distributed Data Management)
- **Use Case**: Cloud-native deployments, Kubernetes infrastructure, ML pipelines
- **Helper Module**: Access via `eexp_engine_utils`

## How Tasks Use ExecutionWare

Tasks use the utilities from `eexp_engine_utils` to interact with the execution environment. The utilities automatically detect which ExecutionWare backend is being used and route function calls to the appropriate implementation:

```python
from eexp_engine_utils import utils

# Load input data
dataset = utils.load_dataset(variables, resultMap, "input_data")

# Process the data
processed_data = process_dataset(dataset)

# Save output data
utils.save_dataset(variables, resultMap, "output_data", processed_data)
```

This approach allows you to write task implementations once and run them on any ExecutionWare backend (Local, Proactive, or Kubeflow) without modification.

## ExecutionWare Selection

The choice of ExecutionWare depends on your deployment requirements:

- **Local ExecutionWare**: Choose for development, testing, or single-machine experiments
- **Proactive ExecutionWare**: Choose for production deployments with ActiveEon ProActive infrastructure
- **Kubeflow ExecutionWare**: Choose for Kubernetes-based deployments, cloud-native applications, or when you need ML pipeline integration

## Data Management Integration

ExecutionWare supports different data management backends:

#### Local ExecutionWare:
   - **Local Files**: Traditional filesystem-based storage

#### Proactive ExecutionWare:
   - **Local Files**: Traditional filesystem-based storage
   - **DDM**: Distributed data management for cloud and cluster environments
   - **Hybrid Approaches**: Combination of local and distributed storage

#### Kubeflow ExecutionWare:
   - **MinIO S3**: Object storage for artifacts and intermediate files
   - **DDM**: Distributed data management integration
   - **Kubernetes Volumes**: Persistent volume claims for data storage

The workflow DSL automatically handles the appropriate data management configuration based on the ExecutionWare type and configuration settings.

## Configuration

ExecutionWare behavior is controlled through configuration files:

- **Local**: `variables.json`, `execution_engine_mapping.json`
- **Proactive**: Runtime configuration files with execution engine metadata
- **Kubeflow**: Runtime configuration files with execution engine metadata

## Next Steps

Learn more about each ExecutionWare implementation and their specific helper functions:

- **[Local ExecutionWare](local.md)**: Helper functions for local development and testing
- **[Proactive ExecutionWare](proactive.md)**: Helper functions for ProActive-based production deployments
- **[Kubeflow ExecutionWare](kubeflow.md)**: Helper functions for Kubernetes and Kubeflow Pipelines