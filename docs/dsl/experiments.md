# Experiments

Experiments in ExtremeXP allow you to define and execute parameter exploration studies across multiple workflow variants. An experiment consists of one or more experimental spaces, each containing a workflow with specific parameter configurations and exploration strategies.

The experiment DSL provides a structured way to:

- Define sequential, parallel, or conditional execution of experimental spaces
- Configure different parameter exploration strategies (grid search, random search)
- Apply parameter variations to specific tasks within workflows
- Control the number of runs and parameter value ranges
- Add custom configuration filters and generators
- Include experiment-level tasks and user interactions
- Set up conditional control flow based on experiment results

## Key Concepts

- **Control Flow Flexibility**: Support for sequential, parallel, and conditional execution patterns
- **Parameter Exploration**: Multiple strategies for exploring parameter spaces
- **Configuration Management**: Filtering and generation of parameter combinations
- **Interactive Experiments**: Integration of user interactions and experiment-level tasks
- **Conditional Logic**: Dynamic experiment flow based on results and conditions
- **External Functions**: Integration with Python functions for conditions, filters, and generators

## Basic Experiment Structure

```dsl
experiment DemoWP5Experiment {
  control {
    START -> S1 -> S2 -> END;
  }

  space S1 of AssembledWorkflow1 {
    strategy gridsearch;
    param_values demo_param_value = range(4, 6);
    task Task1 {
      param demo_param = demo_param_value;
    }
  }

  space S2 of AssembledWorkflow2 {
    strategy randomsearch;
    runs = 1;
    param_values demo_param_value = enum(6);
    task Task1 {
      param demo_param = demo_param_value;
    }
  }
}
```

## Advanced Experiment Features

### Parallel Execution
```dsl
experiment ParallelExperiment {
  control {
    START -> (S1 || S2) -> END;
  }
  
  space S1 of WorkflowA {
    strategy gridsearch;
    param_values param1_vp = enum(2, 5, 1);
    task Task1 {
      param param1 = param1_vp;
    }
  }
  
  space S2 of WorkflowB {
    strategy gridsearch;
    param_values param1_vp = range(3, 6);
    task Task1 {
      param param1 = param1_vp;
    }
  }
}
```

### Conditional Control Flow
```dsl
experiment ConditionalExperiment {
  control {
    S1 ?-> S2 { condition "check_results_less_than 100" };
    S2 -> T1;
  }
  
  space S1 of WorkflowA {
    strategy randomsearch;
    runs = 1;
    param_values param1_vp = enum(2, 5, 7);
    task Task1 {
      param param1 = param1_vp;
    }
  }
  
  space S2 of WorkflowB {
    strategy gridsearch;
    param_values param1_vp = range(3, 4);
    task Task1 {
      param param1 = param1_vp;
    }
  }
  
  task T1 {
    implementation "ExpTask1";
    input data T1InputFile {
      path "tests/dummy.txt";
    }
  }
}
```

### Configuration Validation
```dsl
experiment ValidationExperiment {
  control {
    S1 -> S2 -> END;
  }
  
  space S2 of WorkflowB {
    strategy gridsearch;
    param_values param1_vp = range(3, 5);
    param_values param1_vp = enum(5, 6);
    filter "configuration_filter_S2";
    generator "configuration_generator_S2";
    task Task1 {
      param param1 = param1_vp;
    }
  }
}
```

### User Interactions
```dsl
experiment InteractiveExperiment {
  control {
    START -> S1 -> I1 -> END;
  }
  
  space S1 of WorkflowA {
    strategy randomsearch;
    runs = 1;
    param_values param1_vp = enum(2, 5, 7);
    task Task1 {
      param param1 = param1_vp;
    }
  }
  
  interaction I1 {
    implementation "ExpInteraction1";
  }
}
```

## Experiment Structure Breakdown

### 1. Experiment Declaration
```dsl
experiment DemoWP5Experiment {
  intent testComplexControl;
```

- Defines an experiment with a name
- Optional `intent` declaration specifies the experiment's purpose

### 2. Control Flow Options

#### Sequential Execution
```dsl
control {
  START -> S1 -> S2 -> END;
}
```
Executes experimental spaces in sequence.

#### Parallel Execution
```dsl
control {
  START -> (S1 || S2) -> END;
}
```
Executes experimental spaces in parallel using `||` operator.

#### Conditional Execution
```dsl
control {
  S1 ?-> S2 { condition "check_results_less_than 100" };
}
```

- Uses `?->` for conditional transitions
- Conditions reference external Python functions
- Transitions occur only if condition evaluates to true

### 3. Experimental Spaces

#### Basic Space Configuration
```dsl
space S1 of AssembledWorkflow1 {
  strategy gridsearch;
  param_values demo_param_value = range(4, 6);
  task Task1 {
    param demo_param = demo_param_value;
  }
}
```

#### Advanced Space Configuration
```dsl
space S2 of AssembledWorkflow2 {
  strategy randomsearch;
  runs = 1;
  param_values param1_vp = range(3, 5);
  param_values param1_vp = enum(5, 6);
  filter "configuration_filter_S2";
  generator "configuration_generator_S2";
  task Task1 {
    param param1 = param1_vp;
  }
}
```

**Space Configuration Options:**

- `strategy`: `gridsearch` or `randomsearch`
- `runs`: Number of runs for random search
- `param_values`: Parameter definitions using `range()` or `enum()`
- `filter`: Python function to filter parameter combinations
- `generator`: Python function to generate additional configurations

### 4. Parameter Value Functions

- #### Range Parameters
    ```dsl
    param_values demo_param_value = range(4, 6);
    ```
    Generates continuous values from 4 to 6.

    ```dsl
    param_values demo_param_value = range(4, 6, 2);
    ```
    Generates values from 4 to 6 with a step size of 2. This would produce values: 4, 6.

- #### Enumerated Parameters
    ```dsl
    param_values param1_vp = enum(2, 5, 7);
    ```
    Creates discrete parameter values: 2, 5, and 7.

### 5. Experiment-Level Tasks
```dsl
task T1 {
  implementation "ExpTask1";
  input data T1InputFile {
    path "tests/dummy.txt";
  }
}
```
Tasks that execute as part of the experiment control flow, separate from workflow spaces.

### 6. User Interactions
```dsl
interaction I1 {
  implementation "ExpInteraction1";
}
```
Interactive elements that can be integrated into the experiment control flow.

!!! info "External Function Integration"
    Experiments can reference external Python functions for conditions, configuration filters, and generators. These functions should be defined in separate Python files and imported into the experiment execution environment inside the `tasks` directory.

!!! note "Parallel vs Sequential Execution"
    Use parallel execution (`||`) when experimental spaces are independent and can run simultaneously. Use sequential execution (`->`) when spaces depend on each other's results or when resource constraints require ordered excecution.