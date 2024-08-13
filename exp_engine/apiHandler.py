import exp_engine_functions as functions
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ApiHandler(object):

    EXPERIMENTS_FOLDER = 'workflows/'

    def __init__(self):
        print("ApiHandler created")

    def run_experiment(self, exp_id):
        dsl_file="IDEKO_main"

        with open(self.EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
            experiment_specification = file.read()

        logger.info("running experiment NOW")
        functions.run_experiment(experiment_specification, exp_id)


apiHandler = ApiHandler()
