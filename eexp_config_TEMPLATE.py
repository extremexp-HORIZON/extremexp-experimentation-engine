# Main folders (mandatory) - paths are just examples
TASK_LIBRARY_PATH = 'exp_engine/library-tasks'
EXPERIMENT_LIBRARY_PATH = 'exp_engine/library-experiments'
# The ones below has to be a path relative to the script that invokes the client.run()
DATASET_LIBRARY_RELATIVE_PATH = 'exp_engine/library-datasets'
PYTHON_DEPENDENCIES_RELATIVE_PATH = 'exp_engine/tasks'

# Reference here the Python file that holds the functions used in the evaluation of conditions.
# Path is relative to the script that invokes the client.run()
PYTHON_CONDITIONS = 'exp_engine.library-tasks.experiment_conditions'

# The Python file that holds any functions used for filtering or generating configurations for spaces
PYTHON_CONFIGURATIONS = 'exp_engine.library-tasks.experiment_configurations'

# number of workflows that the engine can run in parallel per node at any given moment (if omitted, value is 1)
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 3
MAX_EXPERIMENTS_IN_PARALLEL = 4

EXECUTIONWARE = "PROACTIVE" # other option: "LOCAL"
# Proactive details (only needed if EXECUTIONWARE = "PROACTIVE" above)
PROACTIVE_URL = "http://146.124.106.171:8880"
# Proactive credentials (mandatory - ask ICOM)
PROACTIVE_USERNAME=""
PROACTIVE_PASSWORD=""
# You need to specify the path to the Python version you want to explicitly use (ask ICOM)
PROACTIVE_PYTHON_VERSIONS = {"3.8": "/usr/bin/python3.8", "3.9": "/usr/bin/python3.9"}

KUBEFLOW_URL = ""
KUBEFLOW_MINIO_ENDPOINT = ""
KUBEFLOW_MINIO_USERNAME = ""
KUBEFLOW_MINIO_PASSWORD = ""

# Data abstraction credentials (mandatory - ask ICOM)
DATA_ABSTRACTION_BASE_URL = "http://146.124.106.171:8445/api"
DATA_ABSTRACTION_ACCESS_TOKEN = ''

# possible values: DDM (Decentralized Data Management), LOCAL
DATASET_MANAGEMENT = "DDM"
DATASET_MANAGEMENT_URL = "https://ddm.extremexp-icom.intracom-telecom.com"
PORTAL_USERNAME = "" # the same as the one you use to login to the portal, if in doubt ask ICOM
PORTAL_PASSWORD = "" # the same as the one you use to login to the portal, if in doubt ask ICOM

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
