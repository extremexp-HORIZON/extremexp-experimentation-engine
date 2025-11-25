"""
Custom exceptions for eexp_engine_utils.

This module defines specific exception types to provide clear, actionable error messages
when things go wrong in the experimentation engine utilities.
"""


class EexpEngineUtilsError(Exception):
    """
    Base exception for all eexp_engine_utils errors.

    All custom exceptions in this package inherit from this base class,
    allowing users to catch all package-specific errors with a single except clause.
    """
    pass


class DatasetNotFoundError(EexpEngineUtilsError):
    """
    Raised when a requested dataset cannot be found.

    This error indicates that the dataset key doesn't exist in the current context,
    either in the filesystem, MinIO, or DDM service.

    Example:
        >>> utils.load_dataset(variables, resultMap, "nonexistent_key")
        DatasetNotFoundError: Dataset 'nonexistent_key' not found in task inputs
    """
    pass


class ConfigurationError(EexpEngineUtilsError):
    """
    Raised when configuration is invalid or missing.

    This error indicates problems with:
    - Missing required configuration parameters
    - Invalid configuration values
    - Incompatible configuration combinations

    Example:
        >>> # Missing DDM_URL when DATASET_MANAGEMENT=DDM
        ConfigurationError: DDM_URL is required when DATASET_MANAGEMENT=DDM
    """
    pass


class ExecutionwareError(EexpEngineUtilsError):
    """
    Raised when EXECUTIONWARE configuration is invalid or cannot be determined.

    This error indicates that the system cannot determine which execution environment
    (Kubeflow, ProActive, Local) the code is running in.

    Example:
        >>> # EXECUTIONWARE not set and no runtime config file
        ExecutionwareError: EXECUTIONWARE not found in environment or runtime config
    """
    pass


class DataManagementError(EexpEngineUtilsError):
    """
    Raised when there's an error with data management operations.

    This covers errors related to:
    - File upload/download failures
    - MinIO connection issues
    - DDM service errors

    Example:
        >>> # DDM service returns error
        DataManagementError: Failed to upload file to DDM: Connection timeout
    """
    pass


class ValidationError(EexpEngineUtilsError):
    """
    Raised when input validation fails.

    This error indicates that function arguments don't meet the expected criteria
    (wrong type, invalid value, missing required fields, etc.)

    Example:
        >>> utils.load_dataset(None, resultMap, "key")
        ValidationError: variables must be a dict, got NoneType
    """
    pass
