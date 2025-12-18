# Migration Guide

This guide helps you migrate your ExtremeXP experiments from versions **0.0.41 and earlier** to **version 0.0.42+**.

## Overview of Changes

Starting from version 0.0.42, the ExtremeXP Experimentation Engine introduces several improvements:

- **Unified utility imports**: Single import for all helper functions across different executionwares
- **Workflow library organization**: Cleaner separation of workflow definitions and experiment definitions
- **Simplified module management**: Automatic module path handling
- **Consistent API**: Same helper functions work across all executionwares (ProActive/Kubeflow) and dataset managers (Local/DDM)

---

## Step 1: Configure Workflow Library Path

Add the `WORKFLOW_LIBRARY_PATH` configuration to your `eexp_config.py`:

```python
# eexp_config.py

WORKFLOW_LIBRARY_PATH = "path/to/your/workflows/directory"
```

This tells the Experimentation Engine where to find your workflow definition files.

**Example:**
```python
WORKFLOW_LIBRARY_PATH = "workflows"  # If workflows are in a 'workflows' folder
```

---

## Step 2: Separate Workflow and Experiment Definitions

Previously, workflow definitions and experiment definitions were combined in a single file. Now they should be separated for better organization.

### 2.1 Before (Single File)

Previously, you might have had everything in one file:

```xxp
# experiments/demo_wp5.xxp

workflow DemoWP5Workflow {

    START -> Task1 -> Task2 -> END;

    task Task1 {
        implementation "demo_tasks/DemoWP5Task1";
    }

    task Task2;

    define input data InputFile;
    configure data InputFile {
        path "demo_datasets/titanic.csv";
    }

    define output data OutputFile;
    configure data OutputFile {
        path "output/test_local/titanic_once_more.csv";
    }

    InputFile --> Task1.DemoWP5Task1InputFile;
    Task1.DemoWP5Task1OutputFile --> Task2.DemoWP5Task2InputFile;
    Task2.DemoWP5Task2OutputFile --> OutputFile;
}

workflow DemoWP5AssembledWorkflow1 from DemoWP5Workflow {
    task Task2 {
        implementation "demo_tasks/DemoWP5Task2V1";
    }
}

workflow DemoWP5AssembledWorkflow2 from DemoWP5Workflow {
    task Task2 {
        implementation "demo_tasks/DemoWP5Task2V2";
    }
}

experiment DemoWP5Experiment {

    control {
          START -> S2 -> END;
    }

    space S1 of DemoWP5AssembledWorkflow1 {
        strategy gridsearch;
        param_values demo_param_value = range(4, 6);
        task Task1 {
            param demo_param = demo_param_value;
        }
    }

    space S2 of DemoWP5AssembledWorkflow2 {
        strategy randomsearch;
        runs = 1;
        param_values demo_param_value = enum(6);
        task Task1 {
            param demo_param = demo_param_value;
        }
    }
}
```

### 2.2 After: Workflow Definition File

Create a workflow definition file in your configured workflow library directory:

```xxp
# workflows/demo_wp5.xxp

workflow DemoWP5Workflow {

    START -> Task1 -> Task2 -> END;

    task Task1 {
        implementation "demo_tasks/DemoWP5Task1";
    }

    task Task2;

    define input data InputFile;
    configure data InputFile {
        path "demo_datasets/titanic.csv";
    }

    define output data OutputFile;
    configure data OutputFile {
        path "output/test_local/titanic_once_more.csv";
    }

    InputFile --> Task1.DemoWP5Task1InputFile;
    Task1.DemoWP5Task1OutputFile --> Task2.DemoWP5Task2InputFile;
    Task2.DemoWP5Task2OutputFile --> OutputFile;
}

workflow DemoWP5AssembledWorkflow1 from DemoWP5Workflow {
    task Task2 {
        implementation "demo_tasks/DemoWP5Task2V1";
    }
}

workflow DemoWP5AssembledWorkflow2 from DemoWP5Workflow {
    task Task2 {
        implementation "demo_tasks/DemoWP5Task2V2";
    }
}
```

### 2.3 After: Experiment Definition File

Create a separate experiment file that imports the workflow definitions:

```xxp
# experiments/demo_wp5.xxp

import "demo_wp5.xxp";

experiment DemoWP5Experiment {

    control {
          START -> S2 -> END;
    }

    space S1 of DemoWP5AssembledWorkflow1 {
        strategy gridsearch;
        param_values demo_param_value = range(4, 6);
        task Task1 {
            param demo_param = demo_param_value;
        }
    }

    space S2 of DemoWP5AssembledWorkflow2 {
        strategy randomsearch;
        runs = 1;
        param_values demo_param_value = enum(6);
        task Task1 {
            param demo_param = demo_param_value;
        }
    }
}
```

!!! info "Import Path"
    Notice the import statement `import "demo_wp5.xxp";` uses just the filename. This is because the file is located in the workflow library directory configured in `WORKFLOW_LIBRARY_PATH`.

---

## Step 3: Remove Manual Module Path Configuration

Previously, you needed to manually add module paths in your Python task implementations:

### Before

```python
# Remove these lines from your task implementation files:
[sys.path.append(os.path.join(os.getcwd(), folder))
 for folder in variables.get("dependent_modules_folders").split(",")]
```

### After

**Simply remove these lines.** The Experimentation Engine now handles module paths automatically.

---

## Step 4: Update Helper Function Imports

The import mechanism for helper functions has been unified across all executionwares and dataset managers.

### Before

Previously, you had to import different utilities depending on your executionware:

```python
# For ProActive
from eexp_engine_utils.utilities import proactive_utils as utils

# For Kubeflow
from eexp_engine_utils.utilities import kubeflow_utils as utils

# For Local
from eexp_engine_utils.utilities import local_utils as utils
```

### After

Now use a single unified import:

```python
from eexp_engine_utils import utils
```

The Experimentation Engine automatically selects the correct implementation based on your configuration.

### Usage Remains the Same

All your existing helper function calls work exactly as before:

```python
# Save datasets
utils.save_dataset(variables, resultMap, "output_key", data)

# Load datasets
data = utils.load_dataset(variables, resultMap, "input_key")

# Save multiple datasets
utils.save_datasets(variables, resultMap, "output_key", [data1, data2])

# Load multiple datasets
datasets = utils.load_datasets(variables, resultMap, "input_key")
```

---

## Complete Example

Here's a complete example showing the migration of a task implementation:

### Before

```python
import sys
import os

# Manual module path setup (REMOVE THIS)
[sys.path.append(os.path.join(os.getcwd(), folder))
 for folder in variables.get("dependent_modules_folders").split(",")]

# Executionware-specific import (REPLACE THIS)
from eexp_engine_utils.utilities import proactive_utils as utils

def demo_task(variables, resultMap):
    # Load input data
    input_data = utils.load_dataset(variables, resultMap, "input")

    # Process data
    result = process_data(input_data)

    # Save output
    utils.save_dataset(variables, resultMap, "output", result)
```

### After

```python
# Unified import (NEW)
from eexp_engine_utils import utils

def demo_task(variables, resultMap):
    # Load input data
    input_data = utils.load_dataset(variables, resultMap, "input")

    # Process data
    result = process_data(input_data)

    # Save output
    utils.save_dataset(variables, resultMap, "output", result)
```
