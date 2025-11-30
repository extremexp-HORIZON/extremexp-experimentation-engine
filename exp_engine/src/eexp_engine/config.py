"""
Configuration module for the ExtremeXP Experimentation Engine.

Handles configuration validation and DDM authentication.
"""

import requests
import logging
from . import exceptions

logger = logging.getLogger(__name__)


def get_ddm_token(config):
    """
    Get authentication token from DDM (Decentralized Data Management) system.

    Args:
        config: Configuration object with DDM credentials

    Returns:
        str: Bearer token for DDM authentication, or None if not using DDM
    """
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
        logger.info("Portal authentication successful, DDM token retrieved")
        return f"Bearer {access_token}"


class Config:
    """
    Configuration wrapper for experiment execution.

    Validates and stores all required configuration parameters.
    Handles DDM authentication if needed.
    """

    def __init__(self, config):
        """
        Initialize configuration from a config module/object.

        Args:
            config: Configuration module or object with required attributes

        Raises:
            Various configuration exceptions if required settings are missing
        """
        # Core paths
        self.TASK_LIBRARY_PATH = config.TASK_LIBRARY_PATH
        self.EXPERIMENT_LIBRARY_PATH = config.EXPERIMENT_LIBRARY_PATH
        self.WORKFLOW_LIBRARY_PATH = config.WORKFLOW_LIBRARY_PATH
        self.DATASET_LIBRARY_RELATIVE_PATH = config.DATASET_LIBRARY_RELATIVE_PATH
        self.PYTHON_DEPENDENCIES_RELATIVE_PATH = config.PYTHON_DEPENDENCIES_RELATIVE_PATH

        # Dataset management validation
        if 'DATASET_MANAGEMENT' not in dir(config) or len(config.DATASET_MANAGEMENT) == 0:
            raise exceptions.DatasetManagementNotSet(
                "Please set the variable DATASET_MANAGEMENT in config.py to either \"LOCAL\" or \"DDM\"")
        self.DATASET_MANAGEMENT = config.DATASET_MANAGEMENT

        # DDM-specific validation
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

        # DDM configuration
        self.DDM_URL = config.DDM_URL if 'DDM_URL' in dir(config) else None
        self.DDM_TOKEN = get_ddm_token(config)

        # Data abstraction layer
        self.DATA_ABSTRACTION_BASE_URL = config.DATA_ABSTRACTION_BASE_URL
        self.DATA_ABSTRACTION_ACCESS_TOKEN = config.DATA_ABSTRACTION_ACCESS_TOKEN

        # Executionware configuration
        self.EXECUTIONWARE = config.EXECUTIONWARE

        # ProActive configuration
        self.PROACTIVE_URL = config.PROACTIVE_URL
        self.PROACTIVE_USERNAME = config.PROACTIVE_USERNAME
        self.PROACTIVE_PASSWORD = config.PROACTIVE_PASSWORD
        self.PROACTIVE_PYTHON_VERSIONS = config.PROACTIVE_PYTHON_VERSIONS if 'PROACTIVE_PYTHON_VERSIONS' in dir(config) else None

        # Kubeflow configuration (optional)
        self.KUBEFLOW_URL = config.KUBEFLOW_URL if 'KUBEFLOW_URL' in dir(config) else None
        self.KUBEFLOW_USERNAME = config.KUBEFLOW_USERNAME if 'KUBEFLOW_USERNAME' in dir(config) else None
        self.KUBEFLOW_PASSWORD = config.KUBEFLOW_PASSWORD if 'KUBEFLOW_PASSWORD' in dir(config) else None
        self.KUBEFLOW_MINIO_ENDPOINT = config.KUBEFLOW_MINIO_ENDPOINT if 'KUBEFLOW_MINIO_ENDPOINT' in dir(config) else None
        self.KUBEFLOW_MINIO_USERNAME = config.KUBEFLOW_MINIO_USERNAME if 'KUBEFLOW_MINIO_USERNAME' in dir(config) else None
        self.KUBEFLOW_MINIO_PASSWORD = config.KUBEFLOW_MINIO_PASSWORD if 'KUBEFLOW_MINIO_PASSWORD' in dir(config) else None

        # Python conditions and configurations
        self.PYTHON_CONDITIONS = config.PYTHON_CONDITIONS if 'PYTHON_CONDITIONS' in dir(config) else None
        self.PYTHON_CONFIGURATIONS = config.PYTHON_CONFIGURATIONS if 'PYTHON_CONFIGURATIONS' in dir(config) else None

        # Execution parallelism settings
        self.MAX_EXPERIMENTS_IN_PARALLEL = config.MAX_EXPERIMENTS_IN_PARALLEL if 'MAX_EXPERIMENTS_IN_PARALLEL' in dir(config) else 4

        if 'MAX_WORKFLOWS_IN_PARALLEL_PER_NODE' in dir(config):
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to {config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = config.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE
        else:
            default_max_workflows_in_parallel_per_node = 1
            logger.debug(f"Setting MAX_WORKFLOWS_IN_PARALLEL_PER_NODE to the default value of {default_max_workflows_in_parallel_per_node}")
            self.MAX_WORKFLOWS_IN_PARALLEL_PER_NODE = default_max_workflows_in_parallel_per_node
