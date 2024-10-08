import exp_engine_functions as functions
from data_abstraction_layer.data_abstraction_api import create_experiment

EXPERIMENTS_FOLDER = 'IDEKO-experiment1/'
# EXPERIMENTS_FOLDER = 'MOBY-experiment1/'

dsl_file="IDEKO_high"
# dsl_file="moby-exp1"

with open(EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
    workflow_specification = file.read()

new_exp = {
    'name': "TestExperiment",
    'model': str(workflow_specification),
}
exp_id = create_experiment(new_exp)
functions.run_experiment(workflow_specification, exp_id)
