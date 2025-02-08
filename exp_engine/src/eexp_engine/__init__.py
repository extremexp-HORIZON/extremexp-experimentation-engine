from .functions import parsing
from .functions.execution import Execution
import logging

logger = logging.getLogger(__name__)


def run_experiment(exp_id, experiment_specification, runner_folder, config):
    parsing.CONFIG = config

    logger.info("*********************************************************")
    logger.info("***************** PARSE WORKFLOWS ***********************")
    logger.info("*********************************************************")
    parsed_workflows, task_dependencies = parsing.parse_workflows(experiment_specification)

    logger.info("*********************************************************")
    logger.info("********** PARSE ASSEMBLED WORKFLOWS DATA ***************")
    logger.info("*********************************************************")
    assembled_workflows_data = parsing.parse_assembled_workflow_data(experiment_specification)

    assembled_flat_wfs = []
    if assembled_workflows_data:
        logger.info("*********************************************************")
        logger.info("************ GENERATE ASSEMBLED WORKFLOWS ***************")
        logger.info("*********************************************************")
        assembled_wfs = parsing.generate_final_assembled_workflows(parsed_workflows, assembled_workflows_data)
        for wf in assembled_wfs:
            wf.print()

        logger.info("*********************************************************")
        logger.info("********** GENERATE ASSEMBLED FLAT WORKFLOWS ************")
        logger.info("*********************************************************")
        parsing.generate_assembled_flat_workflows(assembled_wfs, assembled_flat_wfs)

    logger.info("*********************************************************")
    logger.info("************** EXPERIMENT SPECIFICATION *****************")
    logger.info("*********************************************************")
    exp = parsing.parse_experiment_specification(experiment_specification)
    exp.print()

    logger.info("*********************************************************")
    logger.info("***************** RUNNING WORKFLOWS *********************")
    logger.info("*********************************************************")
    execution = Execution(exp_id, exp, assembled_flat_wfs, runner_folder, config)
    execution.start()
