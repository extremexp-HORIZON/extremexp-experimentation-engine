import exp_engine_functions as functions
from data_abstraction_layer.data_abstraction_api import create_experiment

EXPERIMENTS_FOLDER = 'library-experiments/'
# EXPERIMENTS_FOLDER = 'MOBY-experiment1/'

dsl_file="IDEKO_high"
# dsl_file="moby-exp1"
dsl_file="IDEKO_main"


with open(EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
    workflow_specification = file.read()

new_exp = {
    'name': "IDEKO_Experiment",
    'model': str(workflow_specification),
}
exp_id = create_experiment(new_exp)
functions.run_experiment(workflow_specification, exp_id)

# experiment_specifications = functions.get_experiment_specification(workflow_specification)
#
# for ep in experiment_specifications:
#     print(ep)
#     functions.run_experiment(ep)
