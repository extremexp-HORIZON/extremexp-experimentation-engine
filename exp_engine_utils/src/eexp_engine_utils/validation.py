from typing import Any, Dict
from collections.abc import Mapping
from .exceptions import ValidationError


def validate_variables(variables: Any) -> None:
    """
    Validate the variables parameter.

    Args:
        variables: The variables dict to validate

    Raises:
        ValidationError: If variables is invalid
    """
    if variables is None:
        raise ValidationError("variables parameter cannot be None")

    # Accept dict or any dict-like object (including ProActive's JavaMap)
    if not isinstance(variables, (dict, Mapping)):
        raise ValidationError(
            f"variables must be a dict or dict-like object, got {type(variables).__name__}"
        )


def validate_result_map(resultMap: Any) -> None:
    """
    Validate the resultMap parameter.

    Args:
        resultMap: The resultMap dict to validate

    Raises:
        ValidationError: If resultMap is invalid
    """
    if resultMap is None:
        raise ValidationError("resultMap parameter cannot be None")

    # Accept dict or any dict-like object (including ProActive's JavaMap)
    if not isinstance(resultMap, (dict, Mapping)):
        raise ValidationError(
            f"resultMap must be a dict or dict-like object, got {type(resultMap).__name__}"
        )


def validate_key(key: Any) -> None:
    """
    Validate the dataset key parameter.

    Args:
        key: The key string to validate

    Raises:
        ValidationError: If key is invalid
    """
    if key is None:
        raise ValidationError("key parameter cannot be None")

    if not isinstance(key, str):
        raise ValidationError(
            f"key must be a string, got {type(key).__name__}"
        )

    if not key.strip():
        raise ValidationError("key cannot be an empty string")


def validate_dataset_inputs(variables: Any, resultMap: Any, key: Any) -> None:
    """
    Validate all common dataset function inputs.

    Args:
        variables: Runtime variables dict
        resultMap: Result metadata dict
        key: Dataset key string

    Raises:
        ValidationError: If any parameter is invalid
    """
    validate_variables(variables)
    validate_result_map(resultMap)
    validate_key(key)


def validate_variables_has_key(variables: Dict[str, Any], key: str, parameter_name: str) -> None:
    """
    Validate that variables dict contains a required key.

    Args:
        variables: The variables dict to check
        key: The required key
        parameter_name: Name of the parameter for error message

    Raises:
        ValidationError: If key is missing
    """
    if key not in variables:
        raise ValidationError(
            f"Required key '{key}' not found in {parameter_name}. "
            f"Available keys: {list(variables.keys())}"
        )
