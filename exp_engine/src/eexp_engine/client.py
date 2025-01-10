from .functions import run_experiment
from .executionware import proactive_runner as proactive_runner
from .data_abstraction_layer.data_abstraction_api import set_data_abstraction_config, create_experiment
import os
import logging.config


def run(runner_file, exp_name, config):
    with open(os.path.join(config.EXPERIMENT_LIBRARY_PATH, exp_name + ".xxp"), 'r') as file:
        workflow_specification = file.read()

    if 'LOGGING_CONFIG' in dir(config):
        logging.config.dictConfig(config.LOGGING_CONFIG)

    new_exp = {
        'name': exp_name,
        'model': str(workflow_specification),
    }
    set_data_abstraction_config(config)
    exp_id = create_experiment(new_exp)
    run_experiment(exp_id, workflow_specification, os.path.dirname(os.path.abspath(runner_file)), config)


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
