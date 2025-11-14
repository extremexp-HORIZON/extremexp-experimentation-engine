# Local ExecutionWare

Local ExecutionWare provides a simple, filesystem-based execution environment for workflows running on a single machine. It's ideal for development, testing, and small-scale experiments where distributed computing is not required.

## Overview

Local ExecutionWare uses the local filesystem to store intermediate data between tasks and manages data flow through pickle serialization. It provides a straightforward development environment where you can easily debug and test workflows.

## Helper Functions

Import the local helper module in your tasks:
```python
import local_helper as lh
```

### Data Loading Functions

#### load_datasets()
Load multiple datasets with a single call:
```python
# Load single dataset
dataset = lh.load_datasets(variables, "dataset_key")

# Load multiple datasets
train_data, test_data = lh.load_datasets(variables, "train_data", "test_data")
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `*keys`: Variable number of data keys to load

**Returns:**

- Single dataset if one key provided
- Tuple of datasets if multiple keys provided

#### Internal: _load_dataset()
Loads a single dataset (used internally by `load_datasets`):
```python
data = lh._load_dataset(variables, "data_key")
```

### Data Saving Functions

#### save_datasets()
Save multiple datasets and update variables:
```python
# Save datasets
lh.save_datasets(variables, 
                ("output_key1", processed_data1),
                ("output_key2", processed_data2))
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `*data`: Tuples of (key, value) pairs to save

**Behavior:**

- Saves each dataset using pickle serialization
- Updates the variables.json file with new variables
- Creates intermediate_files directory structure

#### Internal: _save_dataset()
Saves a single dataset (used internally by `save_datasets`):
```python
lh._save_dataset(variables, "output_key", data)
```

### Directory Management

#### create_dir()
Create a directory for intermediate files:
```python
folder_path = lh.create_dir(variables, "subfolder_name")
```

**Parameters:**

- `variables`: Dictionary containing workflow variables
- `key`: Name of the subdirectory to create

**Returns:**
- Path to the created directory

### Result Management

#### save_result()
Save final experiment results:
```python
result = {
    "accuracy": 0.95,
    "f1_score": 0.92,
    "model_params": {"max_depth": 5}
}
lh.save_result(result)
```

**Parameters:**

- `result`: Dictionary containing experiment results

**Behavior:**

- Saves results to `results.json` file
- Uses JSON serialization with NumPy support

## Task Implementation Example

Here's a complete example of a task using Local ExecutionWare:

```python
import os
import sys
import local_helper as lh
import pandas as pd
from sklearn.model_selection import train_test_split

# Add dependent modules to path
for folder in variables.get("dependent_modules_folders").split(","):
    sys.path.append(os.path.join(os.getcwd(), folder))

# Load input data
print("Loading dataset...")
dataset = lh.load_datasets(variables, "dataset")

# Process the data
print("Splitting dataset...")
train_data, test_data = train_test_split(dataset, test_size=0.2, random_state=42)

# Save output data
print("Saving results...")
lh.save_datasets(variables, 
                ("train_data", train_data),
                ("test_data", test_data))

# Save experiment metadata
result = {
    "train_size": len(train_data),
    "test_size": len(test_data),
    "split_ratio": 0.8
}
lh.save_result(result)

print("Task completed successfully!")
```

## Data Flow Between Tasks

1. **First Task**: Saves data using `save_datasets()`
2. **Process ID**: Each task gets a unique process ID
3. **Intermediate Storage**: Data stored in `intermediate_files/process_id/`
4. **Next Task**: Loads data using `load_datasets()`
5. **Mapping**: Uses `execution_engine_mapping.json` to resolve data keys
   > `execution_engine_mapping.json` is an internal file that the engine creates and deletes when needed

## Limitations

- **Single Machine**: Only runs on one machine
- **Memory Constraints**: Limited by available RAM
- **No Distributed Storage**: Files stored locally only
- **Process Dependencies**: Sequential execution only
- **No Fault Tolerance**: No automatic recovery from failures

For distributed computing and advanced features, consider using [Proactive ExecutionWare](proactive.md).