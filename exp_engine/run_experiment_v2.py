import exp_engine_functions as functions

EXPERIMENTS_FOLDER = 'IDEKO-experiment1/'

# dsl_file = input("Please provide the name of the DSL file (without the extension):")

dsl_file="IDEKO_main"

with open(EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
    experiment_specification = file.read()

functions.run_experiment(experiment_specification)

