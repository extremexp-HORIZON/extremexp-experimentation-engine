from . import run_experiment
from .executionware import proactive_runner as proactive_runner
from .data_abstraction_layer.data_abstraction_api import set_data_abstraction_config, create_experiment
import os
import logging.config

logger = logging.getLogger(__name__)

class Config:

    def __init__(self, config):
        self.TASK_LIBRARY_PATH = config.TASK_LIBRARY_PATH
        self.EXPERIMENT_LIBRARY_PATH = config.EXPERIMENT_LIBRARY_PATH
        self.DATASET_LIBRARY_RELATIVE_PATH = config.DATASET_LIBRARY_RELATIVE_PATH
        self.PYTHON_DEPENDENCIES_RELATIVE_PATH = config.PYTHON_DEPENDENCIES_RELATIVE_PATH
        self.DATA_ABSTRACTION_BASE_URL = config.DATA_ABSTRACTION_BASE_URL
        self.DATA_ABSTRACTION_ACCESS_TOKEN = config.DATA_ABSTRACTION_ACCESS_TOKEN
        self.EXECUTIONWARE = config.EXECUTIONWARE
        self.PROACTIVE_USERNAME = config.PROACTIVE_USERNAME
        self.PROACTIVE_PASSWORD = config.PROACTIVE_PASSWORD
        self.PYTHON_CONDITIONS_FILE = config.PYTHON_CONDITIONS_FILE
        if 'MAX_SUBPROCESSES' in dir(config):
            logger.debug(f"Setting MAX_SUBPROCESSES to {config.MAX_SUBPROCESSES}")
            self.MAX_SUBPROCESSES = config.MAX_SUBPROCESSES
        else:
            default_max_subprocesses = 1
            logger.debug(f"Setting MAX_SUBPROCESSES to the default value of {default_max_subprocesses}")
            self.MAX_SUBPROCESSES = default_max_subprocesses


def run(runner_file, exp_name, config):
    with open(os.path.join(config.EXPERIMENT_LIBRARY_PATH, exp_name + ".xxp"), 'r') as file:
        workflow_specification = file.read()

    if 'LOGGING_CONFIG' in dir(config):
        logging.config.dictConfig(config.LOGGING_CONFIG)

    new_exp = {
        'name': exp_name,
        'model': str(workflow_specification),
    }

    config_obj = Config(config)
    set_data_abstraction_config(config_obj)
    exp_id = create_experiment(new_exp, "dummy_user")
    run_experiment(exp_id, workflow_specification, os.path.dirname(os.path.abspath(runner_file)), config_obj)


def kill_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config.PROACTIVE_USERNAME, config.PROACTIVE_PASSWORD)
    gateway.killJob(job_id)


def pause_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config.PROACTIVE_USERNAME, config.PROACTIVE_PASSWORD)
    gateway.pauseJob(job_id)


def resume_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config.PROACTIVE_USERNAME, config.PROACTIVE_PASSWORD)
    gateway.resumeJob(job_id)


def kill_task(job_id, task_name, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config.PROACTIVE_USERNAME, config.PROACTIVE_PASSWORD)
    gateway.killTask(job_id, task_name)
