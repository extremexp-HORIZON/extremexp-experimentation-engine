from . import run_experiment
from .executionware import proactive_runner as proactive_runner
from .data_abstraction_layer.data_abstraction_api import DataAbstractionClient
import os
import requests
import logging.config
from . import exceptions
import threading
import time
import traceback

logger = logging.getLogger(__name__)

# Global registry for tracking running experiment threads and their cancellation flags
_running_experiments = {}  # {exp_id: {"thread": thread_obj, "cancel_flag": threading.Event()}}


def get_ddm_token(config):
    if config.DATASET_MANAGEMENT != "DDM":
        return None
    url = f"{config.DDM_URL}/extreme_auth/api/v1/person/login"
    data = {
        "username": config.PORTAL_USERNAME,
        "password": config.PORTAL_PASSWORD
    }
    response = requests.post(url, json=data)
    status_code = response.status_code
    response_json = response.json()
    if status_code == 401:
        logger.error("Portal authentication failed.")
        error_code = response_json["error_code"]
        if error_code == 4012:
            raise exceptions.PortalUserDoesNotExist(
                "Portal user not found - please check the PORTAL_USERNAME in your configuration")
        if error_code == 4011:
            raise exceptions.PortalPasswordDoesNotMatch(
                "Portal user found, but password does not match - please check PORTAL_PASSWORD in your configuration")
    if status_code == 200:
        access_token = response.json()["access_token"]
        logger.info("portal authentication successful, ddm token retrieved")
        return f"Bearer {access_token}"
    
class ErrorLogger:
    def __init__(self, log_dir="/error_logs", retention_seconds=15*60):
        self.log_dir = log_dir
        self.retention_seconds = retention_seconds
        os.makedirs(self.log_dir, exist_ok=True)

    def cleanup_old_logs(self):
        now = time.time()
        for fname in os.listdir(self.log_dir):
            fpath = os.path.join(self.log_dir, fname)
            if os.path.isfile(fpath):
                try:
                    mtime = os.path.getmtime(fpath)
                    if now - mtime > self.retention_seconds:
                        os.remove(fpath)
                except Exception as e:
                    print(f"Error cleaning up log file {fpath}: {e}")

    def write_error_log(self, identifier, error, extra_info=None):
        self.cleanup_old_logs()
        ts = int(time.time())
        log_fname = f"error_{identifier}_{ts}.log"
        log_path = os.path.join(self.log_dir, log_fname)
        try:
            with open(log_path, "w") as f:
                if extra_info:
                    for k, v in extra_info.items():
                        f.write(f"{k}: {v}\n")
                f.write(f"Timestamp: {ts}\n")
                f.write(f"Exception: {error}\n")
                f.write("Stack Trace:\n")
                f.write(traceback.format_exc())
        except Exception as log_exc:
            print(f"Failed to write error log: {log_exc}")


class Config:

    def __init__(self, config):
        self.TASK_LIBRARY_PATH = config.TASK_LIBRARY_PATH
        self.EXPERIMENT_LIBRARY_PATH = config.EXPERIMENT_LIBRARY_PATH
        self.DATASET_LIBRARY_RELATIVE_PATH = config.DATASET_LIBRARY_RELATIVE_PATH
        self.PYTHON_DEPENDENCIES_RELATIVE_PATH = config.PYTHON_DEPENDENCIES_RELATIVE_PATH
        if 'DATASET_MANAGEMENT' not in dir(config) or len(config.DATASET_MANAGEMENT) == 0:
            raise exceptions.DatasetManagementNotSet(
                "Please set the variable DATASET_MANAGEMENT in config.py to either \"LOCAL\" or \"DDM\"")
        else:
            self.DATASET_MANAGEMENT = config.DATASET_MANAGEMENT
        if config.DATASET_MANAGEMENT == "DDM":
            if 'DDM_URL' not in dir(config) or len(config.DDM_URL) == 0:
                raise exceptions.DatasetManagementSetToDDMButNoURLProvided(
                    "Please set the variable DDM_URL in config.py")
            if 'PORTAL_USERNAME' not in dir(config) or len(config.PORTAL_USERNAME) == 0:
                raise exceptions.DatasetManagementSetToDDMButNoPortalUserOrPasswordProvided(
                    "Please set the variable PORTAL_USERNAME in config.py")
            if 'PORTAL_PASSWORD' not in dir(config) or len(config.PORTAL_PASSWORD) == 0:
                raise exceptions.DatasetManagementSetToDDMButNoPortalUserOrPasswordProvided(
                    "Please set the variable PORTAL_PASSWORD in config.py")
        self.DDM_URL = config.DDM_URL if 'DDM_URL' in dir(config) else None
        self.DDM_TOKEN = get_ddm_token(config)
        self.DATA_ABSTRACTION_BASE_URL = config.DATA_ABSTRACTION_BASE_URL
        self.DATA_ABSTRACTION_ACCESS_TOKEN = config.DATA_ABSTRACTION_ACCESS_TOKEN
        self.EXECUTIONWARE = config.EXECUTIONWARE
        self.PROACTIVE_URL = config.PROACTIVE_URL
        self.PROACTIVE_USERNAME = config.PROACTIVE_USERNAME
        self.PROACTIVE_PASSWORD = config.PROACTIVE_PASSWORD
        self.PROACTIVE_PYTHON_VERSIONS = config.PROACTIVE_PYTHON_VERSIONS if 'PROACTIVE_PYTHON_VERSIONS' in dir(config) else None
        self.KUBEFLOW_URL = config.KUBEFLOW_URL if 'KUBEFLOW_URL' in dir(config) else None
        self.KUBEFLOW_MINIO_ENDPOINT = config.KUBEFLOW_MINIO_ENDPOINT if 'KUBEFLOW_MINIO_ENDPOINT' in dir(config) else None
        self.KUBEFLOW_MINIO_USERNAME = config.KUBEFLOW_MINIO_USERNAME if 'KUBEFLOW_MINIO_USERNAME' in dir(config) else None
        self.KUBEFLOW_MINIO_PASSWORD = config.KUBEFLOW_MINIO_PASSWORD if 'KUBEFLOW_MINIO_PASSWORD' in dir(config) else None
        self.PYTHON_CONDITIONS = config.PYTHON_CONDITIONS if 'PYTHON_CONDITIONS' in dir(config) else None
        self.PYTHON_CONFIGURATIONS = config.PYTHON_CONFIGURATIONS if 'PYTHON_CONFIGURATIONS' in dir(config) else None
        if 'MAX_WORKFLOWS_IN_PARALLEL_PER_NODE' in dir(config):
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to {config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE
        else:
            default_max_workflows_in_parallel_per_node = 1
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to the default value of {default_max_workflows_in_parallel_per_node}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = default_max_workflows_in_parallel_per_node


def run(runner_file, exp_name, config, async_execution: bool = False):
    if async_execution:
        error_logger = ErrorLogger()
    mode_str = "async" if async_execution else "sync"
    logger.info(f"[run] starting experiment creation ({mode_str} mode)")
    logger.info(f"abspath: {os.path.relpath(config.EXPERIMENT_LIBRARY_PATH)}")
    logger.info(f"listing experiment library: {os.listdir(config.EXPERIMENT_LIBRARY_PATH)}")

    try:
        spec_path = os.path.join(config.EXPERIMENT_LIBRARY_PATH, exp_name + ".xxp")
        if not os.path.isfile(spec_path):
            logger.error(f"Specification file not found for experiment '{exp_name}': {spec_path}")
            raise FileNotFoundError(f"Experiment specification '{exp_name}.xxp' not found")

        with open(spec_path, 'r') as file:
            workflow_specification = file.read()

        if 'LOGGING_CONFIG' in dir(config):
            try:
                logging.config.dictConfig(config.LOGGING_CONFIG)
            except Exception:
                logger.exception("Failed to apply LOGGING_CONFIG")

        new_exp = {
            'name': exp_name,
            'model': str(workflow_specification),
        }

        config_obj = Config(config)
        data_client = DataAbstractionClient(config_obj)

        exp_id = data_client.create_experiment(new_exp, "dummy_user")
        if not exp_id:
            # create_experiment already logged details
            raise RuntimeError("Failed to create experiment")
    except Exception as e:
        logger.exception(f"Experiment parsing/init failed: {e}")
        if async_execution:
            error_logger.write_error_log(
                identifier=exp_name,
                error=e,
                extra_info={"phase": "parsing/init", "experiment_name": exp_name}
            )
        raise

    def _execute():
        try:
            cancel_flag = _running_experiments.get(exp_id, {}).get("cancel_flag")
            run_experiment(exp_id, workflow_specification, os.path.dirname(os.path.abspath(runner_file)), config_obj, data_client, cancel_flag)
        except Exception as e:
            logger.exception(f"Experiment {exp_id} crashed: {e}")
            if async_execution:
                error_logger.write_error_log(
                    identifier=exp_id,
                    error=e,
                    extra_info={"phase": "runtime", "experiment_id": exp_id}
                )
            try:
                data_client.update_experiment(exp_id, {"status": "failed"})
            except Exception:
                logger.exception(f"Could not update experiment {exp_id} status to failed")
        finally:
            # Clean up from registry when done
            if exp_id in _running_experiments:
                del _running_experiments[exp_id]
                logger.info(f"Removed experiment {exp_id} from running experiments registry")

    if async_execution:
        cancel_flag = threading.Event()
        t = threading.Thread(target=_execute, name=f"exp-run-{exp_id}", daemon=False)
        _running_experiments[exp_id] = {"thread": t, "cancel_flag": cancel_flag}
        t.start()
        logger.info(f"Experiment {exp_id} launched asynchronously (thread {t.name}, daemon={t.daemon})")
        return exp_id
    else:
        logger.info(f"Experiment {exp_id} executing synchronously")
        _execute()
        logger.info(f"Experiment {exp_id} finished (synchronous mode)")
        return exp_id


def kill_experiment_thread(exp_id):
    """
    Sets the cancellation flag for a running experiment, signaling it to stop.
    Returns True if the experiment was found and flagged, False otherwise.
    """
    if exp_id in _running_experiments:
        logger.info(f"Setting cancellation flag for experiment {exp_id}")
        _running_experiments[exp_id]["cancel_flag"].set()
        return True
    else:
        logger.warning(f"Experiment {exp_id} not found in running experiments registry")
        return False


def kill_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.killJob(job_id)


def pause_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.pauseJob(job_id)


def resume_job(job_id, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    try:
        gateway.resumeJob(job_id)
    except Exception as e:
        logger.exception(f"Failed to resume job {job_id}: {e}")


def kill_task(job_id, task_name, config):
    gateway = proactive_runner.create_gateway_and_connect_to_it(config)
    gateway.killTask(job_id, task_name)
