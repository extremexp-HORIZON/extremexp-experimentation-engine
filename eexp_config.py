# Workspace root (optional) - Set this if you are using eexp_egnine as a service.
# Point this to the root directory where all user workspaces will be created.
WORKSPACE_ROOT = None

# Main folders (mandatory) - paths are just examples
TASK_LIBRARY_PATH = 'playground/tasks'
EXPERIMENT_LIBRARY_PATH = 'playground/experiments'
WORKFLOW_LIBRARY_PATH = 'playground/workflows'
# The ones below has to be a path relative to the script that invokes the client.run()
DATASET_LIBRARY_RELATIVE_PATH = 'playground/datasets'
PYTHON_DEPENDENCIES_RELATIVE_PATH = 'playground/dependencies'
# Reference here the Python file that holds the functions used in the evaluation of conditions.
# Path is relative to the script that invokes the client.run()
PYTHON_CONDITIONS = 'playground.tasks.experiment_conditions'

# The Python file that holds any functions used for filtering or generating configurations for spaces
PYTHON_CONFIGURATIONS = 'playground.tasks.experiment_configurations'

# number of workflows that the engine can run in parallel per node at any given moment (if omitted, value is 1)
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 3
MAX_EXPERIMENTS_IN_PARALLEL = 4

PREFECT_API_URL="http://127.0.0.1:4200/api"
EXECUTIONWARE = "AIRFLOW" # other options: "LOCAL" & "KUBEFLOW"
# Proactive details (only needed if EXECUTIONWARE = "PROACTIVE" above)
PROACTIVE_URL = "http://146.124.106.171:8880"
# Proactive credentials (mandatory - ask ICOM)
PROACTIVE_USERNAME=""
PROACTIVE_PASSWORD=""
# You need to specify the path to the Python version you want to explicitly use (ask ICOM)
PROACTIVE_PYTHON_VERSIONS = {"3.8": "/usr/bin/python3.8", "3.9": "/usr/bin/python3.9"}

KUBEFLOW_URL = ""
KUBEFLOW_USERNAME = ""
KUBEFLOW_PASSWORD = ""
KUBEFLOW_MINIO_ENDPOINT = ""
KUBEFLOW_MINIO_USERNAME = ""
KUBEFLOW_MINIO_PASSWORD = ""

# Data abstraction credentials (mandatory - ask ICOM)
DATA_ABSTRACTION_BASE_URL = "http://146.124.106.171:8445/api"
DATA_ABSTRACTION_ACCESS_TOKEN = '668c8d6d014e0ef3a2f264d92ccd337a7451f6b2'

# possible values: DDM (Decentralized Data Management), LOCAL
DATASET_MANAGEMENT = "LOCAL"
DATASET_MANAGEMENT_URL = "https://ddm.extremexp-icom.intracom-telecom.com"

# ExtremeExp Portal credentials (he same as the one you use to login to the portal)
PORTAL_USERNAME = ""
PORTAL_PASSWORD = ""

# logging configuration, optional; if not set, all loggers have INFO level
LOGGING_CONFIG = {
    'version': 1,
    'loggers': {
        'eexp_engine.functions': {
            'level': 'INFO'
        },
        'eexp_engine.functions.parsing': {
            'level': 'INFO',
        },
        'eexp_engine.functions.execution': {
            'level': 'INFO',
        },
        'eexp_engine.data_abstraction_layer': {
            'level': 'INFO'
        },
        'eexp_engine.models': {
            'level': 'INFO'
        },
        'eexp_engine.proactive_executionware': {
            'level': 'INFO'
        }
    }
}
