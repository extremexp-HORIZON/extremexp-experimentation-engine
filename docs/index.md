# ExpEngine Documentation

Welcome!  
This site contains the official documentation for the **ExtremeXP ExpEngine** — your tool for specifying and running experiments with a powerful Domain-Specific Language (DSL) and flexible execution backends.

## Overview

The Experimentation Engine (ExpEngine in short) serves as the core component of ExtremeXP’s implementing the Continuous Adaptive Experiment Planning functionality. Its primary responsibility is to execute ExtremeXP experiments by orchestrating and evaluating workflows. It takes the form of a Python module published at [PyPI](https://pypi.org/project/eexp-engine/) .



``` mermaid
classDiagram
  ExcecutionWare <-- ExperimentationEngine:runs on
  ExcecutionWare <|-- LocalExec
  ExcecutionWare <|-- Proactive
  DataManager <-- ExperimentationEngine:uses
  DataManager <|-- LocalStorage
  DataManager <|-- DDM
  DAL <-- ExperimentationEngine:uses
  class ExperimentationEngine{
    dataManager: DataManager
    executionWare: ExcecutionWare
    dal: Dal
  }
  class DataManager{
  }
  class LocalStorage{
  }
  class DDM{
  }
  class ExcecutionWare{
  }
  class LocalExec{
  }
  class Proactive{
  }
  class DAL{
  }
```

Diagram presents the class diagram of the module, illustrating its core internal interfaces and their configurable implementations. In particular, the Experimentation Engine provides three interfaces: 

### 1. DataManager

DataManager handles the retrieval and storage of datasets (files) during experiment execution. Two implementations are currently supported.

- **LocalStorage**: Uses the local file system (of the machine where the experiment is launched) for retrieving and saving datasets. This is useful when using the module as a stand-alone component, i.e., without depending on the Decentralized Data Management (DDM) component of the ExtremeXP framework. 
- **DDM**: Uses the API endpoints of the DDM component of the ExtremeXP framework for retrieving and saving datasets. Internally, DDM uses the Zenoh framework, making it possible to manage datasets distributed over a cluster of machines. This implementation provides more flexibility for accessing datasets generated via workflows from different components of the framework (e.g., from the Experiment Visualization component).

### 2. ExecutionWare 

ExecutionWare handles the scheduling and execution of workflows generated during the execution of an experiment via the Experimentation Engine. Two implementations are currently supported.

- **LocalExec**: Workflows are executed directly on the local machine (where the experiment is launched) as Python processes. This is useful mostly for debugging purposes and offers fewer integration possibilities compared to Proactive.
- **Proactive**: Workflows are transformed into Proactive “jobs” and submitted for execution to Activeeon’s ProActive platform. The Proactive Python client is used for this, which internally connects to ProActive via dedicated endpoints. The Experimentation Engine periodically polls to obtain the status of execution of the submitted workflows.

### 3. DAL (Data Abstraction Layer)

The DAL is an interface for saving and retrieving (i) metadata about experiments and workflows, and (ii) values of produced metrics. It currently has a single implementation that acts as a Python client to the Data Abstraction Layer service of the ExtremeXP framework. Once the metadata of an experiment is saved in the Data Abstraction Layer, they can be retrieved by other components of the framework (e.g., the Experiment Visualization and Experiment Cards ones).

---

Given the above modular and adaptable architecture, the Experimentation Engine performs the following key steps when provided with an experiment definition: 

1. It parses the experiment definition written in the ExtremeXP Domain-Specific Language (DSL) using textX, a Python tool for working with textual DSLs.
2. It executes the steps of an experiment according to its control logic (in sequence or in parallel). It can do so in a conditional way, i.e., execute steps based on the results of previous ones.  
3. For each step being executed, it generates the necessary executable workflows, i.e., the workflows consisting of non-abstract, fully parametrized tasks.
4. It submits the executable workflows for execution. 
5. It retrieves the results of each executed workflow (such as metrics values, generated datasets) and saves them alongside the metadata of the experiment and the executed workflows. 
6. It may submit special types of workflows for execution, which consist of tasks that expect input from users – “user-interaction” tasks. Inputs from users are also saved together with the results of each workflow. 

---

- **Start with the [User Guide](guide.md)**  
- **Learn about [Configuration](config.md)**  
- **Understand the [DSL Syntax](dsl/experiments.md)**  
- **See [Examples](examples.md)**