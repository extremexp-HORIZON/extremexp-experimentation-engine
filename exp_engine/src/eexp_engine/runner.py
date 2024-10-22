from . import exp_engine_functions as functions
from .data_abstraction_layer.data_abstraction_api import set_data_abstraction_config, create_experiment
import os

def run(runner_file, exp_name, config):
    with open(os.path.join(config.EXPERIMENT_LIBRARY_PATH, exp_name + ".xxp"), 'r') as file:
        workflow_specification = file.read()

    new_exp = {
        'name': exp_name,
        'model': str(workflow_specification),
    }
    set_data_abstraction_config(config)
    exp_id = create_experiment(new_exp)
    functions.run_experiment(workflow_specification, exp_id, os.path.dirname(os.path.abspath(runner_file)), config)

# experiment_specifications = functions.get_experiment_specification(workflow_specification)
#
# for ep in experiment_specifications:
#     print(ep)
#     functions.run_experiment(ep)
