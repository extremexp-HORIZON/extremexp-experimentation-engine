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
        self.PYTHON_CONDITIONS = config.PYTHON_CONDITIONS if 'PYTHON_CONDITIONS' in dir(config) else None
        self.PYTHON_CONFIGURATIONS = config.PYTHON_CONFIGURATIONS if 'PYTHON_CONFIGURATIONS' in dir(config) else None
        if 'MAX_WORKFLOWS_IN_PARALLEL_PER_NODE' in dir(config):
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to {config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE
        else:
            default_max_workflows_in_parallel_per_node = 1
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to the default value of {default_max_workflows_in_parallel_per_node}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = default_max_workflows_in_parallel_per_node


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
