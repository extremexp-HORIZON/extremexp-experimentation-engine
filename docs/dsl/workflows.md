# Workflows

Workflows in ExtremeXP define the structure and execution flow of computational tasks. A workflow consists of task definitions, data flow connections, and execution order specifications. Workflows can be inherited and specialized to create variants with different implementations while maintaining the same structure.

The workflow DSL provides a structured way to:

- Define task execution order and dependencies
- Configure task implementations and external dependencies
- Set up data flow between tasks and external files
- Create workflow variants through inheritance
- Specify input and output data paths

## Key Concepts

- **Linear Execution**: Tasks execute in the order defined by the flow specification
- **Task Implementation**: Each task references a specific implementation class
- **Dependency Management**: Tasks can specify external file dependencies using glob patterns
- **Data Flow**: Explicit connections between task inputs/outputs and workflow data
- **Workflow Inheritance**: The `from` keyword allows workflows to inherit structure and behavior from base workflows
- **Task Override**: Derived workflows can override specific task implementations while maintaining the same execution flow
- **Implementation Variants**: Different implementations of the same task can be swapped to create workflow variants for testing or different use cases
- **Flexible Data Paths**: Input and output data can be configured to use different file paths

## Basic Workflow Structure

```dsl
workflow DemoWP5Workflow {
  START -> Task1 -> Task2 -> END;

  task Task1 {
    implementation "demo_tasks/DemoWP5Task1";
  }

  task Task2;

  define input data InputFile;
  define output data OutputFile;

  configure data InputFile {
    path "demo_datasets/titanic.json";
  }

  configure data OutputFile {
    path "output/test_local/titanic_once_more.json";
  }

  InputFile --> Task1.DemoWP5Task1InputFile;
  Task1.DemoWP5Task1OutputFile --> Task2.DemoWP5Task2InputFile;
  Task2.DemoWP5Task2OutputFile --> OutputFile;
}
```

## Advanced Workflow Features

### Workflow Inheritance and Specialization
```dsl
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

### Task-Only Workflows
```dsl
workflow UserInteraction {
  START -> Task1 -> Task2 -> Task3 -> END;

  task Task1 {
    implementation "Task1";
  }

  task Task2 {
    implementation "Task2";
  }

  task Task3 {
    implementation "Task3";
  }
}

workflow AssembledUserInteraction from UserInteraction {
  // Inherits all tasks without modifications
}
```

## Workflow Structure Breakdown

### 1. Workflow Declaration
```dsl
workflow DemoWP5Workflow {
```
Defines a workflow named `DemoWP5Workflow`. All workflow components are enclosed within the curly braces.

### 2. Task Execution Flow

#### Linear Execution
```dsl
START -> Task1 -> Task2 -> END;
```
Defines the execution order of tasks. The workflow starts at `START`, executes `Task1`, then `Task2`, and ends at `END`. This creates a linear execution pipeline.

#### Conditional Execution
```dsl
Task1 ?-> "check_task1_result" ? Task2 : Task3 -> Task4;
```
Our DSL also allows the specification of conditional links between tasks via an expression where:

- `check_task1_result` is a condition specified as a Python function in the module linked by the `PYTHON_CONDITIONS` option in `config.py`
- `Task2` is the task to be executed if the condition returns true
- `Task3` is the task to be executed if the condition returns false  
- `Task4` is executed after either `Task2` or `Task3`

This creates a branching execution flow based on dynamic conditions evaluated at runtime.

!!! info "Conditional Task Execution"
    Conditional execution allows workflows to adapt their behavior based on runtime conditions, enabling dynamic workflow paths and decision-making logic within the execution flow.

### 3. Task Definitions

#### Basic Task Definition
```dsl
task Task1 {
  implementation "demo_tasks/DemoWP5Task1";
}

task Task2;
```

- `Task1` is defined with a specific implementation class
- `Task2` is declared without an explicit implementation (uses default or can be overridden in derived workflows)

### 4. Data Definitions
```dsl
define input data InputFile;
define output data OutputFile;
```
Declares the input and output data objects for the workflow:

- `InputFile` - data that enters the workflow
- `OutputFile` - data that exits the workflow

### 5. Data Configuration
```dsl
configure data InputFile {
  path "demo_datasets/titanic.json";
}

configure data OutputFile {
  path "output/test_local/titanic_once_more.json";
}
```
Configures the actual file paths for the data objects:

- `InputFile` reads from the specified path
- `OutputFile` writes to the specified path

!!! note
    For more examples on Data Configuration check out [Github Examples](https://github.com/extremexp-HORIZON/extremexp-experimentation-engine/tree/main/exp_engine/library-experiments/tests/dataset_management)

### 6. Data Flow Connections
```dsl
InputFile --> Task1.DemoWP5Task1InputFile;
Task1.DemoWP5Task1OutputFile --> Task2.DemoWP5Task2InputFile;
Task2.DemoWP5Task2OutputFile --> OutputFile;
```
Defines how data flows between tasks:

- Workflow input connects to Task1's input port
- Task1's output connects to Task2's input port
- Task2's output connects to the workflow output

This creates a complete data processing pipeline where data flows from the input file through both tasks to the output file.

## Workflow Inheritance and Specialization

### 7. Basic Inheritance
```dsl
workflow DemoWP5AssembledWorkflow1 from DemoWP5Workflow {
  task Task2 {
    implementation "demo_tasks/DemoWP5Task2V1";
  }
}
```
Creates a specialized workflow that inherits from `DemoWP5Workflow` and overrides:

- `Task2` implementation is changed to `DemoWP5Task2V1`
- All other aspects (data flow, configurations) remain the same as the base workflow

### 8. Multiple Variants
```dsl
workflow DemoWP5AssembledWorkflow2 from DemoWP5Workflow {
  task Task2 {
    implementation "demo_tasks/DemoWP5Task2V2";
  }
}
```
Creates another specialized workflow that inherits from `DemoWP5Workflow` and overrides:

- `Task2` implementation is changed to `DemoWP5Task2V2`
- This demonstrates how multiple variants can be created from the same base workflow

### 9. Empty Inheritance
```dsl
workflow AssembledUserInteraction from UserInteraction {
  // Inherits all tasks and configurations without modifications
}
```
Creates an assembled workflow that inherits everything from the base workflow without any overrides.

!!! note "Workflow Variants"
    Workflow inheritance is particularly useful for creating different versions of the same workflow with alternative task implementations, allowing for A/B testing or different algorithmic approaches.

!!! info "Task Naming Convention"
    Task input and output ports follow the naming convention `TaskName.TaskNameInputFile` and `TaskName.TaskNameOutputFile`, making data flow connections