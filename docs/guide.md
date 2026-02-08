# User Guide

This guide provides a step-by-step walkthrough for using the **ExpEngine** within the **ExtremeXP** framework.  
It uses a simple demo experiment to illustrate all steps.

## Video tutorial 
The user guide is also available in the form of the following video tutorial: 

[![Watch the video](https://img.youtube.com/vi/2yUChB5ZOvk/0.jpg)](https://www.youtube.com/watch?v=2yUChB5ZOvk)

## Prerequisites

- **Python** (>= 3.10)
- **Java** version 11 or 13 (required for Proactive as executionware)

!!! warning "Note"
      This guide has been tested on Unix-based systems. Windows usage is possible with minimal adjustments (e.g., virtual environment activation and path separators).

---

## Step 1 — Set up your development environment

1. Open a terminal and navigate to your project directory.

      ```bash
      cd /root/directory/of/your/project
      ```

2. Create a Python virtual environment:

      ```bash
      python -m venv <environment_name>
      ```
      > Replace `<environment_name>` with something like `env`.

3. Activate the environment:

    === "Unix/macOS"
        ```bash
        source <environment_name>/bin/activate
        ```

    === "Windows"
        ```cmd
        .\<environment_name>\Scripts\activate
        ```

4. Install the `eexp_engine` package:

      ```bash
      pip install eexp_engine
      ```

      To upgrade to the latest version later:

      ```bash
      pip install eexp_engine --upgrade
      ```

---

## Step 2 — Configure your project

Next, you'll create a configuration file and define:

- Main directories
- Helper modules
- Execution settings
- Data management
- Logging

---

1. Create the configuration file in the root folder:

      ```bash
      touch eexp_config.py
      ```

2. Create a directory structure following this layout:

      ```text
      .
      ├── experiments/
      ├── workflows/
      ├── datasets/
      ├── tasks/
      └── dependencies/
      ```

3. Edit `eexp_config.py`:
      - For detailed information, see the [Configuration](config.md) page

---

## Step 3 — Create your Workflow

1. From the root directory navigate to the experiments directory:

      ```bash
      cd workflows
      ```

2. Create a *demo* experiment:

      ```bash
      touch demo-workflow.xxp
      ```
   > All DSL files should have `.xxp` format. 

3. Edit `demo-workflow.xxp` file with the following content:

    ??? info "example"
        ```dsl
        workflow DemoWorkflow {
            START -> Task1 -> Task2 -> END;

        task Task1 {
            implementation "demo/task1";
        }

        task Task2;

        define input data InputFile;
        define output data OutputFile;

        configure data InputFile {
            path "demo/test.json";
        }

        configure data OutputFile {
            path "output/test_local/test_output.json";
        }

        InputFile --> Task1.Task1InputFile;
        Task1.Task1OutputFile --> Task2.Task2InputFile;
        Task2.Task2OutputFile --> OutputFile;
        }

        workflow AssembledWorkflow1 from DemoWorkflow {
            task Task2 {
                  implementation "demo/task2V1";
            }
        }

        workflow AssembledWorkflow2 from DemoWorkflow {
            task Task2 {
                  implementation "demo/task2V2";
            }
        }
        ```
      For detailed information about the DSL syntax and available options, see the [Experiment](dsl/experiments.md) & [Workflow](dsl/workflows.md) DSL page

## Step 4 — Create your experiment

1. From the root directory navigate to the experiments directory:

      ```bash
      cd experiments
      ```

2. Create a *demo* experiment:

      ```bash
      touch demo-experiment.xxp
      ```
   > All DSL files should have `.xxp` format. 

3. Edit `demo-experiment.xxp` file with the following content:

    ??? info "example"
        ```dsl
        import "demo-workflow.xxp";

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
      For detailed information about the DSL syntax and available options, see the [Experiment](dsl/experiments.md) & [Workflow](dsl/workflows.md) DSL page


## Step 5 — Create your dataset

1. From the root directory navigate to the datasets directory:

      ```bash
      cd datasets
      ```

2. Create a directory for the demo experiment:

      ```bash
      mkdir demo
      ```

3. Create the test dataset file:

      ```bash
      cd demo
      touch test.json
      ```

4. Edit `test.json` with your dataset content:

      ```json
      {
        "test_data": "your_data_here"
      }
      ```

---


## Step 6 - Create Task Specifications

In the `demo-workflow.xxp` we defined two Tasks inside the workflow block *(Task1, Task2)*.
Next up we are going to create and edit the corresponding `<task>.xxp` files for these two Tasks.

1. From the root directory navigate to the *tasks* directory:

      ```bash
      cd tasks
      ```

2. Create `.xxp` files following this layout:

      ```text
      tasks
      │──── demo
            ├── task1/
            │   ├── task.xxp
            ├── task2V1/
            │   ├── task.xxp
            └── task2V2/
                  ├── task.xxp
      ```
    

3. Edit the files with the following examples:

    ??? info "task1 xxp file"

           ```dsl
            task Task1 {
        
            define input data Task1InputFile;
            define output data Task1OutputFile;
        
            define param demo_param {
                type Integer;
                default 10;
                range (4, 20, 2);
            }
        
            define metric ParamIncreasedBy5 {
                kind single-value;
                type Integer;
            }
        
            implementation "demo/Task1/task1.py";
            python_version "3.9";
            }
           ```
    ??? info "task2V1 xxp file"

           ```dsl
            task Task2V1 {

            define input data Task2InputFile;
            define output data Task2OutputFile;

            implementation "demo/task2V1/task2V1.py";
            python_version "3.9";
            }
           ```
    ??? info "task2V2 xxp file"

           ```dsl
            task Task2V2 {

            define input data Task2InputFile;
            define output data Task2OutputFile;

            implementation "demo/task2V2/task2V2.py";
            python_version "3.9";
            }
           ```

      For comprehensive documentation on task DSL syntax and configuration options, refer to the [Task](dsl/tasks.md) DSL page.

## Step 6 — Provide Task Implementations

1. From the root directory navigate to the *tasks* directory:

      ```bash
      cd tasks
      ```

2. Create `.py` files following this layout:

      ```text
      tasks
      │──── demo
            ├── task1/
            │   ├── task.xxp
            │   └── task1.py
            ├── task2V1/
            │   ├── task.xxp
            │   └── task2V1.py
            └── task2V2/
                  ├── task.xxp
                  └── task2V2.py
      ```

3. Edit the `task.py` files for each task we created with the following examples.

    ??? info "task1.py file"
        ```py
        import os
        import sys

        # Import the utilities - automatically routes to correct backend (Proactive, Kubeflow, or Local)
        from eexp_engine_utils import utils

        print("Running DemoWP5Task1")

        # For Proactive/Kubeflow, pass both variables and resultMap
        # For Local, only variables is needed
        dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task1InputFile")

        demo_param = variables.get("demo_param")
        print(f"with value of demo_param: {demo_param}")

        increment = 5
        metric_name = "ParamIncreasedBy5"

        print(f"Increasing this parameter by {increment} and adding the result to the metric {metric_name}")
        resultMap.put(metric_name, int(demo_param) + increment)

        utils.save_dataset(variables, resultMap, "DemoWP5Task1OutputFile", dataset)
        ```

    ??? info "task2V1.py file"
        ```py
        import os
        import sys

        from eexp_engine_utils import utils

        print("Running DemoWP5Task2V1")

        dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task2InputFile")

        utils.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset)
        ```

    ??? info "task2V2.py file"
        ```py
        import os
        import sys

        from eexp_engine_utils import utils

        print("Running DemoWP5Task2V2")

        dataset = utils.load_dataset(variables, resultMap, "DemoWP5Task2InputFile")

        utils.save_dataset(variables, resultMap, "DemoWP5Task2OutputFile", dataset)
        ```

      <!-- - [task1.py](examples.md#task1py)
      - [task2V1.py](examples.md#task2v1py)
      - [task2V2.py](examples.md#task2v2py) -->

    For comprehensive documentation on task implementation depending on your ExecutionWare option, refer to the [ExecutionWare](executionware/overview.md) section.

    !!! note

        Each task directory should include a `.xxp` file (DSL configuration) and a `.py` file (Task Code)

## Step 7 - Run the experiment

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

Create a Python script (e.g., `run_experiment.py`) in your project root:

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
    experiment_name = "path/to/demo-experiment"

    client.run(__file__, experiment_name, eexp_config)
```

Then execute:

```bash
python run_experiment.py
```
