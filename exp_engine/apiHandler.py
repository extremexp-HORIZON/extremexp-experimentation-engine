import src.eexp_engine.exp_engine_functions as functions
from src.eexp_engine import client
from src.eexp_engine.data_abstraction_layer.data_abstraction_api import *
import eexp_config
import logging


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
set_data_abstraction_config(eexp_config)


class ApiHandler(object):

    EXPERIMENTS_FOLDER = 'workflows/'

    def __init__(self):
        print("ApiHandler created")

    def run_experiment(self, exp_id):
        # TODO make this work with the eexp_engine module instead
        None
        # dsl_file="IDEKO_main"
        #
        # with open(self.EXPERIMENTS_FOLDER + dsl_file + '.xxp', 'r') as file:
        #     experiment_specification = file.read()
        #
        # logger.info("running experiment NOW")
        # functions.run_experiment(experiment_specification, exp_id)

    def kill_workflow(self, wf_id):
        print(f"Killing workflow with id: {wf_id}")
        job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
        print(f"Killing proactive job with id: {job_id}")
        client.kill_job(job_id, eexp_config)

    def pause_workflow(self, wf_id):
        print(f"Pausing workflow with id: {wf_id}")
        job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
        print(f"Pausing proactive job with id: {job_id}")
        client.pause_job(job_id, eexp_config)

    def resume_workflow(self, wf_id):
        print(f"Resuming workflow with id: {wf_id}")
        job_id  = get_workflow(wf_id)["metadata"]["proactive_job_id"]
        print(f"Resuming proactive job with id: {job_id}")
        client.resume_job(job_id, eexp_config)


apiHandler = ApiHandler()
