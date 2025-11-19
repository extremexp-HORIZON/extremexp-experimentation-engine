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

ExtremeXP currently supports two main ExecutionWare implementations:

### 1. Local ExecutionWare
- **Purpose**: Executes workflows locally on a single machine
- **Data Management**: Files are stored locally using the filesystem
- **Use Case**: Development, testing, and small-scale experiments
- **Helper Module**: `local_helper`

### 2. Proactive ExecutionWare
- **Purpose**: Executes workflows on distributed computing infrastructure
- **Data Management**: Supports both local files and distributed data management (Zenoh)
- **Use Case**: Large-scale experiments, cloud deployments, and distributed computing
- **Helper Module**: `proactive_helper`

## How Tasks Use ExecutionWare

Tasks import the appropriate helper module and use its functions to handle data operations:

```python
# Example task using Proactive ExecutionWare
import proactive_helper as ph

# Load input data
dataset = ph.load_dataset(variables, resultMap, "input_data")

# Process the data
processed_data = process_dataset(dataset)

# Save output data
ph.save_dataset(variables, resultMap, "output_data", processed_data)
```

## ExecutionWare Selection

The choice of ExecutionWare depends on your deployment requirements:

- **Local ExecutionWare**: Choose for development, testing, or single-machine experiments
- **Proactive ExecutionWare**: Choose for production deployments, distributed computing, or when using cloud infrastructure

## Data Management Integration

ExecutionWare supports different data management backends:

#### Local ExecutionWare:
   - **Local Files**: Traditional filesystem-based storage

#### Proactive ExecutionWare:
   - **Local Files**: Traditional filesystem-based storage
   - **Zenoh DDM**: Distributed data management for cloud and cluster environments
   - **Hybrid Approaches**: Combination of local and distributed storage

The workflow DSL automatically handles the appropriate data management configuration based on the ExecutionWare type and configuration settings.

## Configuration

ExecutionWare behavior is controlled through configuration files:

- **Local**: `variables.json`, `execution_engine_mapping.json`
- **Proactive**: Runtime configuration files with execution engine metadata

## Next Steps

Each ExecutionWare provides a set of helper functions that tasks use to interact with the execution environment:

- **[Local Helper](local.md)**: Learn how to use local execution helper functions for development and testing.
- **[Proactive Helper](proactive.md)**: Learn how to use proactive helper functions for production deployments.