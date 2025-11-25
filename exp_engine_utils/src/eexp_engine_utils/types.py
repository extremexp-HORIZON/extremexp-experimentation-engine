"""
Type definitions for experimentation engine task execution context.

These types help with IDE autocomplete and type checking for variables
that are injected at runtime by the execution engine.
"""

from typing import Any, Dict, TypedDict, Optional


class Variables(TypedDict, total=False):
    """
    Variables dictionary passed to tasks by the execution engine.

    Contains task-specific configuration and runtime parameters.
    Common keys include:
    - task_name: Name of the current task
    - wf_id: Workflow ID
    - data_abstraction_base_url: URL for data abstraction layer
    - data_abstraction_access_token: Access token for data layer
    - User-defined task parameters from .xxp files
    """
    task_name: str
    wf_id: str
    data_abstraction_base_url: Optional[str]
    data_abstraction_access_token: Optional[str]


class ResultMap(Dict[str, Any]):
    """
    Result map dictionary for passing data between tasks.

    Keys are typically the names of outputs from previous tasks.
    Values can be any serializable Python object (strings, dicts, lists, etc.)
    """
    pass


# Convenience function for getting variables with type hints
def get_runtime_context() -> tuple[Variables, ResultMap]:
    """
    Helper function to get typed references to runtime variables.

    This is just for IDE type hints - at runtime, the actual variables
    and resultMap are provided by the execution engine.

    Usage in tasks:
        # At the top of your task, add this for IDE support:
        if False:  # Type checking only, never executes
            from eexp_engine_helpers.types import get_runtime_context
            variables, resultMap = get_runtime_context()

    Returns:
        tuple: (variables, resultMap) with proper type hints
    """
    raise RuntimeError("This function is for type hints only and should never be called at runtime")
