"""
Client module for the ExtremeXP Experimentation Engine.

This module provides the main API for running and managing experiments.
Focused on experiment orchestration and control.
"""

from eexp_engine.error_logger import ErrorLogger
from . import run_experiment
from .executionware import proactive_runner as proactive_runner
from .data_abstraction_layer.data_abstraction_api import DataAbstractionClient
from .config import Config
import os
import logging.config
import threading

logger = logging.getLogger(__name__)

# Import experiment queue - will be initialized on first async execution
_experiment_queue = None


def _get_queue(config):
    """Lazy initialization of experiment queue for async execution only."""
    global _experiment_queue
    max_concurrent_config = config.MAX_EXPERIMENTS_IN_PARALLEL if config.MAX_EXPERIMENTS_IN_PARALLEL is not None else 4
    if _experiment_queue is None:
        # Import here to avoid circular dependencies
        from .experiment_queue import get_experiment_queue
        _experiment_queue = get_experiment_queue(max_concurrent=max_concurrent_config)
        logger.info("Experiment queue initialized for async execution")
    return _experiment_queue


def get_final_experiment_spec(config, exp_name):
    """
    Load and process experiment specification file.

    Handles import statements to include workflow definitions.

    Args:
        config: Configuration object
        exp_name: Name of the experiment

    Returns:
        str: Complete experiment specification with imported workflows
    """
    exp_spec_file = os.path.join(config.EXPERIMENT_LIBRARY_PATH, exp_name + ".xxp")
    if not os.path.isfile(exp_spec_file):
        logger.error(f"Specification file not found for experiment '{exp_name}': {exp_spec_file}")
        raise FileNotFoundError(f"Experiment specification '{exp_name}.xxp' not found")

    with open(exp_spec_file, 'r') as file:
        experiment_specification = file.readlines()

    workflows_to_import = []
    final_exp_spec = ""
    for line in experiment_specification:
        if line.startswith("import"):
            if "\'" in line:
                workflows_to_import.append(line.split("\'")[1])
            elif "\"" in line:
                workflows_to_import.append(line.split("\"")[1])
        else:
            final_exp_spec += line

    for wf_file in workflows_to_import:
        file_path = os.path.join(config.WORKFLOW_LIBRARY_PATH, wf_file)
        with open(file_path, 'r') as file:
            final_exp_spec += file.read()

    return final_exp_spec


def run(runner_file, exp_name, config, async_execution: bool = False, username: str = None):
    """
    Run an experiment.

    Args:
        runner_file: Path to the runner script
        exp_name: Name of the experiment to run
        config: Configuration object
        async_execution: If True, run asynchronously in queue
        username: Username for experiment ownership and logging

    Returns:
        str: Experiment ID
    """
    if async_execution:
        error_logger = ErrorLogger()
    mode_str = "async" if async_execution else "sync"
    logger.info(f"[run] starting experiment creation ({mode_str} mode)")
    logger.info(f"relpath: {os.path.relpath(config.EXPERIMENT_LIBRARY_PATH)}")

    try:
        final_exp_spec = get_final_experiment_spec(config, exp_name)

        if 'LOGGING_CONFIG' in dir(config):
            try:
                logging.config.dictConfig(config.LOGGING_CONFIG)
            except Exception:
                logger.exception("Failed to apply LOGGING_CONFIG")

        new_exp = {
            'name': exp_name,
            'model': final_exp_spec,
        }

        config_obj = Config(config)
        data_client = DataAbstractionClient(config_obj)

        # Determine the username for experiment creation
        creator_name = username if username else (config.PORTAL_USERNAME if hasattr(config, 'PORTAL_USERNAME') else "dummy_user")

        exp_id = data_client.create_experiment(new_exp, creator_name)
        if not exp_id:
            raise RuntimeError("Failed to create experiment")
    except Exception as e:
        logger.exception(f"Experiment parsing/init failed: {e}")
        raise

    if async_execution:
        cancel_flag = threading.Event()

        def _execute_async():
            try:
                run_experiment(exp_id, final_exp_spec, os.path.dirname(os.path.abspath(runner_file)), config_obj, data_client, cancel_flag)
            except Exception as e:
                logger.exception(f"Experiment {exp_id} crashed: {e}")
                error_logger.write_error_log(
                    identifier=exp_id,
                    error=e,
                    extra_info={"phase": "runtime", "experiment_id": exp_id}
                )
                try:
                    data_client.update_experiment(exp_id, {"status": "failed"})
                except Exception:
                    logger.exception(f"Could not update experiment {exp_id} status to failed")

        # Enqueue the experiment (queue manages cancel_flag and lifecycle)
        queue = _get_queue(config)
        queue.enqueue(exp_id, _execute_async, cancel_flag)

        logger.info(f"Experiment {exp_id} enqueued for execution")
        return exp_id
    else:
        # Sync execution
        try:
            logger.info(f"Experiment {exp_id} executing synchronously")
            run_experiment(exp_id, final_exp_spec, os.path.dirname(os.path.abspath(runner_file)), config_obj, data_client)
            logger.info(f"Experiment {exp_id} finished (synchronous mode)")
        except Exception as e:
            logger.exception(f"Experiment {exp_id} crashed: {e}")
            try:
                data_client.update_experiment(exp_id, {"status": "failed"})
            except Exception:
                logger.exception(f"Could not update experiment {exp_id} status to failed")
            raise

        return exp_id


# ============================================================================
# Experiment Control Functions
# ============================================================================

def kill_experiment_thread(exp_id):
    """
    Sets the cancellation flag for a running or queued async experiment, signaling it to stop.

    For sync experiments, users should use terminal interrupt (Ctrl+C).

    Args:
        exp_id: Experiment ID to cancel

    Returns:
        bool: True if the experiment was found and flagged, False otherwise
    """
    global _experiment_queue
    if _experiment_queue is not None:
        if _experiment_queue.cancel_experiment(exp_id):
            logger.info(f"Experiment {exp_id} cancelled via queue")
            return True

    logger.warning(f"Experiment {exp_id} not found in queue")
    return False


def kill_job(job_id, config):
    """Kill a ProActive job."""
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.killJob(job_id)


def pause_job(job_id, config):
    """Pause a ProActive job."""
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.pauseJob(job_id)


def resume_job(job_id, config):
    """Resume a paused ProActive job."""
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    try:
        gateway.resumeJob(job_id)
    except Exception as e:
        logger.exception(f"Failed to resume job {job_id}: {e}")


def kill_task(job_id, task_name, config):
    """Kill a specific task in a ProActive job."""
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.killTask(job_id, task_name)
