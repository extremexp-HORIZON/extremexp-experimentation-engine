# Local ExecutionWare

Local ExecutionWare provides a simple, filesystem-based execution environment for workflows running on a single machine. It's ideal for development, testing, and small-scale experiments where distributed computing is not required.

## Overview

Local ExecutionWare uses the local filesystem to store intermediate data between tasks and manages data flow through pickle serialization. It provides a straightforward development environment where you can easily debug and test workflows.

## Helper Functions

Import the utilities in your tasks:
```python
from eexp_engine_utils import utils
```

!!! info "Universal Interface"
    The `utils` module automatically detects the ExecutionWare backend and routes function calls appropriately. The same import works for Local, Proactive, and Kubeflow ExecutionWare.

### Data Loading Functions

#### load_dataset()
Load a dataset:
```python
# Load single dataset
dataset = utils.load_dataset(variables, resultMap, "dataset_key")
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping object (not used in Local, but required for API compatibility)
- `key`: Data key to load

**Returns:**

- Dataset content

### Data Saving Functions

#### save_dataset()
Save a dataset:
```python
# Save dataset
utils.save_dataset(variables, resultMap, "output_key", processed_data)
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `resultMap`: Result mapping object (not used in Local, but required for API compatibility)
- `key`: Data key for saving
- `value`: Data to save

**Behavior:**

- Saves the dataset using pickle serialization
- Updates the internal variables mapping
- Creates intermediate_files directory structure as needed

### Additional Helper Functions

#### get_experiment_results()
Retrieve results from previous experiment runs:
```python
results = utils.get_experiment_results()
```

**Returns:**
- Experiment results dictionary

#### load_dataset_by_path()
Load data directly from a file path:
```python
data = utils.load_dataset_by_path("/path/to/file.csv")
```

**Parameters:**
- `path`: Absolute file path

**Returns:**
- File content

## Task Implementation Example

Here's a complete example of a task using Local ExecutionWare:

```python
import os
import sys
from eexp_engine_utils import utils
import pandas as pd
from sklearn.model_selection import train_test_split

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load input data
print("Loading dataset...")
dataset = utils.load_dataset(variables, resultMap, "dataset")

# Process the data
print("Splitting dataset...")
train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=42)

# Save output data
print("Saving results...")
utils.save_dataset(variables, resultMap, "train_data", train_data)
utils.save_dataset(variables, resultMap, "test_data", test_data)

print("Task completed successfully!")
```

## Data Flow Between Tasks

1. **First Task**: Saves data using `utils.save_dataset()`
2. **Process ID**: Each task gets a unique process ID
3. **Intermediate Storage**: Data stored in `intermediate_files/process_id/`
4. **Next Task**: Loads data using `utils.load_dataset()`
5. **Mapping**: Uses internal mapping to resolve data keys between tasks
   > The engine automatically manages intermediate file paths and cleanup

## Limitations

- **Single Machine**: Only runs on one machine
- **Memory Constraints**: Limited by available RAM
- **No Distributed Storage**: Files stored locally only
- **Process Dependencies**: Sequential execution only
- **No Fault Tolerance**: No automatic recovery from failures

For distributed computing and advanced features, consider using [Proactive ExecutionWare](proactive.md).