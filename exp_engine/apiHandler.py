import exp_engine_functions as functions


class ApiHandler(object):

    EXPERIMENTS_FOLDER = 'IDEKO-experiment1/'

    def __init__(self):
        print("ApiHandler created")

    def run_experiment(self):
        print("run_experiment")

        dsl_file="IDEKO_main"

        with open(self.EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
            experiment_specification = file.read()

        functions.run_experiment(experiment_specification)


apiHandler = ApiHandler()
