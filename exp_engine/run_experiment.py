import exp_engine_functions as functions

EXPERIMENTS_FOLDER = 'IDEKO-experiment1/'

# dsl_file = input("Please provide the name of the DSL file (without the extension):")

dsl_file="IDEKO_high"

with open(EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
    workflow_specification = file.read()

experiment_specifications = functions.get_experiment_specification(workflow_specification)

for ep in experiment_specifications:
    print(ep)
    # functions.run_experiment(ep)

