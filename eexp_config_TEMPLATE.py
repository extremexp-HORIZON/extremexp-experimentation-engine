# Main folders (mandatory) - paths are just examples
TASK_LIBRARY_PATH = 'exp_engine/library-tasks'
EXPERIMENT_LIBRARY_PATH = 'exp_engine/library-experiments'
# The ones below has to be a path relative to the script that invokes the client.run()
DATASET_LIBRARY_RELATIVE_PATH = 'exp_engine/library-datasets'
PYTHON_DEPENDENCIES_RELATIVE_PATH = 'exp_engine/tasks'

# Reference here the Python file that holds the functions used in the evaluation of conditions.
# Path is relative to the script that invokes the client.run()
PYTHON_CONDITIONS_FILE = 'exp_engine.library-tasks.experiment_conditions'

# number of workflows that the engine can run in parallel per node at any given moment (if omitted, value is 1)
MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = 3

EXECUTIONWARE = "PROACTIVE" # other option: "LOCAL"
# Proactive credentials (only needed if EXECUTIONWARE = "PROACTIVE" above)
PROACTIVE_USERNAME=""
PROACTIVE_PASSWORD=""

# Data abstraction credentials (mandatory - ask CUNI)
DATA_ABSTRACTION_BASE_URL = "https://api.expvis.smartarch.cz/api"
DATA_ABSTRACTION_ACCESS_TOKEN = ''

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
