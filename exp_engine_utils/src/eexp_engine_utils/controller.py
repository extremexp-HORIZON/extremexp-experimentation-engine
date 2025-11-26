from __future__ import annotations

import os
import json
from typing import Any, Dict, Optional, List
from types import ModuleType
from io import BytesIO

from .exceptions import ExecutionwareError, ConfigurationError

# Constants
EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX = "execution_engine_runtime_config"

_utils_module_cache = None


class UtilsProxy:
    """
    A transparent proxy that routes all attribute/function calls to the appropriate
    utils module based on EXECUTIONWARE configuration.
    """

    def __getattr__(self, name):
        """
        Intercept attribute access and route to the correct utils module.

        Args:
            name: The attribute/function name being accessed

        Returns:
            The attribute/function from the appropriate utils module
        """
        # Get the appropriate utils module
        utils_module = get_utils()

        # Get the attribute from that module
        try:
            return getattr(utils_module, name)
        except AttributeError:
            raise AttributeError(
                f"'{type(self).__name__}' object has no attribute '{name}'. "
                f"The current utils module ({utils_module.__name__}) does not provide this function."
            )

    def __dir__(self):
        """Return the list of available attributes from the current utils module."""
        utils_module = get_utils()
        return dir(utils_module)

    def get_experiment_results(self, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Get experiment results from the results file.

        Args:
            variables: Runtime variables containing workflow ID

        Returns:
            Optional[Dict[str, Any]]: Experiment results if file exists, None otherwise

        Raises:
            ValidationError: If variables is invalid or missing required keys
        """
        return self.__getattr__('get_experiment_results')(variables)

    def save_datasets(
        self,
        variables: Dict[str, Any],
        resultMap: Dict[str, Any],
        key: str,
        values: List[BytesIO],
        file_names: Optional[List[str]] = None,
    ) -> None:
        """
        Save multiple datasets (typically used with DDM).

        Args:
            variables: Runtime variables containing experiment metadata and mappings
            resultMap: Dictionary to store result metadata
            key: Dataset key
            values: List of dataset values to save (BytesIO objects)
            file_names: Optional list of filenames for the datasets

        Raises:
            ValidationError: If inputs are invalid
            ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        """
        return self.__getattr__('save_datasets')(variables, resultMap, key, values, file_names)

    def save_dataset(
        self,
        variables: Dict[str, Any],
        resultMap: Dict[str, Any],
        key: str,
        value: BytesIO
    ) -> None:
        """
        Save a single dataset.

        Args:
            variables: Runtime variables containing experiment metadata
            resultMap: Dictionary to store result metadata
            key: Dataset key
            value: Dataset value to save

        Raises:
            ValidationError: If inputs are invalid
            ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        """
        return self.__getattr__('save_dataset')(variables, resultMap, key, value)

    def load_datasets(
        self,
        variables: Dict[str, Any],
        resultMap: Dict[str, Any],
        key: str
    ) -> List[BytesIO]:
        """
        Load multiple datasets (typically used with DDM).

        Args:
            variables: Runtime variables containing experiment metadata
            resultMap: Dictionary containing result metadata from previous tasks
            key: Dataset key to load

        Returns:
            List[BytesIO]: List of loaded dataset values

        Raises:
            ValidationError: If inputs are invalid
            DatasetNotFoundError: If the dataset cannot be found
            ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        """
        return self.__getattr__('load_datasets')(variables, resultMap, key)

    def load_dataset(
        self,
        variables: Dict[str, Any],
        resultMap: Dict[str, Any],
        key: str
    ) -> BytesIO:
        """
        Load a single dataset.

        Args:
            variables: Runtime variables containing experiment metadata
            resultMap: Dictionary containing result metadata from previous tasks
            key: Dataset key to load

        Returns:
            BytesIO: The loaded dataset value

        Raises:
            ValidationError: If inputs are invalid
            DatasetNotFoundError: If the dataset cannot be found
            ConfigurationError: If DATASET_MANAGEMENT is not properly configured
        """
        return self.__getattr__('load_dataset')(variables, resultMap, key)

    def load_dataset_by_path(self, file_path: str) -> bytes:
        """
        Load a dataset directly from a file path.

        Args:
            file_path: Path to the file to load

        Returns:
            bytes: The file contents

        Raises:
            FileNotFoundError: If the file does not exist
            IOError: If there's an error reading the file
        """
        return self.__getattr__('load_dataset_by_path')(file_path)

    def load_pickled_dataset_by_path(self, file_path: str) -> Any:
        """
        Load a pickled dataset from a file path.

        Args:
            file_path: Path to the pickled file

        Returns:
            Any: The unpickled object

        Raises:
            FileNotFoundError: If the file does not exist
            pickle.UnpicklingError: If there's an error unpickling the file
        """
        return self.__getattr__('load_pickled_dataset_by_path')(file_path)

    def save_dataset_local(
        self,
        variables: Dict[str, Any],
        resultMap: Dict[str, Any],
        key: str,
        value: BytesIO
    ) -> None:
        """
        Save a dataset locally (without DDM).

        Args:
            variables: Runtime variables containing experiment metadata
            resultMap: Dictionary to store result metadata
            key: Dataset key
            value: Dataset value to save

        Raises:
            ValidationError: If inputs are invalid
        """
        return self.__getattr__('save_dataset_local')(variables, resultMap, key, value)

    def load_dataset_local(
        self,
        variables: Dict[str, Any],
        key: str
    ) -> BytesIO:
        """
        Load a dataset locally (without DDM).

        Args:
            variables: Runtime variables containing experiment metadata
            key: Dataset key to load

        Returns:
            BytesIO: The loaded dataset value

        Raises:
            ValidationError: If inputs are invalid
            DatasetNotFoundError: If the dataset cannot be found
        """
        return self.__getattr__('load_dataset_local')(variables, key)


def _get_runtime_config() -> Dict[str, Any]:
    """
    Locate and load the runtime configuration file.

    Returns:
        Dict[str, Any]: The runtime configuration dictionary containing EXECUTIONWARE and other settings.

    Raises:
        ConfigurationError: If the runtime config file cannot be found or is invalid JSON.
    """
    try:
        # Find the runtime config file in the current directory
        runtime_config_file = next(
            filename for filename in os.listdir('.')
            if filename.startswith(EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX)
        )
    except StopIteration:
        raise ConfigurationError(
            f"Runtime config file starting with '{EXECUTION_ENGINE_RUNTIME_CONFIG_PREFIX}' "
            f"not found in current directory"
        )
    except OSError as e:
        raise ConfigurationError(f"Error accessing current directory: {e}")

    try:
        with open(runtime_config_file, 'r') as file:
            runtime_config = json.load(file)
        return runtime_config
    except json.JSONDecodeError as e:
        raise ConfigurationError(f"Invalid JSON in runtime config file '{runtime_config_file}': {e}")
    except IOError as e:
        raise ConfigurationError(f"Error reading runtime config file '{runtime_config_file}': {e}")


def _get_executionware_from_config() -> str:
    """
    Extract the EXECUTIONWARE setting from the runtime configuration or environment variables.

    This function checks two sources in order:
    1. EXECUTIONWARE environment variable (used by Kubeflow/Local)
    2. Runtime config file (used by ProActive)

    Returns:
        str: The EXECUTIONWARE value (e.g., "KUBEFLOW", "PROACTIVE", "LOCAL").

    Raises:
        ExecutionwareError: If EXECUTIONWARE is not found in config or environment.
    """
    # First try to get from environment variable (used by Kubeflow)
    executionware = os.getenv("EXECUTIONWARE")
    if executionware:
        return executionware

    # Fall back to runtime config file (used by ProActive)
    try:
        runtime_config = _get_runtime_config()
    except ConfigurationError:
        # Config file not found, re-raise as ExecutionwareError with helpful message
        raise ExecutionwareError(
            "EXECUTIONWARE not found in environment variables and no runtime config file exists. "
            "Please set the EXECUTIONWARE environment variable or ensure the runtime config file is present."
        )

    if "EXECUTIONWARE" not in runtime_config:
        raise ExecutionwareError(
            "EXECUTIONWARE key not found in runtime configuration file. "
            "The config file must contain an 'EXECUTIONWARE' field."
        )

    return runtime_config["EXECUTIONWARE"]


def get_utils() -> ModuleType:
    """
    Get the appropriate utils module based on the EXECUTIONWARE configuration.

    This function reads the runtime configuration to determine which execution
    environment is being used, and returns the corresponding utils module.

    Returns:
        ModuleType: Either kubeflow_utils, local_utils, or proactive_utils module.

    Raises:
        ExecutionwareError: If EXECUTIONWARE has an unsupported value or cannot be determined.
    """
    global _utils_module_cache

    # Return cached module if available
    if _utils_module_cache is not None:
        return _utils_module_cache

    # Get executionware configuration
    executionware = _get_executionware_from_config()

    # Validate executionware value
    valid_values = ["KUBEFLOW", "LOCAL", "PROACTIVE"]
    if executionware not in valid_values:
        raise ExecutionwareError(
            f"Unsupported EXECUTIONWARE value: '{executionware}'. "
            f"Supported values are: {', '.join(valid_values)}"
        )

    # Import the appropriate utils module based on EXECUTIONWARE
    if executionware == "KUBEFLOW":
        from .utilities import kubeflow_utils
        _utils_module_cache = kubeflow_utils
    elif executionware == "LOCAL":
        from .utilities import local_utils
        _utils_module_cache = local_utils
    elif executionware == "PROACTIVE":
        from .utilities import proactive_utils
        _utils_module_cache = proactive_utils

    return _utils_module_cache
