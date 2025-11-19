# Tasks

Tasks in ExtremeXP are the fundamental building blocks of workflows. Each task represents a single computational unit with defined inputs, outputs, parameters, and execution environment specifications. Tasks can be configured with various options including implementation details, dependencies, virtual environments, and parameter definitions.

The task DSL provides a structured way to:

- Define input and output data ports
- Configure task parameters with types, defaults, and ranges
- Specify implementation files and dependencies
- Set up virtual environments and Python versions
- Define task types for categorization
- Configure execution requirements

## Basic Task Structure

```dsl
task read_data {
    define input data FileToRead;
    define output data dataset;

    implementation "UC2/read_data/read_data.py";
    dependency "UC2_src/**";
    venv "UC2/read_data/requirements.txt";
    python_version "3.9";
}
```

## Advanced Task Features

### Task with Multiple Inputs and Outputs
```dsl
task split_dataset {
    define input data dataset;

    define output data train_data;
    define output data test_data;

    implementation "UC2/split_dataset/split_dataset.py";
    dependency "UC2_src/**";
    venv "UC2/split_dataset/requirements.txt";
    python_version "3.9";
}
```

### Task with Parameters
```dsl
task train_model {
    define input data train_data;
    define input data test_data;
    
    define output data model;
    define output data train_data;
    define output data test_data;

    define param max_depth {
        type Integer;
        default 3;
        range (3, 30);
    }

    define param n_estimators {
        type Integer;
        default 5;
        range (5, 50);
    }

    define param min_child_weight {
        type Integer;
        default 1;
        range (1, 10);
    }

    define param gamma {
        type Integer;
        default 0;
        range (1, 5);
    }

    implementation "UC2/train_model/train_model.py";
    dependency "UC2_src/**";
    venv "UC2/train_model/requirements.txt";
    python_version "3.9";
}
```

### Task with Type Classification
```dsl
task Explainability {
    type explainability;

    define input data train_data;
    define input data test_data;
    define input data trained_model;
    
    define output data mlAnalysis;

    implementation "UC2/Explainability/task.py";
    dependency "UC2_src/**";
    venv "UC2/Explainability/requirements.txt";
    python_version "3.9";
}
```

### Minimal Task Structure
```dsl
task benchmarking {
    define input data ExternalDataFile;
    
    implementation "I2CAT/benchmarking/benchmarking.py";
    dependency "I2CAT/**";
}
```

## Task Structure Breakdown

### 1. Task Declaration
```dsl
task read_data {
```
Defines a task named `read_data`. All task components are enclosed within the curly braces.

### 2. Task Type (Optional)
```dsl
type explainability;
```
Specifies the task type for categorization purposes. This is optional and helps organize tasks by functionality.

### 3. Data Port Definitions

#### Input Data Ports
```dsl
define input data FileToRead;
define input data train_data;
define input data test_data;
```
Declares input data ports that the task expects to receive:

- `FileToRead` - a single input file
- `train_data` - training dataset
- `test_data` - testing dataset

#### Output Data Ports
```dsl
define output data dataset;
define output data train_data;
define output data test_data;
define output data model;
```
Declares output data ports that the task will produce:

- `dataset` - processed dataset
- `train_data` - training data subset
- `test_data` - testing data subset
- `model` - trained machine learning model

### 4. Parameter Definitions
```dsl
define param max_depth {
    type Integer;
    default 3;
    range (3, 30);
}

define param n_estimators {
    type Integer;
    default 5;
    range (5, 50);
}
```
Defines configurable parameters for the task:

- `type` - parameter data type (Integer, Float, String, Boolean)
- `default` - default value if not specified
- `range` - valid range for parameter values (used in parameter exploration)

### 5. Implementation Configuration
```dsl
implementation "UC2/read_data/read_data.py";
```
Specifies the Python file that contains the task implementation.

### 6. Dependencies
```dsl
dependency "UC2_src/**";
dependency "I2CAT/**";
```
Defines external dependencies using glob patterns:

- `UC2_src/**` - all files in the UC2_src directory and subdirectories
- `I2CAT/**` - all files in the I2CAT directory and subdirectories

!!! note "Usage Example"
    - Glob patterns (`demoHelper/**`, `helpers/*.py`)
    - Specific files (`config/settings.json`)

!!! info "Task Dependencies"
    The `dependency` keyword allows tasks to specify external files or resources they need during execution. Dependencies use glob patterns to match files and directories.

### 7. Virtual Environment Configuration
```dsl
venv "UC2/read_data/requirements.txt";
python_version "3.9";
```
Configures the execution environment:

- `venv` - path to requirements.txt file for virtual environment setup
- `python_version` - specific Python version to use

!!! warning
    If you want to use `venv` in your task DSL file then the `python_version` field is mandatory.
    `python_version` should also be specified as an option in the [configuration file](../config.md#configuration-file-structure)

## Task Examples by Use Case

### Data Processing Task
```dsl
task read_data {
    define input data FileToRead;
    define output data dataset;

    implementation "UC2/read_data/read_data.py";
    dependency "UC2_src/**";
    venv "UC2/read_data/requirements.txt";
    python_version "3.9";
}
```
A simple data processing task that reads a file and outputs a processed dataset.

### Data Transformation Task
```dsl
task split_dataset {
    define input data dataset;

    define output data train_data;
    define output data test_data;

    implementation "UC2/split_dataset/split_dataset.py";
    dependency "UC2_src/**";
    venv "UC2/split_dataset/requirements.txt";
    python_version "3.9";
}
```
A transformation task that splits a dataset into training and testing subsets.

### Machine Learning Task
```dsl
task train_model {
    define input data train_data;
    define input data test_data;
    
    define output data model;
    define output data train_data;
    define output data test_data;

    define param max_depth {
        type Integer;
        default 3;
        range (3, 30);
    }

    define param n_estimators {
        type Integer;
        default 5;
        range (5, 50);
    }

    implementation "UC2/train_model/train_model.py";
    dependency "UC2_src/**";
    venv "UC2/train_model/requirements.txt";
    python_version "3.9";
}
```
A machine learning task with multiple configurable parameters for model training.

### Analysis Task
```dsl
task Explainability {
    type explainability;

    define input data train_data;
    define input data test_data;
    define input data trained_model;
    
    define output data mlAnalysis;

    implementation "UC2/Explainability/task.py";
    dependency "UC2_src/**";
    venv "UC2/Explainability/requirements.txt";
    python_version "3.9";
}
```
An analysis task that performs explainability analysis on trained models.

### Benchmarking Task
```dsl
task benchmarking {
    define input data ExternalDataFile;
    
    implementation "I2CAT/benchmarking/benchmarking.py";
    dependency "I2CAT/**";
}
```
A minimal benchmarking task without virtual environment configuration.

## Parameter Types and Configuration

### Integer Parameters
```dsl
define param max_depth {
    type Integer;
    default 3;
    range (3, 30);
}
```

### Parameter Configuration Options

- **type**: Specifies the parameter data type
  - `Integer` - whole numbers
  - `Float` - decimal numbers
  - `String` - text values
  - `Boolean` - true/false values
- **default**: Default value used when parameter is not specified
- **range**: Valid range for parameter values, used in parameter exploration experiments

## Key Concepts

- **Data Ports**: Input and output data connections that enable data flow between tasks
- **Parameters**: Configurable values that modify task behavior and can be explored in experiments
- **Implementation**: Python file containing the actual task execution logic
- **Dependencies**: External files and directories required for task execution
- **Virtual Environment**: Isolated Python environment with specific package requirements
- **Task Types**: Optional categorization for organizing tasks by functionality

!!! info "Task Parameters in Experiments"
    Task parameters defined with `range` specifications can be automatically explored in experiments using different parameter exploration strategies like grid search or random search.

!!! note "Virtual Environment Best Practices"
    Each task can have its own virtual environment with specific package requirements, ensuring isolation and reproducibility across different computational environments.

!!! tip "Dependency Management"
    Use glob patterns for dependencies to automatically include all necessary files and subdirectories, ensuring tasks have access to all required resources.